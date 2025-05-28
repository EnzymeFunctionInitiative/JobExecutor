
from typing import Tuple, List, Dict, Any

import sqlalchemy
from sqlalchemy import URL, create_engine, Column, Integer, String, DateTime, Enum, func, select
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase, mapped_column, Mapped
from sqlalchemy.types import TypeDecorator

from constants import Status
from jobModels.job_orm import Base, Job
from configClasses.baseConfig import BaseConfig

# giving an example of a data strategy, only made complex by creating Job class
# objects to mirror behavior from SQLAlchemy ORM database Job class objects
class SQLStrategy(BaseDataStrategy):
    """ for dummy testing """ 
    def __init__(self, config: BaseConfig):
        """ 
        Need an init for these strategies since the strategy obj will handle
        all data context internally. 
        """
        self.config = config.get_attribute("jobdb", {})

        self.db_url = self.create_db_url()
        
        self.engine: Optional[sqlalchemy.engine.Engine] = None
        self.Session: Optional[sqlalchemy.orm.sessionmaker] = None
        self.session: Optional[sqlalchemy.orm.Session] = None

        self.updatable_attrs = [
            "status",
            "timeStarted",
            "timeCompleted",
            "results"
        ]

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

    def load_data(self):
        """ 
        Establish a connection to the database
        """
        try:
            self.engine = create_engine(self.db_url)
            
            # Create tables if they don't exist
            Base.metadata.create_all(self.engine) 
            
            self.Session = sessionmaker(bind=self.engine)
            self.session = self.Session()
            print(f"Connected to database: {self.db_url}")
            
        # handle exceptions better
        except Exception as e:
            print(f"Error connecting to database: {e}")
            raise

    def close(self):
        """
        Close the connection to the database.  SQLAlchemy handles connection 
        pooling, so the connection is not explicitly closed here. Instead, 
        dispose of the session.
        """
        try:
            if self.session:
                self.session.close()
                self.session = None
                print("Disconnected from database (session closed)")
            if self.engine:
                self.engine.dispose()
                self.engine = None
                print("Disconnected from database (engine disposed)")
            
        # handle exceptions better
        except Exception as e:
            print(f"Error disconnecting from database: {e}")
            raise

    def fetch_jobs(self, 
            status: Status = Status.INCOMPLETE
            ) -> sqlalchemy.engine.ChunkedIteratorResult:
        """ 
        Return an iterator containing Job objects associated with rows in the
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
            statement = select(Job).where(Job.status.in_(status_strings))
            # execute the query
            jobs = self.session.execute(statement)
            return jobs
        except Exception as e:
            print(f"Error fetching unfinished jobs: {e}")
            raise

    def update_job(self, job_obj: Job, update_dict: Dict[str, Any]) -> None: 
        """
        Update the Job object's attributes with information contained in the
        update_dict. 
        
        Arguments
        ---------
            job_obj
                Job, the ORM class to denote a row in table Job. 
            updates_dict 
                dict, keys map to Job attributes (column names) and associated
                values are the new values to be updated to. 
        """
        if not self.session:
            raise Exception("Not connected to the database")

        if not updates_dict:
            print(f"No updates applied to the Job ({job_obj.__repr__}).")
            return

        for key, value in updates_dict.items():
            if key not in self.updatable_attrs: 
                continue
            setattr(job_obj, key, value)
        
        self.session.commit()


