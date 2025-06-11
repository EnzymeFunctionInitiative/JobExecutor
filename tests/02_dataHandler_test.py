
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
        data_handler.update_job(
            job, 
            {"status": Status.NEW, "results": "new value"}
        )
        assert data_handler._strategy.data[job.id]["status"] == Status.NEW


import dataStrategies.sqlStrategy as data_strategy

test_data = [
    pytest.param(
        {
            "dbi": "sqlite",
            "db_name": "testing.sqlite",
        },
        "sqlite:///testing.sqlite"
    ),
    pytest.param(
        {
            "dbi": "sqlite",
            "db_name": "/tmp/testing.sqlite",
        },
        "sqlite:////tmp/testing.sqlite"
    ),
    pytest.param(
        {
            "dbi": "mysql",
            "username": "username",
            "password": "password",
            "host": "127.0.0.1",
            "port": "3306",
            "db_name": "app",
        },
        "mysql://username:***@127.0.0.1:3306/app"
    ),
    pytest.param(
        {
            "dbi": "mysql+pymysql",
            "username": "username",
            "password": "password",
            "host": "127.0.0.1",
            "port": "3306",
            "db_name": "app",
        },
        "mysql+pymysql://username:***@127.0.0.1:3306/app"
    ),
] 
@pytest.mark.parametrize(
    "db_dict, expected_url", 
    test_data
)
def test_db_url_creator(
        db_dict,
        expected_url):
    """ 
    Testing wrapper function for the dataStrategies/sqlStrategy.py 
    create_db_url() method, which intakes a dictionary of key:value pairs that
    SQLAlchemy uses to create a "URL" string that points to the database to be
    connected to.
    """
    # need to input a config_obj to the strategy
    config = BaseConfig.read_ini_config("templates/dummy.config")
    # init the strategy obj instance
    strategy = data_strategy.SQLStrategy(config)
    # reassign the .config attribute to the testing dictionary
    strategy.config = db_dict
    # run the create_db_url() method with the newly assigned config dictionary
    db_url = strategy.create_db_url()
    print(type(db_url),db_url)
    print(type(expected_url), expected_url)
    assert str(db_url) == expected_url


