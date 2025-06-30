
from typing import Dict, Any

import configparser
import json
import os

class BaseConfig:
    """
    Class used to gather necessary configuration details about the resources
    to be used to run EFI tools' nextflow codes. Two resources in particular
    need to have parameters specified in this object:
        - the resource hosting the JobDB. Parameters stored in the `jobdb_dict`
          attribute.
        - the compute resource running the EFI tools. Parameters stored in the
          `compute_dict` attribute.
        - the means of transporting data between the two resources. Parameters
          stored in the 'transport_dict' attribute.

    Parameters
    ----------
        parameter_dict
            dict, expected to be a multi-layered dict of dicts. parameter names
            mapping to their subdict or values.

    Attributes
    ----------
        jobdb_dict
            dict, generally expecting str keys mapping to str values; relevant
            parameters for accessing the database containing information about
            each task/job.
        compute_dict
            dict, generally expecting str keys mapping to str values; relevant
            parameters for the compute resource being used.
        transport_dict
            dict, generally expecting str keys mapping to str values; relevant
            parameters for moving data/files between the jobdb and compute
            file systems.
        strategies_dict
            dict, contains the file paths to strategy code that implement the
            preparation, execution/submission, and transportation of EFI 
            input/output files. 

        The first three attributes will be empty dictionaries if left undefined
        in the input parameter_dict. If strategies_dict is incomplete, the 
        working shell environment will be queried for env variables that may 
        have been defined. If these env vars don't exist, a RuntimeError will 
        be thrown to prevent any job table interactions from happening before
        a failure in the executor.
        
        preparation_strategy
            class, defined in the "preparation_strategy_file" sub-parameter in
            the strategies_dict or in EFI_PREPARATION_STRATEGY env var.
        execution_strategy
            class, defined in the "execution_strategy_file" sub-parameter in
            the strategies_dict or in EFI_EXECUTION_STRATEGY env var.
        transport_strategy
            class, defined in the "transport_strategy_file" sub-parameter in
            the strategies_dict or in EFI_TRANSPORT_STRATEGY env var.
    """
    
    def __init__(self, parameter_dict: Dict[str, Any]) -> None:
        """ """
        self.jobdb_dict = parameter_dict.get("jobdb", {})
        self.compute_dict = parameter_dict.get("compute",{})
        self.transport_dict = parameter_dict.get("transportation",{})
        
        # given a strategies subsection (or not) in the config file, determine
        # if the specified strategy classes are importable before any 
        # calculations are run.
        self.strategies_dict = parameter_dict.get("strategies",{})
        strategies = self.validate_strategies()
        self.preparation_strategy = strategies[0]
        self.execution_strategy = strategies[1]
        self.transport_strategy = strategies[2]

    #################
    # factory methods
    @classmethod
    def read_ini_config(cls, config_path: str):
        """
        Method to read a configuration file. Assumes that all necessary
        information about both the jobdb and compute configurations are stored
        in this one file.
        """
        # parse the config as normal
        config = configparser.ConfigParser()
        config.read(config_path)
        config = {s: dict(config.items(s)) for s in config.sections()}
        
        ## check to see if the transport_strategy key is already present, if
        ## it isn't, assign it to be a dict.
        #config["transport_strategy"] = config.get(
        #    "transport_strategy",
        #    {}
        #)

        ## INI files can't handle arrays, so strategies are contained as single
        ## line key entries. Get that one liner and check to make sure its not
        ## already included as a key in the transport_strategy subdictionary
        #str_val = config.get("new_transport_strategy")
        #if str_val and not config["transport_strategy"].get("new"):
        #    # split the single-lined, comma-separated entry into a list; remove
        #    # white space from both ends of the strings
        #    list_val = [elem.strip() for elem in str_val.split(",")]
        #    # add a subdict containing the contents
        #    config["transport_strategy"]["new"] = {
        #        "destination1": list_val[0],
        #        "destination2": list_val[1]
        #    }
        #
        ## INI files can't handle arrays, so strategies are contained as single
        ## line key entries. Get that one liner and check to make sure its not
        ## already included as a key in the transport_strategy subdictionary
        #str_val = config.get("finished_transport_strategy")
        #if str_val and not config["transport_strategy"].get("finished"):
        #    # split the single-lined, comma-separated entry into a list; remove
        #    # white space from both ends of the strings
        #    list_val = [elem.strip() for elem in str_val.split(",")]
        #    # add a subdict containing the contents
        #    config["transport_strategy"]["finished"] = {
        #        "destination1": list_val[0],
        #        "destination2": list_val[1]
        #    }
        
        return cls(config)

    @classmethod
    def read_json_config(cls, config_path: str):
        """
        Method to read a configuration file. Assumes that all necessary
        information about both the jobdb and compute configurations are stored
        in this one file.
        """
        with open(config_path, 'r') as f:
            config = json.load(f)
        return cls(config)
    #################
    
    #################
    ## Writer methods
    #def write_ini_config(self, config_path: str) -> str:
    #    """
    #    Method to write an INI formatted configuration file. Only write out
    #    the relevant configuration dictionaries to this new file.
    #    """
    #    config = configparser.ConfigParser()
    #    if self.jobdb_dict:
    #        config.read_dict({"jobdb": self.jobdb_dict})
    #    if self.compute_dict:
    #        config.read_dict({"compute": self.compute_dict})
    #    if self.transport_dict:
    #        config.read_dict({"transportation": self.transport_dict})
    #    config.write(config_path, space_around_delimiters=False)

    #def write_json_config(self, config_path: str):
    #    """
    #    Method to write an json formatted configuration file. Only write out
    #    the relevant configuration dictionaries to this new file.
    #    """
    #    with open(config_path, 'w') as f:
    #        json.dump(
    #            {
    #                "jobdb": self.jobdb_dict,
    #                "compute": self.compute_dict,
    #                "transportation": self.transport_dict
    #            },
    #            f,
    #            indent = 4
    #        )
    #################


    def get_attribute(self, attrname: str, default: Any = None):
        """ Getter for an attribute's value """
        return getattr(self, attrname, default)
    
    #def set_attribute(self, attrname: str, value: Any = True):
    #    """ Setter for creating attributes """
    #    return setattr(self, attrname, value)

    def get_parameter(self, attr, key, default: Any = None):
        """ Getter for a parameter defined within one of the config dicts """
        attr_dict = self.get_attribute(attr, {})
        return attr_dict.get(key, default)

    #def set_parameter(self, attr: str, key: str, value: Any = True):
    #    """ Setter for a parameter defined within one of the config dicts """
    #    attr_dict = self.get_attribute(attr, {})
    #    attr_dict.update({key: value})
    #    if not attr_dict:
    #        self.set_attribute(attr, attr_dict)

    def validate_strategies(self):
        """ 
        Validation of task preparation/execution/transportation strategy 
        classes.
        """
        preparation_strategy_module = self.get_parameter(
            "strategies_dict",
            "preparation_strategy_file",
            os.getenv("EFI_PREPARATION_STRATEGY")
        )
        if preparation_strategy_module:
            module = importlib.import(preparation_strategy_module)
            preparation_strategy = getattr(module, "Preparation")
        else:
            raise RuntimeError("No Preparation Strategy defined.")

        execution_strategy_module = self.get_parameter(
            "strategies_dict",
            "execution_strategy_file",
            os.getenv("EFI_EXECUTION_STRATEGY")
        )
        if execution_strategy_module:
            module = importlib.import(execution_strategy_module)
            execution_strategy = getattr(module, "Submit")
        else:
            raise RuntimeError("No submission/execution strategy defined.")

        transport_strategy_module = self.get_parameter(
            "strategies_dict",
            "transport_strategy_file",
            os.getenv("EFI_TRANSPORT_STRATEGY")
        )
        if transport_strategy_module:
            module = importlib.import(transport_strategy_module)
            transport_strategy = getattr(module, "Transport")
        else:
            raise RuntimeError("No transportation strategy defined.")

        return preparation_strategy, execution_strategy, transport_strategy

    # what other methods are needed for the config interface?


