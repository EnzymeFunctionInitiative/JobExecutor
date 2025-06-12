
from typing import Union
from enum import Flag, auto

class Status(Flag):
    """ Setting accessible status states """
    NEW = auto()
    RUNNING = auto()
    FINISHED = auto()
    FAILED = auto()
    ARCHIVED = auto()
    
    # flag combinations
    INCOMPLETE = NEW | RUNNING
    COMPLETED = FINISHED | FAILED | ARCHIVED
    CURRENT = NEW | RUNNING | FINISHED | FAILED
    ALL = NEW | RUNNING | FINISHED | FAILED | ARCHIVED

    def __str__(self):
        return self.name.lower()

    @classmethod
    def get_flag(cls, status: Union[int, str]):
        try:
            if type(status) == int:
                return cls(status)
            elif type(status) == str:
                return getattr(cls, status.upper())
            else:
                raise ValueError(f"Given status value ({status}) is" 
                    + " incorrectly typed.")
        except (ValueError, AttributeError) as e:
            print(f"Given status value ({status}) does not match a Status" 
                + f" Flag.\n{e}")
            raise

