
import os
from datetime import datetime
from typing import Dict, Any, Tuple, List
from pathlib import Path
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape
import zipfile

from constants import Status
from configClasses.baseConfig import BaseConfig
from jobModels.job_orm import Job
from .baseStrategy import BaseStrategy

class Start(BaseStrategy):
    ############################################################################
    # Interface method
    def execute(self, job_obj: Job, config_obj: BaseConfig) -> Tuple[str, Dict]:
        """
        """
        ## OUTLINE:
        # the job_obj, config_obj, and possibly environment variables contain 
        # all necessary information for running this task. 
        # 1) determine the nf pipeline; general nextflow pipeline as well as 
        #    specific avenue/mode to perform the calculation. Also get the 
        #    transportation strategy for a NEW job. 
        # 2) gather the parameters from the job object in the form of 
        #    dictionary
        # 3) using the config_obj, develop config-specific parameters. 
        # 4) run pipeline specific input parameter code development (port 
        #    equivalent code from the EST/bin/*py scripts
        # 5) Write parameters to a file. 
        # 6) prepare batch commands/files. 
        # 7) collect and transport files, as needed. 
        # 8) execute the batch commands. 
        # 9) fill out the updates_dict and return
        
        # step 1. Determine the type of Job to be performed. 
        # the pipeline class attribute is just one way to denote this 
        # information. I could also use the class name itself to determine the
        # necessary information... 
        pipeline = job_obj.pipeline.split(":")
        ## or 
        #cls_name = job_obj.__class__.__name__
        ## apply some sort of splits to the class names to generate the same 
        ## info as what's in the pipeline class attribute. 
        
        transport_strategy = config_obj.get_attribute(
            "transport_dict",
            "transport_strategy"
        )
        if transport_strategy:
            for strat in transport_strategy:
                if job_obj.status.__str__() == strat.status:
                    self.from_destination = Path(strat.destination1)
                    self.to_destination   = Path(strat.destination2)
                    self.transport_cmd    = strat.command
        else:
            self.from_destination = Path("/tmp")
            self.to_destination = Path("/tmp")
        
        # steps 2-4. Parameter handling.
        self.params_dict = self.prepare_params(job_obj, config_obj, pipeline)

        # step 5. Parameter Rendering
        params_file_path = self.render_params()

        # step 6. Command preparation.
        command_template_file = Path(
            config_obj.get_attribute(
                "compute_dict",
                "template_dir",
            )
        ) / f"run_nextflow_{pipeline[0]}.jinja"
        self.command_list = self.render_commands(command_template_file)
       
        # step 7. Transport files.
        if self.from_destination != self.to_destination:
            # get list of input files that need to be transferred
            input_files = job_obj.get_input_files(self.from_destination)
            input_files.append(params_file_path)
            # zip up files
            zip_file_path = self.from_destination / "input_files.zip"
            with zipfile.ZipFile(zip_file_path, "w") as zip_file:
                for file_path in file_paths:
                    zip_file.write(file_path, arcname = file_path.name)

            # predict destination's file paths for these files
            destination = self.to_destination / jobId
            # run the transfer command; in the local sense, this is kinda dumb
            retcode, comms = run_command(
                f"unzip {zip_file_path} -d {destination}"
            )
            if retcode != 0:
                raise TransportError("")
            
        # step 8. Command execution.
        retcode = 0
        for i, cmd in self.command_list:
            print(i, cmd)
            retcode, comms = run_command(cmd)
            proc_stdout, proc_stderr = [proc_std.decode() for proc_std in comms]
            print("\n".join([proc_stdout, proc_stderr]))

            # if an error occurs
            if proc_stderr or retcode != 0:
                raise CommandError("")
      
        # step 9. Collect updates.
        updates_dict = {}
        if retcode == 0:
            updates_dict["status"] = Status.RUNNING
            updates_dict["timeStarted"] = datetime.now()
            # process the last command's stdout string to get the 
            # schedulerJobId. NOTE: this is placeholder code assuming the last 
            # command was sbatch which has stdout in the form of: 
            # "Submitted batch job 19162807"
            schedulerJobId = proc_stdout.decode().split()[-1]

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
        """
        # use the parameters, config_obj, and environment variables to fill in 
        # any missing parameters
        
        # step 2.
        params_dict = job_obj.get_parameters_dict()
    
        # step 3.
        output_dir = config_obj.get_parameter(
            "compute_dict",
            "output_dir",
            os.getenv("EFI_OUTPUT_DIR")
        )
        params_dict["output_dict"] = Path(output_dir) / params_dict["job_id"]

        params_dict["efi_config"] = config_obj.get_parameter(
            "compute_dict", 
            "efi_config", 
            os.getenv("EFI_JOB_CONFIG")
        )
        params_dict["efi_db"] = config_obj.get_parameter(
            "compute_dict", 
            "efi_db", 
            os.getenv("EFI_DB")
        )
        params_dict["nf_config"] = config_obj.get_parameter(
            "compute_dict", 
            "nf_config", 
            os.getenv("EFI_NF_CONFIG")
        )
        
        # params only relevant to EST but the params.yaml file can be 
        # overfilled with parameters so no harm done to non-EST job types
        params_dict["duckdb_mem_limit"] = config_obj.get_parameter(
            "compute_dict", 
            "duckdb_memory_limit", 
            os.getenv("EFI_DDB_MEM_LIMIT", 0)
        )
        params_dict["duckdb_threads"] = config_obj.get_parameter(
            "compute_dict", 
            "duckdb_threads", 
            os.getenv("EFI_DDB_THREADS", 0 )
        )
        params_dict["fasta_shards"] = config_obj.get_parameter(
            "compute_dict", 
            "fasta_shards", 
            os.getenv("EFI_FASTA_SHARDS", 128)
        )

        # step 4.
        # ... develop pipeline specific handling of parameters

        # develop the path to the nf pipeline script 
        params_dict["workflow_path"] = Path(
            config_obj.get_parameter(
                "compute_dict", 
                "est_repo_path",
                os.getenv("EST_REPO_PATH")
            )
        ) / "pipelines" / pipeline[0] / f"{pipeline[0]}.nf"
        
        #if len(pipeline) == 2:
        #    a specific input path's parameters need to be prepared
        #    ...

        return params_dict

    def render_params(self) -> Path:
        """
        """
        params_file_path = Path(self.from_destination) / self.params_dict["job_id"] / "params.json"
        params_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(params_file_path,'w') as out:
            json.dump(self.params_dict, out, indent=4)
        return params_file_path

    def render_commands(template_file_path: Path) -> List[str]:
        """
        """
        env = Environment(
            loader = FilSystemLoader(template_file_path.parent), 
            autoescape=select_autoescape()
        )
        command_template = env.get_template(template_file_path)
        command_str = command_template.render(**self.params_dict)
        return command_str.strip().split("\n")


class CheckStatus(BaseStrategy):
    def execute(self, job_obj: Job, config_obj: BaseConfig):
        """
        """
        updates_dict = {}
        return 0, updates_dict






