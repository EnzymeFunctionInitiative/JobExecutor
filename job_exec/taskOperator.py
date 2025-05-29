
from __future__ import annotations
from typing import Tuple, Dict, Any
import importlib

from constants import Status

from taskStrategies.baseStrategy import BaseStrategy
from configClasses.baseConfig import BaseConfig

class Operator:
    """
    """

    def __init__(self, mode: str) -> None:
        self.mode = mode
        self._strategy = None

        # ensure the given mode has actually been implemented
        self.check_mode()
        
        # assign instance attributes for self.StartStrategy,
        # self.CheckStatusStrategy, and self.TransferStrategy
        self.get_strategies()
        
    def check_mode(self):
        """ Kill the init if the given self.mode is not implemented. """
        # update this list as new modes are implemented
        if self.mode not in ["dummy","mysql","sqlite"]:
            raise NotImplementedError("This mode is not implemented. Try" 
                + "something different, like 'dummy'")

    ############################################################################
    ## Strategy Design Pattern Handles
    ## NOTE REMOVE PROPERTY AND JUST self._strategy = ...
    #@property
    #def strategy(self) -> BaseStrategy:
    #    """
    #    The Context maintains a reference to one of the Strategy objects. The
    #    Context does not know the concrete class of a strategy. It should work
    #    with all strategies via the Strategy interface.
    #    """

    #    return self._strategy


    #@strategy.setter
    #def strategy(self, strategy: BaseStrategy) -> None:
    #    """
    #    Usually, the Context allows replacing a Strategy object at runtime.
    #    """

    #    self._strategy = strategy


    def get_strategies(self):
        """
        The self.mode attribute is used to identify a submodule file from which
        the associated Strategies are imported and assigned to attributes.
        """
        try:
            module = importlib.import_module(f"taskStrategies.{self.mode}Strategy")
            self.StartStrategy = getattr(module, "Start")
            self.CheckStatusStrategy = getattr(module, "CheckStatus")
            #self.TransferStrategy = getattr(module, "Transfer")
            #self.ArchiveStrategy = getattr(module, "Archive")
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
        retcode, results = self._strategy.execute(job, config_obj)
        
        return retcode, results


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


