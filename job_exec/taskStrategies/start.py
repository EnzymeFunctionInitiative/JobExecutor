
from typing import Dict, Any, Tuple, List
import os
from datetime import datetime
from pathlib import Path
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape

from constants import Status
from configClasses.baseConfig import BaseConfig
from jobModels.job_dummy_orm import Job
from .baseStrategy import BaseStrategy

from .utilities import run_command, zip_files, slurm_job_states as job_states

class Start(BaseStrategy):
    ############################################################################
    # Interface method
    def execute(
            self, 
            job_obj: Job, 
            config_obj: BaseConfig
        ) -> Tuple[str, Dict]:
        """
        """
        ## OUTLINE:
        # - the job_obj, config_obj, and possibly environment variables contain
        #   all necessary information for running this task. 
        # 1) Determine the efi nf (sub)pipeline.
        # 2) Given entries in the config file, determine the strategies to be
        #    used for transportation and submission/execution.
        # 3) Gather and create destinations for transportation.
        # 4) Prepare the parameters
        #    a) from the job object
        #    b) from the config object
        #    c) prepare (sub)pipeline-specific input parameters
        # 5) Write parameters to a file.
        # 6) Write the submission script to file.
        # 7) Apply the transportation strategy to the input files.
        # 8) Apply the submission/execution strategy to the input files. 
        # 9) Fill out the updates_dict and return.
       
        # step 1. Determine the type of Job to be performed. 
        pipeline = job_obj.pipeline.split(":")
       
        # step 2. Determine the transportation and execution strategies to be
        # used. 
        transport_strategy_module = config_obj.get_parameter(
            "transport_dict",
            "transport_strategy_file",
            os.getenv("EFI_TRANSPORTATION_STRATEGY")
        )
        # if defined, load the module and class
        if transport_strategy_module:
            module = importlib.import(transport_strategy_module)
            transport_strategy = getattr(module, "Transport")
        # otherwise, raise an error
        else:
            raise RuntimeError("No transportation strategy defined.")
        
        execution_strategy_module = config_obj.get_parameter(
            "compute_dict",
            "execution_strategy_file",
            os.getenv("EFI_EXECUTION_STRATEGY")
        )
        # if defined, load the module and class
        if execution_strategy_module:
            module = importlib.import(execution_strategy_module)
            execution_strategy = getattr(module, "Submit")
        # otherwise, raise an error
        else:
            raise RuntimeError("No submission/execution strategy defined.")

        # step 3. Gather and create the destination file paths.
        destination1 = config_obj.get_parameter(
            "transport_dict",
            "local_destination"
        )
        if not destination1: 
            raise RuntimeError("")
        
        destination2 = config_obj.get_parameter(
            "transport_dict",
            "remote_destination",
            destination1
        )
        # turn them into Path objects
        from_destination = Path(destination1) / str(job_obj.id)
        to_destination   = Path(destination2) / str(job_obj.id)
        # make the working directories.
        from_destination.mkdir(parents=True, exist_ok=True)
        to_destination.mkdir(parents=True, exist_ok=True)

        # step 4. Parameter handling.
        self.params_dict = self.prepare_params(job_obj, config_obj, pipeline)

        # step 5. Parameter rendering.
        params_file_path = Path(from_destination) / "params.json"
        self.render_params(params_file_path)
        self.params_dict["params_file"] = str(params_file_path)

        # step 6. Command preparation.
        batch_file_path = Path(from_destination) / "batch.sh"
        batch_file_template = config_obj.get_parameter(
            "compute_dict",
            "batch_template_file",
            os.getenv("EFI_BATCH_TEMPLATE")
        )
        if not batch_file_template:
            raise RuntimeError("")
        
        self.render_batch(batch_file_template, batch_file_path)
       
        # step 7. Transport files.
        # get list of input files that need to be transferred
        file_list = job_obj.get_input_files()
        file_list.append(params_file_path)
        file_list.append(batch_file_path)
        # if transportation needs to happen, do so here.
        if from_destination != to_destination:
            retcode, results = transport_strategy.run(
                file_list,
                from_destination,
                to_destination
            )
            if retcode != 0:
                print(f"Transportation failed.\n{job_obj}")
                raise results[0]

        # step 8. Command execution.
        retcode, results = execution_strategy.run(
            to_destination, 
        )
        if len(results) > 1:
            schedulerJobId = results[0]
        
        #commands = config_obj.get_parameter(
        #    "compute_dict",
        #    "submit_command"
        #)
        #retcode = 0
        #for i, cmd in enumerate(commands):
        #    print(i, cmd)

        #    retcode, results = run_command(cmd, working_dir = to_destination)
        #    if retcode != 0:
        #        print(f"Command {cmd} failed.\n{job_obj}")
        #        raise results[0]
        #    
        #    # no error occurred so process the stdout and stderr
        #    proc_stdout, proc_stderr = results
        #    print("\n".join([proc_stdout, proc_stderr]))
        #
        #    # get scheduler's job id from lines that have sbatch
        #    if "sbatch" in cmd:
        #        schedulerJobId = proc_stdout.strip().split()[-1]    # NOTE
      
        # step 9. Collect updates.
        updates_dict = {}
        if retcode == 0:
            updates_dict["status"] = Status.RUNNING
            updates_dict["timeStarted"] = datetime.now()
        else:
            updates_dict["status"] = Status.FAILED
        
        if schedulerJobId:
            updates_dict["schedulerJobId"] = schedulerJobId
        
        return retcode, updates_dict

    ############################################################################

    def prepare_params(
            self, 
            job_obj: Job, 
            config_obj: BaseConfig, 
            pipeline_list: List[str]
        ) -> Dict[str, Any]:
        """
        Gather all relevant parameters for the nextflow pipeline into a dict.

        Arguments
        ---------
            job_obj
                Job object, a subclass of the Job table with specified
                parameters accessible via the `get_parameters_dict()` method.
            config_obj
                BaseConfig object, a container for the input parameters given
                via the Config INI or JSON file. This contains all
                site-specific details such as paths, environment files, etc.
            pipeline_list
                list, can be len of 1 or 2. Zeroth element describes which
                nextflow pipeline to use. If present, the first element
                specifies the input/import mode for the given pipeline. E.g.
                an ESTGenerateFastaJob has a pipeline_list of ["est","fasta"].

        Returns
        -------
            a parameter dictionary filled with key:value pairs relevant to the
            given job_obj. May include extra parameters that go unused in the
            nextflow run; no harm is done by doing this.
        """
        # step 2.
        params_dict = job_obj.get_parameters_dict()
    
        # step 3.
        output_dir = config_obj.get_parameter(
            "compute_dict",
            "output_dir",
            os.getenv("EFI_OUTPUT_DIR")
        ) # NOTE: this is a local path or redundant w/ transportation subparameters?
        params_dict["output_dir"] = str(Path(output_dir) / str(job_obj.id))

        params_dict["efi_config"] = config_obj.get_parameter(
            "compute_dict",
            "efi_config",
            os.getenv("EFI_JOB_CONFIG")
        ) # NOTE: this value is pointing to a file on the compute resource; is this needed if efi_db is an sqlite file?

        params_dict["efi_db"] = config_obj.get_parameter(
            "compute_dict",
            "efi_db",
            os.getenv("EFI_DB")
        ) # NOTE: this value is pointing to a file if efi_db is sqlite or a db name if mysql.
        
        params_dict["nf_config"] = config_obj.get_parameter(
            "compute_dict",
            "nf_config",
            os.getenv("EFI_NF_CONFIG")
        ) # NOTE: this value is pointing to a file on the compute resource
        
        # params only relevant to EST but the params.yaml file can be
        # overfilled with parameters so no harm done to non-EST job types
        params_dict["duckdb_mem_limit"] = config_obj.get_parameter(
            "compute_dict",
            "duckdb_memory_limit",
            os.getenv("EFI_DDB_MEM_LIMIT", 0)
        )
        # NOTE: this parameter is not currently used by any workflow
        #params_dict["duckdb_threads"] = config_obj.get_parameter(
        #    "compute_dict",
        #    "duckdb_threads",
        #    os.getenv("EFI_DDB_THREADS", 1)
        #)
        params_dict["num_fasta_shards"] = config_obj.get_parameter(
            "compute_dict",
            "fasta_shards",
            os.getenv("EFI_FASTA_SHARDS", 128)
        )
        params_dict["num_accession_shards"] = config_obj.get_parameter(
            "compute_dict",
            "accession_shards",
            os.getenv("EFI_ACCESSION_SHARDS", 16)
        )

        # develop the path to the nf pipeline script
        workflow_path = Path(
            config_obj.get_parameter(
                "compute_dict",
                "est_repo_path",
                os.getenv("EST_REPO_PATH")
            ) # NOTE: this value is pointing to a file on the compute resource
        ) / "pipelines" / pipeline_list[0] / f"{pipeline_list[0]}.nf"
        params_dict["workflow_path"] = str(workflow_path)
        
        # step 4. Develop pipeline specific handling of parameters.
        if pipeline_list[0].lower() == "est":
            params_dict["import_mode"] = pipeline_list[1].lower()

            # look at EST/lib/EFI/Import/Config/Filter.pm for the formatting of
            # members of the params' filter keyword...
            # e.g. in params.json:
            # "filter": [
            #   "family=PF07476",           # comma separated list of accession Ids (no spaces)
            #   "fragment",                 # just a flag
            #   "fraction=1",               # integer value directly after equals sign
            ### NOTE: below not implemented
            #   "predef-file=/some/path/to/a/taxonomy_filter_file.yml",
            #   "predef-filter=bacteria",
            #   "user-file=/some/path/to/a/taxonomy_filter_file.yml",
            #   "user-filter=bacteria",

            # check for filter keywords and gather them into a single filter
            # list/array in params_dict
            filter_keys = [
                ["filterByFamilies", "families"],
                ["excludeFragments","fragments"],
                ["fraction", "fraction"],
                # how do I turn these into user-defined or pre-defined filter entries?
                #["taxSearch", ...],
                #["taxSearchName", ...],
            ]
            params_dict["filter"] = []
            # loop over filter types' Job table keys
            for key, keyword in filter_keys:
                # get the assigned value for the key if present in the
                # params_dict
                val = params_dict.get(key)
                if val:
                    # add the correctly formatted string to the "filter" list
                    params_dict["filter"].append(f"{keyword}={val}")
                    # remove the original key from the params_dict so it isn't
                    # written to the params.json file
                    params_dict.pop(key)

        # More parameters to be handled: 
        # EST: 
        #   - DONE params.import_mode
        #   - DONE params.filter (temp)
        #   - params.
        #   - params.blast_num_matches (dev site only; not mapped to a value in the Job table)
        #
        # GenerateSSN: 
        #   - 
        #
        # GNT: 
        #   - 
        #

        return params_dict

    def render_params(self, params_file_path: str | Path):
        """
        Write a `params.json` file filled with the necessary parameters to run
        the nextflow pipeline, whichever that is.
        """
        with open(params_file_path,'w') as out:
            json.dump(self.params_dict, out, indent=4)

    def render_batch(self, template_file_path: Path, batch_file_path: Path):
        """
        """
        env = Environment(
            loader = FileSystemLoader(template_file_path.parent), 
            autoescape=select_autoescape()
        )
        command_template = env.get_template(template_file_path.name)
        command_str = command_template.render(**self.params_dict)
        with open(batch_file_path, "w") as batch:
            batch.write(command_str)


