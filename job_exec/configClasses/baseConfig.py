
from typing import Dict, Any

import configparser
import json

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

        These three attributes will be empty dictionaries if left undefined in 
        the input parameter_dict. 
    """
    
    def __init__(self, parameter_dict: Dict[str, Any]) -> None:
        """ """
        self.jobdb_dict = parameter_dict.get("jobdb", {})
        self.compute_dict = parameter_dict.get("compute",{})
        self.transport_dict = parameter_dict.get("transportation",{})
        # do not collect any other fields to avoid incorporating unnecessary
        # or injected config sections

    #################
    # factory methods
    @classmethod
    def read_ini_config(cls, config_path: str):
        """ 
        Method to read a configuration file. Assumes that all necessary 
        information about both the jobdb and compute configurations are stored
        in this one file.
        """
        config = configparser.ConfigParser()
        config.read(config_path)
        config = {s: dict(config.items(s)) for s in config.sections()}
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

    # what other methods are needed for the config interface? 


