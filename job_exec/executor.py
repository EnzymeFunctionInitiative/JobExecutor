
"""
Code to automate the submission of new EFI jobs on a compute machine, assuming
the jobs' input parameters and statuses are contained in a database table (like
the one created from the hosted website). 
"""

import argparse

from configClasses.baseConfig import BaseConfig
from constants import Status
from taskOperator import Operator
from dataHandler import DataHandler

def parse_input_arguments() -> argparse.Namespace:
    """
    """
    parser = argparse.ArgumentParser(description = "Create new jobs, keep tabs on queued jobs, and gather results.")
    parser.add_argument("--configuration-file","--conf", required=True, help="File path to the json- or INI-formatted config file specifying the access tokens/details for the job database and compute resources.")
    #parser.add_argument("--configuration-format","--conf-fmt", default = "ini", help="File format for the config file.")
    parser.add_argument("--logging","-log", default = False, help="File path to a to-be-written log file within which all execution actions are recorded. Default: False (no logging).")
    parser.add_argument("--verbose","-v", action='store_true', help="Flag to increase verbosity in logging.")
    parser.add_argument("--dry-run","-dry", action='store_true', help="Flag to prevent any commands from actually being run. Instead, the commands will be printed.")
    args = parser.parse_args()
    # validation of input arguments happens here...
    return args

if __name__ == "__main__":
    # load input arguments for the job executor
    args = parse_input_arguments()

    # read the config file
    config = BaseConfig.read_ini_config(args.configuration_file)
    ## instantiate the config obj here and feed it into the operator
    #if args.configuration_format == "ini":
    #    config = BaseConfig.read_ini_config(args.configuration_file)
    #elif args.configuration_format == "json": 
    #    config = BaseConfig.read_json_config(args.configuration_file)
    #else:
    #    raise NotImplementedError("A configuration reader for" 
    #        + f" {args.configuration_file} format has not been implemented.")

    # Operator is the context object for the taskStrategies
    task_operator = Operator(config)

    # open a DataHandler using a with statement
    with DataHandler(config) as data_handler:
        # gather incomplete jobs
        jobs = data_handler.get_jobs(Status.INCOMPLETE)
        # loop over the iterator and handle each job individually 
        for job in jobs:
            # execute the task_operator._strategy's execute() method
            retcode, updates = task_operator.execute(job, config)
            # update the job object with any new information
            data_handler.update_job(job, updates)

