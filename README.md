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

# if jupyter notebooks/lab will be used to test implementations
conda install jupyterlab
```

## Running the unit tests
Unit tests are implemented for each moving part of the job executor. To run all
tests: 

```
conda activate job_exec
pytest
```

or, to run individual tess, e.g. `tests/config_file_test.py':

```
pytest -q tests/config_file_test.py
```

## Running implementation tests
The `dummy` data strategy and task strategies are immediately useable to 
demonstrate the job executor implementation. Within the python env, run this
implementation test as:

```
cd job_exec
python3 executor.py --mode dummy --configuration-file ../templates/dummy.config
# OR use the interactive jupyter notebook to get hands on with the code
cd tests/implementation_tests/
jupyter notebook dummy.ipynb
```

This results in a dummy dataset being used to run through the executor.py 
script. Print statements from the dummy task and data strategies highlight 
how jobs evolve as tasks are "performed" on them. In reality, nothing is 
happening on the back end; that is left to more complex task strategies and
real job datasets. 

A more real implementation test is run via: 
```

```
