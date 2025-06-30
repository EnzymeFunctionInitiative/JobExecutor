
from typing import Tuple, List

from .baseCheckStatus import BaseCheckStatus

class CheckStatus(BaseCheckStatus):
    def run(self, scheduler_id: int | str) --> Tuple[int, str]:
        """
        """
        return 0, "finished"

