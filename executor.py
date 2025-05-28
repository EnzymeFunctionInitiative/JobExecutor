
"""
Code to automate the submission of new EFI jobs on a compute machine, assuming
the jobs' input parameters and statuses are contained in a database table (like
the one created from the hosted website). 

current version: 0.0.1, 2025-05-27, RBD
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
    parser.add_argument("--mode","-m", required=True, help="Keyword to denote what job executor strategy/mode is to be used to gather unfinished jobs and perform some task for them.")
    parser.add_argument("--configuration-file","--conf", required=True, help="File path to the json- or INI-formatted config file specifying the access tokens/details for the job database and compute resources.")
    #parser.add_argument("--configuration-format","--conf-fmt", default = "ini", help="File format for the config file.")
    #parser.add_argument("--db-name","-db", required=True, help="string, either a file path to a local database or the name of the database accessed via information in `--configuration-file`")
    args = parser.parse_args()
    # validation of input arguments happens here...
    return args

if __name__ == "__main__":
    # load input arguments for the job executor
    args = parse_input_arguments()

    # Operator is the context object for the taskStrategies
    task_operator = Operator(args.mode)

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

    # open a DataHandler using a with statement
    with DataHandler(args.mode, config) as data_handler:
        # gather incomplete jobs
        jobs = data_handler.get_jobs(Status.INCOMPLETE)
        # loop over the iterator and handle each job individually 
        for job in jobs:
            # execute the task_operator._strategy's execute() method
            retcode, updates = task_operator.execute(job, config)
            # update the job object with any new information
            data_handler.update_job(job, updates)












#
#    # SQLAlchemy expects a specific format for database paths/urls so create 
#    # that.
#    db_url = db_connector.create_db_url(config, args.db_name)
#
#    # create the database connection object
#    job_db = db_connector.SQLAlchemyDatabase(db_url)
#    job_db.connect()
#
#    # query the JobDB for rows with status values not equal to 
#    # `Status.INCOMPLETE` 
#    unfinished_jobs = job_db.fetch_jobs(Status.INCOMPLETE)
#    
#    # unfinished_jobs is a ChunkedIteratorResult object that can be iteratively
#    # grabbed from until its empty. 
#    while True:
#        # grab the next row from the unfinished_jobs result; fetchone() and 
#        # equivalent returns a sqlalchemy.engine.row.Row object that basically
#        # functions like a tuple holding within it the db_connector.Job object 
#        # that we want to perform tasks on.
#        job = unfinished_jobs.fetchone()
#        # if the fetch returned None, break out of the while loop
#        if not job:
#            break
#
#        print(f"\n{job}")
#        
#        # run the process_job() func on the db_connector.Job object to
#        # determine which task needs to be performed and subsequently perform
#        # that task. No updates to the Job object's attributes are done within
#        # process_job(); those are all stashed in the `updates` dict and 
#        # applied to the database via `job_db.update_job()` 
#        retcode, updates = task_operator.process_job(job[0], config)
#        
#        # if a status change has occurred, commit it and any relevant info to 
#        # the DB.
#        if updates.get("status") != job[0].status:
#            job_db.update_job(job[0], updates)
#        
#        print(f"{job}\n")
#
#    # close the connection
#    job_db.disconnect()
#

