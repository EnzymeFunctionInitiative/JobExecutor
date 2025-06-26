
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

class CheckStatus(BaseStrategy):
    ############################################################################
    # Interface method
    def execute(
            self,
            job_obj: Job,
            config_obj: BaseConfig
        ) -> Tuple[str, Dict]:
        """
        The job_obj, config_obj, and environment variables (optional) contain
        all necessary information for running the CheckStatus task for the given
        job_obj. 
        
        This method covers many steps: 
        1) get the schedulerJobId parameter from the job object.
        2) Given entries in the config file, determine the strategies to be.
           used for checking status and transportation.
        3) Run the check status strategy.
        4) Collect the status of the job and handle accordingly.
        5) If the job is "finished", run the transport strategy.

        """
        # step 1. get schedulerJobId
        _id = job_obj.schedulerJobId
        if not _id:
            return 1, {"status": Status.FAILED}

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
        
        check_status_strategy_module = config_obj.get_parameter(
            "compute_dict",
            "execution_strategy_file",
            os.getenv("EFI_EXECUTION_STRATEGY")
        )
        # if defined, load the module and class
        if check_status_strategy_module:
            module = importlib.import(check_status_strategy_module)
            check_status_strategy = getattr(module, "CheckStatus")
        # otherwise, raise an error
        else:
            raise RuntimeError("No check status strategy defined.")

        # step 3. Run the check status strategy to determine the job's fate,
        # only knowing the job's _id.
        retcode, results = check_status_strategy.run(
            _id, 
        )
        if retcode != 0:
            print(f"CheckStatus task failed.\n{job_obj}")
            raise results[0]

        # step 4. 
        job_status = results[0]
        # check the job_status value to determine what updates need to be made
        if job_status in ["pending", "running"]:
            print(f"{job_obj} is {job_status}.")
            return 0, {"status": Status.RUNNING}
        elif job_status == "failed":
            print(f"{job_obj} failed.")
            return 0, {"status": Status.FAILED}
        # Step 4 cont'd. The job is finshed, so perform a transport and collect
        # even more updates.
        elif job_status in job_states["finished"]:
            print(f"{job_obj} is finished.")
            updates_dict = {"status": Status.FINISHED}
            # get Job's class attribute containing file names to be gathered 
            # as results. This does not check for existence of the files.
            file_list = job_obj.get_output_files()

            # gather destination information
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
            from_destination = Path(destination2) / str(job_obj.id)
            to_destination   = Path(destination1) / str(job_obj.id)
            # make the working directories.
            from_destination.mkdir(parents=True, exist_ok=True)
            to_destination.mkdir(parents=True, exist_ok=True)

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

            # fill the updates_dict with table values to be updated
            # NOTE: this is gonna change once result columns get figured out
            updates_dict["results"] = ",".join([to_destination / file for file in file_list])

            # NOTE: the job table subclasses need to have their own 
            # apply_update() methods that take in the file list (or other 
            # information) and parse those files into key information that 
            # goes into the Job table...

            return 0, updates_dict

    ############################################################################


