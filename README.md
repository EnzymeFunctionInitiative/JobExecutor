# JobExecutor
Execute and monitor user-submitted jobs on local and remote clusters.

## Installation

The below installation instructions for this workflow code expects an 
installation of a conda distribution, such as Miniconda. Any package and env 
manager will work though.

```
# create the python environment via a Anaconda or Miniconda package manager. 
conda create -n job_exec python=3.10
conda activate job_exec
conda config --add channels conda-forge

# install from the pyproject.toml file
python3 -m pip install .
```


