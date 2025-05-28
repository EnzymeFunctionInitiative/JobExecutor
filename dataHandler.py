
from typing import Dict, Any
import importlib

from dataStrategies.baseStrategy import BaseDataStrategy
from configClasses.baseConfig import BaseConfig

class DataHandler:
    def __init__(self, mode_str: str, config: BaseConfig):
        """ 
        gets called when `with DataHandler(...) as data_handler` is run

        Since the DataStrategy object must contain all information regarding
        the data and its source, an instance of the Strategy object is needed.
        Can't just call the strategy's underlying methods (like a rudimentary
        strategy design pattern would suggest). 
        """
        
        # determine which dataStrategies module to import and gather the 
        # relevant class
        if (mode_str.lower() == "dummy" 
                or config["jobdb"]["type"].lower() in ["dummy","dictofdict"]):
            module = importlib.import_module(f"dataStrategies.baseStrategy")
            strategy_obj = getattr(module,"DictOfDictStrategy")
        #elif config["jobdb"]["type"].lower() == "csv":
        #    module = importlib.import_module(f"dataStrategies.csvStrategy")
        #    return getattr(module,"CSVStrategy")
        elif config["jobdb"]["type"].lower() in ["sqlite","mysql"]:
            module = importlib.import_module(f"dataStrategies.sqlStrategy")
            strategy_obj = getattr(module,"SQLStrategy")
        else:
            raise NotImplementedError("Data handler strategy not implemented." 
                + " Please set an appropriate value in the config file in" 
                + " section 'jobdb', keyword 'type'.")

        print(f"Using {str(strategy_obj)} as the data handler strategy.")
        
        # assign self._strategy to an instance of the dataStrategy object
        self._strategy: BaseDataStrategy = strategy_obj(config)

    # Defining the interface to interact with the dataStrategies:
    # - enable context management via __enter__ and __exit__
    # - enable gathering and updating "jobs" from the underlying _strategy obj
    def __enter__(self):
        """
        Enables clean opening of the data handler with a `with` statement
        """
        self._strategy.load_data()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """ 
        Enables clean closing of the data strategy's data stream while in a 
        `with` statement
        """
        self._strategy.close()

    def get_jobs(self, key):
        """
        must return an iterator of some sort, where each element in the 
        iterator contains information about "jobs"
        """
        return self._strategy.fetch_jobs(key)

    def update_job(self, job, updates_dict: Dict[str, Any]):
        """
        run the _strategy.update_job() method, where the job object is updated 
        using the updates_dict object.
        """
        self._strategy.update_job(job, updates_dict)


