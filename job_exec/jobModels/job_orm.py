
import sqlalchemy

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy.types import TypeDecorator

class FlagEnumType(TypeDecorator):
    """ 
    SQLAlchemy does not know how to handle python Enum/Flag values as DB column
    values. This class is developing the custom handling of a String column 
    (stored as a VARCHAR or equivalent) and an associated python Flag object.

    This is general code that works for any python Flag Enum, but is intended 
    for the Status object and the status column in the DB. 
    """
    impl = String   # DB column is implemented as a SQLAlchemy String 
    cache_ok = True

    def __init__(self, enum_class, *args, **kwargs):
        self.enum_class = enum_class
        super().__init__(*args, **kwargs)

    def process_bind_param(self, value: Status, dialect):
        """ 
        Overwrite TypeDecorator.process_bind_param() method to implement custom
        handling for this object. Documentation:
        https://docs.sqlalchemy.org/en/20/core/custom_types.html#sqlalchemy.types.TypeDecorator.process_bind_param

        This is used to convert an instance of the python Flag class (e.g. 
        Status.QUEUED) into a string that can be used in the SQL DB (e.g. 
        "queued"). 
        """
        return value.__str__()

    def process_result_value(self, value, dialect):
        """
        Overwrite TypeDecorator.process_result_value() method to implement 
        custom handling for this object. Documentation:
        https://docs.sqlalchemy.org/en/20/core/custom_types.html#sqlalchemy.types.TypeDecorator.process_result_value

        This is used to convert a result-row column's value to the returned 
        python type, in this case a Flag object (e.g. "queued" in the DB is 
        converted to Status.QUEUED)
        """
        if value is None:
            return None
        return self.enum_class.getStatus(value)

class Base(DeclarativeBase):
    ## can do a whole bunch of stuff in this class before passing it on to 
    ## inhereting class/tables like explicitly control python types and their 
    ## associated sqlalchemy types
    #type_annotation_map = {}
    pass

class Job(Base):
    """
    SQLAlchemy model for the 'Job' table.
    """
    __tablename__ = 'Job'

    # SQLalchemy ORM 2.0x notes: PEP484 type annotations used with `Mapped`
    # enables skipping the `mapped_column()` call. The `Mapped` annotation can
    # be used to set datatype _and_ nullability for the column. Default for 
    # nullable is True for non-primary key columns.
    job_id: Mapped[int] = mapped_column("id", primary_key=True)
    user_id: Mapped[int] = mapped_column(nullable=False)
    uuid: Mapped[str] = mapped_column(nullable=False)   # typing.UUID?
    #status: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[Status] = mapped_column(FlagEnumType(Status), nullable=False)
    efi_type: Mapped[str] = mapped_column("type", nullable=False)
    timeCreated: Mapped[datetime] = mapped_column(
        nullable=False, 
        server_default=func.now()
    )
    timeStarted: Mapped[datetime | None]
    timeCompleted: Mapped[datetime | None]
    dbVersion: Mapped[str]
    params: Mapped[str | None]
    results: Mapped[str | None]
    email: Mapped[str]
    parentJob_id: Mapped[int | None]
  
    def __repr__(self):
        if self.status in Status.COMPLETED:
            completed_string = f"timeStarted='{self.timeStarted}', timeCompleted='{self.timeCompleted}'"
        elif self.status == Status.RUNNING:
            completed_string = f"timeStarted='{self.timeStarted}'"
        else:
            completed_string = ""
        return (f"<Job(id={self.job_id}," 
                + f" status='{self.status}'," 
                + f" efi_type='{self.efi_type}'," 
                + f" timeCreated='{self.timeCreated}'" 
                + f" {completed_string})>")

