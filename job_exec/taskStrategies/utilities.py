
import zipfile
import subprocess
from pathlib import Path
from typing import List

slurm_job_states = {
    "running" : ["PENDING", "REQUEUED", "RUNNING"],
    "failed"  : ["BOOT_FAIL","CANCELLED","DEADLINE","FAILED","NODE_FAIL","OUT_OF_MEMORY","PREEMPTED","SUSPENDED","TIMEOUT"],
    "finished": ["COMPLETED"]
}

def zip_files(zip_file_path: Path, file_list: List) -> Path:
    """
    Zip up the files in the list. 

    Arguments
    ---------
        zip_file_path
            Path, path where the zip file will be written.
        file_list
            List[str | Path], contains paths to files to be zipped up.
    """
    try:
        zip_file_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_file_path, "w") as zip_file:
            for file_path in file_list:
                zip_file.write(file_path, arcname = file_path.name)
    except zipfile.BadZipFile as e:
        print(f"Zipping files {file_list} failed.\n{e}")
        raise
    except OSError as e:
        print(f"Zipping files {file_list} failed.\n{e}")
        raise


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

