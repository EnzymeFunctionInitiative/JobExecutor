
from typing import ClassVar

class Job:
    def __init__(self, **kwargs):
        """
        Create a job object having attributes associated with each keyword arg
        and associated values
        """
        if "job_id" not in kwargs or "status" not in kwargs:
            raise ValueError("Missing required fields: 'job_id' and 'status'")
        # update the __dict__ to cleanly implement all attributes
        self.__dict__.update(kwargs)
        
        # make some container within which results can be aggregated
        self.results = {}
    
    def __repr__(self):
        repr_str =  f"<Job job_id={self.job_id}, status={self.status}"
        if self.__dict__.get("timeCreated"):
            repr_str += f", timeCreated={self.timeCreated}"
        elif self.__dict__.get("timeStarted"):
            repr_str += f", timeStarted={self.timeStarted}"
        elif self.__dict__.get("timeFinished"):
            repr_str += f", timeFinished={self.timeFinished}"
        repr_str += ">"
        return repr_str


    _parameter_attrs = frozenset([])
    _updatable_attrs = frozenset(["status","timeStarted","timeCompleted"])

