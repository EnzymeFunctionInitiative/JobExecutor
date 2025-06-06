
import pytest

from constants import Status

test_data = [
    pytest.param(Status.NEW, "new"), 
    pytest.param(Status.RUNNING, "running"), 
    pytest.param(Status.FINISHED, "finished"), 
    pytest.param(Status.FAILED, "failed"), 
    pytest.param(Status.ARCHIVED, "archived")
] 
@pytest.mark.parametrize("Status_flag, Status_str", test_data)
def test_status_strings(Status_flag, Status_str):
    """ Testing wrapper function for the Status.__str__ method """
    assert Status_flag.__str__() == Status_str

test_data = [
    pytest.param("new", Status.NEW), 
    pytest.param("running", Status.RUNNING), 
    pytest.param("finished", Status.FINISHED), 
    pytest.param("failed", Status.FAILED), 
    pytest.param("archived", Status.ARCHIVED)
] 
@pytest.mark.parametrize("Status_str, Status_flag", test_data)
def test_getFlag(Status_str, Status_flag):
    """ Testing wrapper function for the Status.getFlag method """
    assert Status.getFlag(Status_str) == Status_flag

test_data = [
    # check membership in Status.INCOMPLETE
    pytest.param(Status.NEW, Status.INCOMPLETE, True), 
    pytest.param(Status.RUNNING, Status.INCOMPLETE, True), 
    pytest.param(Status.FINISHED, Status.INCOMPLETE, False), 
    pytest.param(Status.FAILED, Status.INCOMPLETE, False), 
    pytest.param(Status.ARCHIVED, Status.INCOMPLETE, False),
    # check membership in Status.COMPLETED
    pytest.param(Status.NEW, Status.COMPLETED, False), 
    pytest.param(Status.RUNNING, Status.COMPLETED, False), 
    pytest.param(Status.FINISHED, Status.COMPLETED, True), 
    pytest.param(Status.FAILED, Status.COMPLETED, True), 
    pytest.param(Status.ARCHIVED, Status.COMPLETED, True),
    # check membership in Status.CURRENT
    pytest.param(Status.NEW, Status.CURRENT, True), 
    pytest.param(Status.RUNNING, Status.CURRENT, True), 
    pytest.param(Status.FINISHED, Status.CURRENT, True), 
    pytest.param(Status.FAILED, Status.CURRENT, True), 
    pytest.param(Status.ARCHIVED, Status.CURRENT, False),
] 
@pytest.mark.parametrize("Status_flag, Status_combo, boolean", test_data)
def test_status_membership(Status_flag, Status_combo, boolean):
    """ Testing wrapper function for Status membership """
    assert (Status_flag in Status_combo) == boolean

