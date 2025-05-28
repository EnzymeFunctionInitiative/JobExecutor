
from constants import Status
from configClasses.baseConfig import BaseConfig
from jobModels.job_plain import Job
from .baseStrategy import BaseStrategy

class Start(BaseStrategy):
    def execute(self, job_obj: Job, config_obj: BaseConfig):
        """
        dummy StartStrategy example. Just do some printing. 
        """
        print(f"A Start task is being performed for {job_obj}.\nUpdating" 
            + f" {job_obj.status} to {str(Status.RUNNING)}")
        return 0, {"status": Status.RUNNING}

    #def __repr__(self):
    #   return f"<Start job_id={job_obj.job_id}, status={self.status}>" 

class CheckStatus(BaseStrategy):
    def execute(self, job_obj: Job, config_obj: BaseConfig):
        """
        dummy CheckStatusStrategy example. Just do some printing. 
        """
        print(f"A CheckStatus task is being performed for {job_obj}.\nUpdating"
            + f" {job_obj.status} to {str(Status.FINISHED)}")
        return 0, {"status": Status.FINISHED}

    #def __repr__(self):
    #   return f"<Start job_id={job_obj.job_id}, status={self.status}>" 


