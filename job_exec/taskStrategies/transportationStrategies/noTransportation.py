
from typing import Tuple, List
from pathlib import Path

from .baseTransportation import BaseTransport

class Transport(BaseTransport):
    def run(
        self,
        file_list: List[str | Path],
        from_destination: str | Path,
        to_destination: str | Path
    ) -> Tuple[int, List[str | Path]]:
        """ 
        No transportation is applied.
        Arguments
        ---------
            file_list
                list of strings or Path objects, pointing to files in the 
                from_destination directory. 
            from_destination
                string or Path object, the directory within which the files are
                stored.
            from_destination
                string or Path object, the directory to which the files are to
                be moved to.
        
        Results
        -------
            retcode
                int, 0 for successful transportation and 1 for a failure.
            file_list
                unaltered file_list from the input arguments.
        """
        return 0, file_list


