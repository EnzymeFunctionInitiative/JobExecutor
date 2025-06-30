
from typing import Tuple, List
from pathlib import Path

from .baseTransportation import BaseTransport

class Transport(BaseTransport):
    def run(
        self,
        file_list: List[str | Path],
        from_destination: str | Path,
        to_destination: str | Path
    ) -> Tuple[int, List[str | Path | RuntimeError]]:
        """
        Transport files via pathlib's Path.rename method to move files' Path
        objects from a path in from_destination to a path in to_destination.

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
            list filled with string or Path objects when the transporation was
            successful. Or filled with a RuntimeError if the transportation
            failed.
                
        """
        # convert string destinations to Path objects; do so even if they are
        # already Path objects -- no harm in doing so.
        from_destination = Path(from_destination)
        to_destination = Path(to_destination)
        # loop over all files.
        new_file_list = []
        for file in file_list:
            # convert file string to a Path object.
            file = Path(file)
            # check to see if from_destination is not a subpath of file; if 
            # True, add the from_destination path to the file path.
            if not from_destination in file.parents:
                file = from_destination / file
            # check to see that file exists.
            if file.is_file():
                # if it exists, move it to the to_destination with the same 
                # file name.
                new_file = to_destination / file.name
                file.rename(new_file)
                new_file_list.append(new_file)
                print(f"Moved {file} to {new_file}.")
            else:
                return 1, [RuntimeError(f"{file} does not exist. Check the" 
                    + " input destinations."),]

        return 0, new_file_list


