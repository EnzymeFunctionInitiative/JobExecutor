
import pytest

from configClasses.baseConfig import BaseConfig
from constants import Status
from taskOperator import Operator

# prep the config object, but with an incorrect compute -> type value
config_obj = BaseConfig.read_ini_config("templates/dummy.config")
config_obj.compute_dict.update({"type":"not_implemented"})

@pytest.mark.parametrize("config_obj", [config_obj])
def test_check_mode(config_obj):
    """ Testing wrapper for the check_mode() method of the taskOperator """
    with pytest.raises(NotImplementedError):
        task_operator = Operator(config_obj)


# testing with the dummy task types
import jobModels.job_dummy as job_model

# prep the Job objects
temp_jobs = [
    job_model.Job(**{"id":i, "status":status, "something":"else"})
    for i, status in enumerate([Status.NEW, Status.RUNNING])
]

# prep the config object
config_obj = BaseConfig.read_ini_config("templates/dummy.config")

# prep the test_data
test_data = [
    pytest.param(
        job_obj,
        config_obj, 
    ) for job_obj in temp_jobs
]

@pytest.mark.parametrize(
    "job_obj, config", test_data
)
def test_task_operator(
        job_obj,
        config):
    """ Testing wrapper function for the Operator class's execute() mehtod """
    
    task_operator = Operator(config)
    assert task_operator._strategy == None
    retcode, updates = task_operator.execute(job_obj, config)
    assert retcode == 0
    if job_obj.status == Status.NEW:
        assert updates["status"] == Status.RUNNING
    elif job_obj.status == Status.RUNNING:
        assert updates["status"] == Status.FINISHED


