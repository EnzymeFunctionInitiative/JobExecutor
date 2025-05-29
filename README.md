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

or, to run an individual test, e.g. `tests/config_file_test.py':

```
pytest -q tests/config_file_test.py
```

## Running implementation tests
The `dummy` data strategy and task strategies are immediately useable to 
demonstrate the job executor implementation. Within the python env, run this
implementation test as:

```
cd job_exec
python3 executor.py --configuration-file ../templates/dummy.config
> Using taskStrategies.dummyStrategy as the source of task strategies.
> Using <class 'dataStrategies.baseStrategy.DictOfDictStrategy'> as the data handler strategy.
> A CheckStatus task is being performed for <Job job_id=2, status=running>.
> Updating running to finished
> A CheckStatus task is being performed for <Job job_id=3, status=running>.
> Updating running to finished
> A Start task is being performed for <Job job_id=4, status=new>.
> Updating new to running
> A Start task is being performed for <Job job_id=5, status=new>.
> Updating new to running

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
# create a fake SQLite database in tests/implementation_tests/testing.sqlite
python3 tests/create_fake_db.py templates/sqlite_dummy.config

# then follow the same instructions as above but point to the sqlite_dummy.config file
cd job_exec
python3 executor.py --configuration-file ../templates/sqlite_dummy.config
> Using taskStrategies.dummyStrategy as the source of task strategies.
> Using <class 'dataStrategies.sqlStrategy.SQLStrategy'> as the data handler strategy.
> Connected to database: sqlite:///../tests/implementation_tests/testing.sqlite
> A CheckStatus task is being performed for <Job(id=2, status='running', efi_type='est', timeCreated='2025-05-29 12:49:02.379173' timeStarted='2025-05-29 12:49:02.379176')>.
> Updating running to finished
> A CheckStatus task is being performed for <Job(id=3, status='running', efi_type='est', timeCreated='2025-05-29 12:49:02.379200' timeStarted='2025-05-29 12:49:02.379201')>.
> Updating running to finished
> A Start task is being performed for <Job(id=4, status='new', efi_type='ssn', timeCreated='2025-05-29 12:49:02.379220' )>.
> Updating new to running
> A Start task is being performed for <Job(id=5, status='new', efi_type='est', timeCreated='2025-05-29 12:49:02.379237' )>.
> Updating new to running
> Disconnected from database (session closed)
> Disconnected from database (engine disposed)

# OR use the interactive jupyter notebook to get hands on with the code
cd tests/implementation_tests/
jupyter notebook sql_dummy.ipynb
```



