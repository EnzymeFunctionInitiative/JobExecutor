
from abc import ABC, abstractmethod

class BaseTransport(ABC):
    """ """

    @abstractmethod
    def run(self, file_list, from_destination, to_destination):
        pass

