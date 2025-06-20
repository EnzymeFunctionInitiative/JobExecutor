
from abc import ABC, abstractmethod
from typing import List, Dict, Any

from constants import Status
from jobModels.job_dummy import Job 
from configClasses.baseConfig import BaseConfig

# defining the interface for DataStrategies
class BaseDataStrategy(ABC):
    @abstractmethod
    def load_data(self):
        """ 
        method used by more complex strategies that need to read files or 
        connect to databases 
        """
        pass

    @abstractmethod
    def close(self):
        """
        method needed to close down access to the data, only used by more 
        complex strategies such as connections to databases
        """
        pass

    @abstractmethod
    def fetch_jobs(self):
        """
        method used to get an iterator filled with jobs that are of interest
        """
        pass

    @abstractmethod
    def update_job(self):
        """
        Update a job row given some representation of updates
        """
        pass

# giving an example of a data strategy, only made complex by creating Job class
# objects to mirror behavior from SQLAlchemy ORM database Job class objects
class DictOfDictStrategy(BaseDataStrategy):
    """ for dummy testing """ 
    def __init__(self, config: BaseConfig):
        """ 
        Need an init for these strategies since the strategy obj will handle
        all data context internally. 
        """
        self.data = None
        self.config = config.get_attribute("jobdb_dict", {})
        # assign any other attributes here based on config...

    def load_data(self):
        """ 
        create a fake dataset; keys in dict act as primary keys (id) and
        subdicts contain keyword and value pairs equivalent to other column
        values; below example is very bare-bones
        """
        data = {
            "1": { "status": Status.FINISHED},
            "2": { "status": Status.RUNNING},
            "3": { "status": Status.RUNNING},
            "4": { "status": Status.NEW},
            "5": { "status": Status.NEW},
            "6": { "status": Status.FAILED},
            "7": { "status": Status.ARCHIVED},
        }
        self.data = data

    def close(self):
        pass

    def fetch_jobs(self, status: Status = Status.INCOMPLETE) -> List[Job]:
        """ 
        Fetch jobs from the dict of dict based on the associated status strings.
        Return a generator containing Job objects associated with keys in 
        self.data that pass the status comparison. 
        """
        for key, subdict in self.data.items():
            # add the `"id": key` pair to the subdict
            subdict.update({"id": key})
            # create a Job object for each subdict, with attributes pulled from
            # the subdict keys and associated values from the keys' values.
            temp_job = Job(**subdict)
            # key is equivalent to the primary key used in a SQL table
            if temp_job.status in status:
                yield temp_job

    def update_job(self, job_obj: Job, update_dict: Dict[str, Any]): 
        """
        Update the Job object's attributes with information contained in the
        update_dict. 
        """
        ## apply the updates contained in update_dict to the Job object
        #job_obj.__dict__.update(update_dict)
        ## and then apply translate the Job object back to a subdict in
        ## self.data
        #self.data[job_obj.id].update(job_obj.__dict__)
        ## or
        # just apply the updates directly to the self.data[job_obj.id] 
        # subdict
        self.data[job_obj.id].update(update_dict)

        # showing both methods may be important when the Job object is more
        # complex or there are more complex updates needing to be performed.

