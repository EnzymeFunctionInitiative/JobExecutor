
from datetime import datetime
from typing import Dict, Any, List

import sqlalchemy
from sqlalchemy import func, inspect
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
    id: Mapped[int] = mapped_column(
        primary_key=True,
        info = {"is_parameter": True, "pipeline_key": "job_id"}
    )
    user_id: Mapped[int] = mapped_column(nullable=False)
    uuid: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[Status] = mapped_column(
        FlagEnumType(Status),
        nullable=False,
        info = {"is_updatable": True}
    )
    efi_type: Mapped[str] = mapped_column("type", nullable=False)
    timeCreated: Mapped[datetime] = mapped_column(
        nullable=False, 
        server_default=func.now()
    )
    timeStarted: Mapped[datetime | None] = mapped_column(
        info = {"is_updatable": True}
    )
    timeCompleted: Mapped[datetime | None] = mapped_column(
        info = {"is_updatable": True}
    )
    dbVersion: Mapped[str]
    params: Mapped[str | None] = mapped_column(
        info = {"is_parameter": True, "pipeline_key": "parameters"}
    )
    results: Mapped[str | None] = mapped_column(
        info = {"is_updatable": True}
    )
    email: Mapped[str]
    parentJob_id: Mapped[int | None]

    def __repr__(self):
        if self.status in Status.COMPLETED:
            completed_string = f"timeStarted='{self.timeStarted}', timeCompleted='{self.timeCompleted}'"
        elif self.status == Status.RUNNING:
            completed_string = f"timeStarted='{self.timeStarted}'"
        else:
            completed_string = ""
        return (f"<Job(id={self.id}," 
                + f" status='{self.status}'," 
                + f" efi_type='{self.efi_type}'," 
                + f" timeCreated='{self.timeCreated}'" 
                + f" {completed_string})>")

    def get_parameters_dict(self) -> Dict[str, Any]:
        """
        Create a dictionary of attributes that should be written to a
        params.yaml file.
        """
        mapper = inspect(self.__class__)
        return {
            key: value
            for key, value in mapper.attrs.items()  # need to check that .items() actually returns key and value
            if isinstance(attr, MappedColumn)
            and attr.column.info.get("is_parameter")
        }

    def get_updatable_attrs(self) -> List[str]:
        """
        Create a list of attribute names that can have their values updated. 
        """
        mapper = inspect(self.__class__)
        return [ 
            key for key, value in mapper.attrs.items() 
            if attr.column.info.get("is_updatable")
        ]

