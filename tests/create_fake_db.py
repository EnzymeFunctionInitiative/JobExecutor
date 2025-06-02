
import sys
from datetime import datetime, timedelta

from configClasses.baseConfig import BaseConfig
from dataStrategies.sqlStrategy import SQLStrategy
from jobModels.job_orm import Job 
from constants import Status

config_file = sys.argv[1]

config = BaseConfig.read_ini_config(config_file)

job_db = SQLStrategy(config)

job_db.load_data()

row0 = Job(
    job_id = 1,
    user_id = 1,
    uuid = "aaa",
    status = "finished",
    efi_type = "est",
    timeCreated = datetime.now() - timedelta(hours = 1),
    timeStarted = datetime.now() - timedelta(hours = 1),
    timeCompleted = datetime.now(),
    dbVersion = "105",
    params = "a whole bunch of stuff",
    results = "another whole bunch of stuff",
    email = "test@hello.com",
    parentJob_id = None
)

row1 = Job(
    job_id = 2,
    user_id = 1,
    uuid = "bbb",
    status = "running",
    efi_type = "est",
    timeCreated = datetime.now() - timedelta(hours = 1),
    timeStarted = datetime.now() - timedelta(hours = 1),
    timeCompleted = None,
    dbVersion = "105",
    params = "a whole bunch of stuff",
    results = "another whole bunch of stuff",
    email = "test@hello.com",
    parentJob_id = None
)

row2 = Job(
    job_id = 3,
    user_id = 1,
    uuid = "bbb",
    status = "running",
    efi_type = "est",
    timeCreated = datetime.now() - timedelta(hours = 1),
    timeStarted = datetime.now() - timedelta(hours = 1),
    timeCompleted = None,
    dbVersion = "105",
    params = "a whole bunch of stuff",
    results = "another whole bunch of stuff",
    email = "test@hello.com",
    parentJob_id = None
)

row3 = Job(
    job_id = 4,
    user_id = 1,
    uuid = "ccc",
    status = "new",
    efi_type = "ssn",
    timeCreated = datetime.now() - timedelta(hours = 1),
    timeStarted = None,
    timeCompleted = None,
    dbVersion = "105",
    params = "a whole bunch of stuff",
    results = "another whole bunch of stuff",
    email = "test@hello.com",
    parentJob_id = None
)

row4 = Job(
    job_id = 5,
    user_id = 1,
    uuid = "ddd",
    status = "new",
    efi_type = "est",
    timeCreated = datetime.now() - timedelta(hours = 1),
    timeStarted = None,
    timeCompleted = None,
    dbVersion = "105",
    params = "a whole bunch of stuff",
    results = "another whole bunch of stuff",
    email = "test@hello.com",
    parentJob_id = None
)

row5 = Job(
    job_id = 6,
    user_id = 1,
    uuid = "aaa",
    status = "failed",
    efi_type = "est",
    timeCreated = datetime.now() - timedelta(hours = 1),
    timeStarted = datetime.now() - timedelta(hours = 1),
    timeCompleted = datetime.now(),
    dbVersion = "105",
    params = "a whole bunch of stuff",
    results = "another whole bunch of stuff",
    email = "test@hello.com",
    parentJob_id = None
)

row6 = Job(
    job_id = 7,
    user_id = 1,
    uuid = "aaa",
    status = "archived",
    efi_type = "est",
    timeCreated = datetime.now() - timedelta(hours = 1),
    timeStarted = datetime.now() - timedelta(hours = 1),
    timeCompleted = datetime.now(),
    dbVersion = "105",
    params = "a whole bunch of stuff",
    results = "another whole bunch of stuff",
    email = "test@hello.com",
    parentJob_id = None
)

job_db.session.add_all([row0, row1, row2, row3, row4, row5, row6])
job_db.session.commit()
job_db.close()

