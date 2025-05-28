
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
    def getStatus(self, status_str: str):
        if status_str is None:
            return None
        return getattr(self, status_str.upper(), None)


