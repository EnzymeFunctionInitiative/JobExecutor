
from typing import Dict, Tuple, Any
import importlib

import sqlalchemy
from sqlalchemy import URL, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from constants import Status
from configClasses.baseConfig import BaseConfig
from .baseStrategy import BaseDataStrategy

class SQLStrategy(BaseDataStrategy):
    def __init__(self, config: BaseConfig):
        """ 
        Need an init for these strategies since the strategy obj will handle
        all data context internally. 
        """
        self.config = config.get_attribute("jobdb_dict", {})

        self.db_url = self.create_db_url()

        self._Base, self._Job = self.set_table_structure()

        self.engine: Optional[sqlalchemy.engine.Engine] = None
        self.Session: Optional[sqlalchemy.orm.sessionmaker] = None
        self.session: Optional[sqlalchemy.orm.Session] = None

    def create_db_url(self) -> str:
        """ 
        Create the database url used in SQLAlchemy to connect to an engine. 
    
        Returns
        -------
            db_url,
                str, points to the database to be queried. format: 
                'sqlite:///./jobs.db', 
                'mysql+mysqlconnector://user:pass@host/dbname'
        """
        # sqlalchemy URL prep
        url_dict = {}
        
        # unfortunately fields in the config files we currently use do not match
        # the expected input argument names to the 
        # sqlalchemy.engine.URL.create() method. Specifically, "user" should be
        # "username" and "dbi" may or may not be defined explicitly.
        dbi = self.config.get("dbi")
        if dbi:
            url_dict["drivername"] = dbi
        else:
            url_dict["drivername"] = "mysql"
    
        username = (self.config.get("username") or self.config.get("user"))
        if username:
            url_dict["username"] = username
        
        # Unfortunately...
        # url_dict["password"] should map to a string, containing the password 
        # characters exactly as they would be typed. Does _not_ need to be URL 
        # encoded when passed as an arg to URL.create()
        password = self.config.get("password")
        if password:
            url_dict["password"] = password
        
        host = self.config.get("host")
        if host:
            url_dict["host"] = host
        
        port = self.config.get("port")
        if port:
            url_dict["port"] = port
        
        # handle the rare cases where the user specified the DBAPI.
        # expected format in the URL for "drivername" is {dialect}[+{driver}] where
        # dialect specifies the database backend (a "dialect" in sqlalchemy terms)
        # and driver specifies the DBAPI to be used to connect to the database. 
        # if the driver is left unspecified, then sqlalchemy uses a default API
        # that is described as "the most widely known driver available" for the 
        # dialect. sqlite -> sqlite3, mysql -> mysqlclient
        # https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls
        dbapi = self.config.get("dbapi")
        if dbapi:
            url_dict["drivername"] += "+" + dbapi
    
        url_dict["database"] = self.config.get("db_name")
        if not url_dict["database"]:
            raise ValueError("User must supply a database name in the config"
                + " file when using the SQLStrategy datahandler.")

        # create the url
        db_url = URL.create(**url_dict)
        return db_url

    def set_table_structure(self) -> Tuple[DeclarativeBase,DeclarativeBase]:
        """
        A small strategy design pattern to enable the use of various table
        designs within this SQLAlchemy interface. If 
        self.config.get("table_def") returns None, then a dummy Job table 
        definition will be imported from job_exec/jobModels/job_dummy_orm.py.
        Else, the file path defined in "table_def" will be imported and the
        Base and Job class will be assigned to the self._Base and self._Job
        attributes. 

        This enables testing of the SQL interface without implementing a fake
        Job table that exactly mirrors the one created from the EFI website.
        """
        job_table_module = self.config.get("table_def")
        if job_table_module:
            module = importlib.import_module(job_table_module)
            return getattr(module, "Base"), getattr(module, "Job")
        else:
            from jobModels.job_dummy_orm import Base, Job
            return Base, Job

    ############################################################################
    # interface methods
    def load_data(self):
        """ 
        Establish a connection to the database
        """
        try:
            self.engine = create_engine(self.db_url)
            
            # Create tables if they don't exist
            self._Base.metadata.create_all(self.engine) 
            
            self.Session = sessionmaker(bind=self.engine)
            self.session = self.Session()
            print(f"Connected to database: {self.db_url}")
            
        # NOTE handle exceptions better
        except Exception as e:
            print(f"Error connecting to database: {e}")
            raise

    def close(self):
        """
        Close the connection to the database.  SQLAlchemy handles connection 
        pooling, so the connection is not explicitly closed here. Instead, 
        dispose of the session.
        """
        # check that any changes get commit to the db before close is executed
        self.session.commit()
        try:
            if self.session:
                self.session.close()
                self.session = None
                print("Disconnected from database (session closed)")
            if self.engine:
                self.engine.dispose()
                self.engine = None
                print("Disconnected from database (engine disposed)")
            
        # NOTE handle exceptions better
        except Exception as e:
            print(f"Error disconnecting from database: {e}")
            raise

    def fetch_jobs(self, 
            status: Status = Status.INCOMPLETE
            ) -> sqlalchemy.engine.ChunkedIteratorResult:
        """ 
        Return a generator containing Job objects associated with rows in the
        SQL table that pass the status comparison.

        Arguments
        ---------
            status,
                Status flag to denote the status of the jobs to be fetched 
                (e.g., 'Status.QUEUED', 'Status.FINISHED', 'Status.INCOMPLETE')

        Returns
        -------
            sqlalchemy.engine.result.ChunkedIteratorResult
                result from the self.session.execute() call. Is an iterator. 
        """
        if not self.session:
            raise Exception("Not connected to the database")
        
        # status can be a combined flag, if so, need to break it into its 
        # components
        status_strings = [flag.__str__() for flag in Status if flag in status]
        try:
            # query string using the status_strings list
            statement = select(self._Job).where(self._Job.status.in_(status_strings))
            # execute the query
            for job in self.session.execute(statement):
                yield job[0]
        # NOTE handle exceptions better
        except Exception as e:
            print(f"Error fetching unfinished jobs: {e}")
            raise

    def update_job(self, job_obj, update_dict: Dict[str, Any]) -> None: 
        """
        Update the Job object's attributes with information contained in the
        update_dict. 
        
        Arguments
        ---------
            job_obj
                Job, the ORM class to denote a row in table Job. 
            update_dict 
                dict, keys map to Job attributes (column names) and associated
                values are the new values to be updated to. 
        """
        if not self.session:
            raise Exception("Not connected to the database")

        if not update_dict:
            print(f"No updates applied to the Job ({job_obj.__repr__}).")
            return

        updatable_columns = job_obj.get_updatable_attrs()
        for key, value in update_dict.items():
            if key not in updatable_columns: 
                continue
            setattr(job_obj, key, value)
        
        self.session.commit()
    ############################################################################


