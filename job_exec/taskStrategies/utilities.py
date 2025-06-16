
import subprocess
from typing import List
from .baseStrategy import BaseStrategy

def run_command(cmd: str):
    """
    Wrapper function to handle the subprocess.Popen call. 

    Arguments
    ---------
        cmd
            str, full string of the command to be run. Will be separated into
            args list internally.

    Returns
    -------
        On success:
            retcode
                int, return code from the Popen call. Non-zero values indicate
                failure. 
            stdout
                str, the standard output text from the Popen call.
            stderr
                str, the standard error text from the Popen call.
        On failure:
            retcode
                int, return code from the Popen call. Non-zero values indicate
                failure. 
            errorType
                Error obj, the exception object associated with the error
                being raised
    """
    try:
        # run the process
        process = subprocess.Popen(
            cmd.split(),
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            shell = True,
        )
        comms = process.communicate()
        retcode = process.returncode
        
        # if retcode != 0, then the process failed
        if retcode:
            return retcode, (
                RuntimeError(
                    f"Command failed: {cmd}\n{comms.stderr.decode()}"
                )
            )
        
        return process.returncode, (
            comms.stdout.decode(), 
            comms.stderr.decode()
        )

    except Exception as e:
        return 1, (e)

