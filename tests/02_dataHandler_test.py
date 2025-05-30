
import pytest

from configClasses.baseConfig import BaseConfig
from constants import Status
from dataHandler import DataHandler

import jobModels.job_plain as job_model
import dataStrategies.baseStrategy as data_strategy
#import jobModels.job_orm as job_model
#import dataStrategies.sqlStrategy as data_strategy

test_data = [
    pytest.param(
        "templates/dummy.config", 
        data_strategy.DictOfDictStrategy,
        job_model.Job,
    ), 
]
@pytest.mark.parametrize(
    "config_file_path, data_strategy_type, job_type", 
    test_data
)
def test_data_handler(
        config_file_path,
        data_strategy_type,
        job_type):
    """ Testing wrapper function for the dataHandler class """
    # required to initiate the config obj
    if ".json" in config_file_path:
        config = BaseConfig.read_json_config(config_file_path)
    else:
        config = BaseConfig.read_ini_config(config_file_path)
    # use the context management capability of the DataHandler class
    with DataHandler(config) as data_handler:
        assert type(data_handler._strategy) == data_strategy_type
        jobs = data_handler.get_jobs(Status.INCOMPLETE)
        for job in jobs:
            assert type(job) == job_type
        print(data_handler._strategy.data[job.job_id])
        data_handler.update_job(
            job, 
            {"status": Status.NEW, "results": "new value"}
        )
        print(data_handler._strategy.data[job.job_id])
        assert data_handler._strategy.data[job.job_id]["status"] == Status.NEW


