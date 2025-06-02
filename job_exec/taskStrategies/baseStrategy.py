
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    """ """

    @abstractmethod
    def execute(self, job_obj, config_obj):
        pass

