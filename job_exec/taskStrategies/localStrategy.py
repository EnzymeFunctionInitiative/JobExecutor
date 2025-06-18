
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
    def execute(self, job_obj: Job, config_obj: BaseConfig) -> Tuple[str, Dict]:
        """
        """
        ## OUTLINE:
        # the job_obj, config_obj, and possibly environment variables contain 
        # all necessary information for running this task. 
        # 1) determine the nf (sub)pipeline; gather working directories from a
        #    web-server and compute-cluster stand point. 
        # 2) gather the parameters from the job object in the form of a
        #    dictionary.
        # 3) using the config_obj, develop config-specific parameters. 
        # 4) run pipeline specific input parameter code development (port 
        #    equivalent code from the EST/bin/*py scripts)
        # 5) Write parameters to a file. 
        # 6) prepare batch commands/files. 
        # 7) collect and transport files, as needed. 
        # 8) execute the batch commands. 
        # 9) fill out the updates_dict and return
       
        # step 1. Determine the type of Job to be performed. 
        pipeline = job_obj.pipeline.split(":")
        
        ## determine the transportation command to be used.
        #Transport_cmd = config_obj.get_parameter(
        #    "transport_dict",
        #    "transport_cmd",
        #    "cp"
        #)
        # determine the transportation strategy to get working dirs.
        transport_strategy = config_obj.get_parameter(
            "transport_dict",
            "transport_strategy"
        )
        # NOTE: better handling of presence or absence of these config settings
        if transport_strategy:
            strat = transport_strategy.get("new")
            if strat:
                self.from_destination= Path(strat["destination1"]) / job_obj.id
                self.to_destination  = Path(strat["destination2"]) / job_obj.id
        else:
            output_dir = config_obj.get_parameter(
                "compute_dict",
                "output_dir",
                "/tmp"
            )
            self.from_destination = Path(output_dir) / job_obj.id
            self.to_destination = Path(output_dir) / job_obj.id
        
        # make the working directories.
        self.from_destination.mkdir(parents=True, exist_ok=True)
        self.to_destination.mkdir(parents=True, exist_ok=True)

        # steps 2-4. Parameter handling.
        self.params_dict = self.prepare_params(job_obj, config_obj, pipeline)

        # step 5. Parameter rendering.
        params_file_path = Path(self.from_destination) / "params.json"
        self.render_params(params_file_path)
        self.params_dict["params_file"] = params_file_path

        # step 6. Command preparation.
        batch_file_path = Path(self.from_destination) / "run_efi_nextflow.sh"
        batch_file_template = Path(
            config_obj.get_parameter(
                "compute_dict",
                "template_dir"
            )
        ) / "run_efi_nextflow.sh.jinja"
        self.render_batch(batch_file_template, batch_file_path)
       
        # step 7. Transport files.
        if self.from_destination != self.to_destination:
            # get list of input files that need to be transferred
            file_list = job_obj.get_input_files(self.from_destination)
            file_list.append(params_file_path)
            file_list.append(batch_file_path)
            
            # zip up files
            zip_file_path = self.from_destination / "input_files.zip"
            zip_files(zip_file_path, file_list)

            # run the transfer command; in the local sense, this is kinda dumb
            cmd = f"unzip {zip_file_path} -d {self.to_destination}"
            retcode, results = run_command(cmd)
            if retcode != 0:
                raise results[0](f"Transportation failed.\n{job_obj}")
            
        # step 8. Command execution.
        commands = config_obj.get_parameter(
            "compute_dict",
            "submit_command"
        )
        retcode = 0
        for i, cmd in commands:
            print(i, cmd)

            retcode, results = run_command(cmd)
            if retcode != 0:
                raise results[0](f"Command {cmd} failed.\n{job_obj}")
            
            # no error occurred so process the stdout and stderr
            proc_stdout, proc_stderr = results
            print("\n".join([proc_stdout, proc_stderr]))
        
            # get scheduler's job id from lines that have sbatch
            if "sbatch" in cmd:
                schedulerJobId = proc_stdout.strip().split()[-1]    # NOTE
      
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
            "final_output_dir",
            os.getenv("EFI_OUTPUT_DIR")
        ) # NOTE: this is a local path or redundant w/ transportation subparameters?
        params_dict["output_dict"] = Path(output_dir) / params_dict["job_id"]

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
        params_dict["workflow_path"] = Path(
            config_obj.get_parameter(
                "compute_dict",
                "est_repo_path",
                os.getenv("EST_REPO_PATH")
            ) # NOTE: this value is pointing to a file on the compute resource
        ) / "pipelines" / pipeline[0] / f"{pipeline[0]}.nf"

        # step 4. Develop pipeline specific handling of parameters.
        if pipeline[0].lower() == "est":
            params_dict["import_mode"] = pipeline[1].lower()

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
                    params_dict["filter"].append(f'"{keyword}={val}"')
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

    def render_batch(template_file_path: Path, batch_file_path: Path):
        """
        """
        env = Environment(
            loader = FilSystemLoader(template_file_path.parent), 
            autoescape=select_autoescape()
        )
        command_template = env.get_template(template_file_path)
        command_str = command_template.render(**self.params_dict)
        with open(batch_file_path, "w") as batch:
            batch.write(command_str)


class CheckStatus(BaseStrategy):
    def execute(self, job_obj: Job, config_obj: BaseConfig):
        """
        """
        ## OUTLINE:
        # the job_obj, config_obj, and possibly environment variables contain
        # all necessary information for running this task.
        # 1) get the schedulerJobId parameter from the job object.
        # 2) prepare the commands to check the job's status.
        # 3) run the commands and parse the stdout to get the job state/status.
        # 4) If the job is finished, run the transport strategy.
        # No matter the status, fill out the updates_dict and return.

        # step 1. get schedulerJobId
        _id = job_obj.schedulerJobId
        if not _id:
            return 1, {"status": Status.FAILED}

        # step 2. Command preparation. The "check_status_cmd" parameter in the
        # config_obj's compute_dict attribute is an f-string with the "{jobid}"
        # placeholder.
        cmd = config_obj.get_attribute(
            "compute_dict",
            "check_status_cmd"
        ).format(jobid = _id)
        
        # step 3. Run the check_status_cmd
        retcode, results = run_command(cmd)
        # if check_status_cmd failed, 
        if retcode != 0:
            raise results[0](f"CheckStatus task failed.\n{job_obj}")
        # otherwise, gather the std out and err strings
        proc_stdout, proc_stderr = results
        # assuming the below command is followed, the state/status is the zeroth
        # element in the split:
        # sacct -j {_id} -X --format=State,JobID,ExitCode,WorkDir%50 --noheader 
        # FAILED    19185085    127:0   /home/n-z/rbdavid/Projects/testing
        # ^this could all be simplified down
        job_status = proc_stdout.split()[0]
        
        # Step 4. Handle the different job states. 
        if job_status in job_states["running"]:
            return retcode, {"status": Status.RUNNING}
        elif job_status in job_states["failed"]:
            return retcode, {"status": Status.FAILED}
        # Step 4 cont'd. Finished job may or may not require a transport event.
        elif job_status in job_states["finished"]:
            update_dict = {"status": Status.FINISHED}
            # get Job's class attribute containing file names to be gathered 
            # as results.
            file_list = job_obj.get_result_files()
            
            ## determine the transportation command to be used.
            #transport_cmd = config_obj.get_parameter(
            #    "transport_dict",
            #    "transport_cmd",
            #    "cp"
            #)
            # get the transportation strategy for gathering final results.
            transport_strategy = config_obj.get_parameter(
                "transport_dict",
                "transport_strategy"
            )
            # NOTE: better handling of presence or absence of these config 
            # settings
            if transport_strategy:
                strat = transport_strategy.get("finished")
                if strat:
                    from_destination = Path(strat["destination1"]) / job_obj.id
                    to_destination   = Path(strat["destination2"]) / job_obj.id
            else:
                # NOTE: this is gonna change if the `sacct -j` call changes
                cwd = Path(proc_stdout.strip().split()[-1])
                # NOTE: this is gonna change once the columns for results is 
                # figured out
                # NOTE: NO CHECKS DONE FOR FILES EXISTING
                update_dict["results"] = [cwd / file for file in file_list]
                return 0, update_dict
            
            # complete the from_destination paths to include the file names
            from_list = [from_destination / file for file in file_list]
            
            # zip those files up
            zip_file_path = from_destination / "result_files.zip"
            zip_files(zip_file_path, from_list)

            # transfer the zip
            to_destination.mkdir(parents=True, exist_ok=True)
            cmd = f"unzip {zip_file_path} -d {to_destination}"
            retcode, results = run_command(cmd)
            if retcode != 0:
                raise results[0](f"Transportation failed.\n{job_obj}")

            # fill the update_dict with table values to be updated
            update_dict["results"] = [to_destination / file for file in file_list]

            return 0, updates_dict


