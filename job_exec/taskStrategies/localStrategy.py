
from typing import Dict, Any, Tuple, List
import os
from datetime import datetime
from pathlib import Path
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape

from constants import Status
from configClasses.baseConfig import BaseConfig
from jobModels.job_orm import Job
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
        
        # determine the transportation strategy to get working dirs.
        transport_strategy = config_obj.get_attribute(
            "transport_dict",
            "transport_strategy"
        )
        if transport_strategy:
            from_destination = ""
            to_destination   = ""
            for strat in transport_strategy:
                if job_obj.status.__str__() == strat.status:
                    self.from_destination = Path(strat.destination1) / job_obj.id
                    self.to_destination   = Path(strat.destination2) / job_obj.id
                    #transport_cmd    = strat.command   # NOTE: not needed
                    break
        else:
            self.from_destination = Path("/tmp")
            self.to_destination = Path("/tmp")
        
        # make the working directories.
        self.from_destination.mkdir(parents=True, exist_ok=True)
        self.to_destination.mkdir(parents=True, exist_ok=True)

        # steps 2-4. Parameter handling.
        self.params_dict = self.prepare_params(job_obj, config_obj, pipeline)

        # step 5. Parameter rendering.
        params_file_path = Path(self.from_destination) / "params.json"
        self.render_params(params_file_path)

        # step 6. Command preparation.
        batch_file_path = Path(self.from_destination) / "batch.sh"
        command_template_file = Path(
            config_obj.get_attribute(
                "compute_dict",
                "template_dir",
            )
        ) / f"run_efi_nextflow.jinja"
        self.render_batch(command_template_file, batch_file_path)
       
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
        commands = config_obj.get_attribute(
            "compute_dict",
            "submit_command",
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

        # develop the path to the nf pipeline script 
        params_dict["workflow_path"] = Path(
            config_obj.get_parameter(
                "compute_dict", 
                "est_repo_path",
                os.getenv("EST_REPO_PATH")
            )
        ) / "pipelines" / pipeline[0] / f"{pipeline[0]}.nf"
        
        # step 4.
        # ... develop pipeline specific handling of parameters

        #if len(pipeline) == 2:
        #    a specific input path's parameters need to be prepared
        #    ...

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
            
            # get the transportation strategy for gathering final results.
            transport_strategy = config_obj.get_attribute(
                "transport_dict",
                "transport_strategy"
            )
            if transport_strategy:
                # NOTE: this is gonna change if the `sacct -j` call changes
                from_destination = Path(proc_stdout.strip().split()[-1])
                to_destination   = ""
                for strat in transport_strategy:
                    if "finished" == strat.status:
                        from_destination = Path(strat.destination1) / job_obj.id
                        to_destination   = Path(strat.destination2) / job_obj.id
                        #transport_cmd    = strat.command   # NOTE: not needed
                        break
            else:
                # NOTE: this is gonna change if the `sacct -j` call changes
                cwd = Path(proc_stdout.strip().split()[-1])
                # NOTE: this is gonna change once the columns for results is 
                # figured out
                # NOTE: NO CHECKS DONE FOR FILE EXISTING
                update_dict["results"] = [cwd / file for file in file_list]
                return 0, update_dict
            
            # complete the from_destination paths to include the file names
            from_list = [from_destination / file for file in file_list]
            
            # if no to_destination has been defined then no transportation 
            # is needed;
            # NOTE: this is needed because there are no constraints on what 
            # parameters are listed in the config_obj's file
            # NOTE: NO CHECKS DONE FOR FILE EXISTING
            if not to_destination:
                update_dict["results"] = from_list
                return 0, update_dict

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


