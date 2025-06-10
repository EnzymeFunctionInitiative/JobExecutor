
from datetime import datetime

from typing import ClassVar

import sqlalchemy

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped

from constants import Status
from jobModels.flag_enum_type import FlagEnumType

class Base(DeclarativeBase):
    ## can do a whole bunch of stuff in this class before passing it on to 
    ## inhereting class/tables like explicitly control python types and their 
    ## associated sqlalchemy types
    #type_annotation_map = {}
    pass

class Job(Base):
    """
    SQLAlchemy model for a fake 'Job' table that kind of mirrors that of the 
    real EFI Job table. This should only be used for dummy testing of the 
    SQLAlchemy interface. 
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
 
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s)
    _parameter_attrs: ClassVar[set[str]] = frozenset([
        "job_id",
        "params",
    ])

    # assign a class variable to contain parameters that can be updated as jobs
    # are processed
    _updatable_attrs: ClassVar[set[str]] = frozenset([
        "status",
        "timeStarted",
        "timeCompleted",
        "results",
    ])

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


