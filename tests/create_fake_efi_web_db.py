
import sys
from datetime import datetime, timedelta

from configClasses.baseConfig import BaseConfig
from dataStrategies.sqlStrategy import SQLStrategy
from jobModels.job_efi_web_orm import Job, ESTGenerateFamiliesJob
from constants import Status

config_file = sys.argv[1]

config = BaseConfig.read_ini_config(config_file)

job_db = SQLStrategy(config)

job_db.load_data()

row0 = ESTGenerateFamiliesJob(
    job_id = 1,
    uuid = "aaa",
    status = Status.NEW,
    isPublic = False,
    efi_db_version = "105",
    job_type = "est_generate_families",
    timeCreated = datetime.now(),
    allByAllBlastEValue = 5,
    families = "pf05544",
    fraction = 1,
)

job_db.session.add_all([row0])
job_db.session.commit()
job_db.close()

