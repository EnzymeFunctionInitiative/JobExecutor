
from __future__ import annotations
from typing import Tuple, Dict, Any
import importlib

from constants import Status

from taskStrategies.baseStrategy import BaseStrategy
from configClasses.baseConfig import BaseConfig

class Operator:
    def __init__(self, config: BaseConfig) -> None:
        self.mode = config.get_parameter("compute_dict","type")
        self._strategy = None

        # ensure the given mode has actually been implemented
        self.check_mode()
        
        # assign instance attributes for self.StartStrategy,
        # self.CheckStatusStrategy, and self.TransferStrategy
        self.get_strategies()
        
    def check_mode(self):
        """ 
        Kill the init if the given self.mode is not implemented. 

        NOTE: need to update this list as new modes are implemented
        """
        if self.mode not in ["dummy","local"]:
            raise NotImplementedError("This mode is not implemented. Try" 
                + " something different, like 'dummy'")

    def get_strategies(self):
        """
        The self.mode attribute is used to identify a submodule file from which
        the associated Strategies are imported and assigned to attributes.

        NOTE: need to update this method if new tasks are implemented
        """
        try:
            module = importlib.import_module(f"taskStrategies.{self.mode}Strategy")
            self.StartStrategy = getattr(module, "Start")
            self.CheckStatusStrategy = getattr(module, "CheckStatus")
            #self.TransferStrategy = getattr(module, "Transfer")
            #self.ArchiveStrategy = getattr(module, "Archive")
            print(f"Using {module.__name__} as the source of task strategies.")
        except Exception as e:
            print(f"Importing the taskStrategies.{self.mode} submodule failed.\n {e}")
            raise

    ############################################################################

    def execute(
            self, 
            job, 
            config_obj: BaseConfig) -> Tuple[int, Dict[str, Any]]:
        """
        Front-facing method that executes some task strategy on the job.

        ARGUMENTS
        ---------
            job,
                Job object, contains as attributes all relevant information for
                running the job-specific task. 
            config_obj, 
                BaseConfig object, contains as attributes all relevant 
                information needed for general implementation of the task to be
                performed on the job. 

        RETURNS
        -------
            retcode,
                int, non-zero values indicate some error occurred during the 
                _strategy.execute() call.
            updates, 
                dict with string keys mapping to any type of values. Created 
                within the _strategy.execute() call and contains all attribute
                keys and values to update the input Job object. 
        """
        # run self.prepare() to set the self._strategy to be one of the 
        # imported task types (stashed in attributes).
        self.prepare(job.status)

        # run the self._strategy.execute() method; all handling of the job obj
        # happens inside of this method
        retcode, updates = self._strategy.execute(job, config_obj)
        
        return retcode, updates


    def prepare(self, job_status: Status):
        """
        Given the job status, assign the appropriate strategy to the Operator's 
        _strategy attribute.
        """
        if job_status == Status.NEW:
            self._strategy = self.StartStrategy()
        elif job_status == Status.RUNNING:
            self._strategy = self.CheckStatusStrategy()
        #elif job_status in Status.FINISHED:
        #    self._strategy = self.ArchiveStrategy
        ## NOTE need to handle Status states that don't have an associated strategy
        else:
            raise ValueError("Unknown job status type.")


