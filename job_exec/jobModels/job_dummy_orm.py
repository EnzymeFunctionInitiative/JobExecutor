
from datetime import datetime

import sqlalchemy

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy.types import TypeDecorator

from constants import Status

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


# from efi-web:
# migrations/Version20250514011931.php
#       $this->addSql('CREATE TABLE Job (id INT AUTO_INCREMENT NOT NULL, user_id INT DEFAULT NULL, uuid CHAR(36) NOT NULL COMMENT \'(DC2Type:guid)\', status VARCHAR(255) NOT NULL, type VARCHAR(255) NOT NULL, timeCreated DATETIME DEFAULT NULL, timeStarted DATETIME DEFAULT NULL, timeCompleted DATETIME DEFAULT NULL, efi_db_version VARCHAR(255) DEFAULT NULL, params JSON DEFAULT NULL COMMENT \'(DC2Type:json)\', results JSON DEFAULT NULL COMMENT \'(DC2Type:json)\', email VARCHAR(255) DEFAULT NULL, isPublic TINYINT(1) NOT NULL, parentJob_id INT DEFAULT NULL, job_type VARCHAR(255) NOT NULL, blastQuery VARCHAR(255) DEFAULT NULL, blastMaxSequences INT DEFAULT NULL, blastDatabase VARCHAR(255) DEFAULT NULL, blastEValue INT DEFAULT NULL, domain TINYINT(1) DEFAULT NULL, domainRegion VARCHAR(255) DEFAULT NULL, inputFasta LONGTEXT DEFAULT NULL, filterByFamilies VARCHAR(255) DEFAULT NULL, accessionIds VARCHAR(255) DEFAULT NULL, domainFamily VARCHAR(255) DEFAULT NULL, filename VARCHAR(255) DEFAULT NULL, sequenceDatabase VARCHAR(255) DEFAULT NULL, exclude_fragments TINYINT(1) DEFAULT NULL, minLength INT DEFAULT NULL, maxLength INT DEFAULT NULL, maxBlastSequences INT DEFAULT NULL, blastSequence LONGTEXT DEFAULT NULL, eValue INT DEFAULT NULL, maxSeqMSA INT DEFAULT NULL, minSeqMSA INT DEFAULT NULL, cooccurrence DOUBLE PRECISION DEFAULT NULL, neighborhood_size INT DEFAULT NULL, referenceDatabase VARCHAR(255) DEFAULT NULL, cdhitSequenceIdentity INT DEFAULT NULL, searchType VARCHAR(255) DEFAULT NULL, minSequenceLength INT DEFAULT NULL, maxSequenceLength INT DEFAULT NULL, allByAllBlastEValue INT DEFAULT NULL, jobName VARCHAR(255) DEFAULT NULL, excludeFragments TINYINT(1) DEFAULT NULL, families VARCHAR(255) DEFAULT NULL, sequence_version VARCHAR(255) DEFAULT NULL, fraction INT DEFAULT NULL, taxSearch VARCHAR(255) DEFAULT NULL, taxSearchName VARCHAR(255) DEFAULT NULL, INDEX IDX_C395A618A76ED395 (user_id), INDEX IDX_C395A6184A4533A0 (parentJob_id), PRIMARY KEY(id)) DEFAULT CHARACTER SET utf8mb4 COLLATE `utf8mb4_unicode_ci` ENGINE = InnoDB');
# migrations/Version2025052614521.php
#       $this->addSql('ALTER TABLE Job ADD alignmentScore DOUBLE PRECISION DEFAULT NULL, ADD alignmentScoreThreshold DOUBLE PRECISION DEFAULT NULL, ADD computeNeighborhoodConnectivity TINYINT(1) DEFAULT NULL, ADD fastaInput VARCHAR(255) DEFAULT NULL, ADD metagenomes LONGTEXT DEFAULT NULL, DROP params, DROP type, DROP minSequenceLength, DROP maxSequenceLength');
#       $this->addSql('ALTER TABLE Job ADD params JSON DEFAULT NULL COMMENT \'(DC2Type:json)\', ADD type VARCHAR(255) NOT NULL, ADD minSequenceLength INT DEFAULT NULL, ADD maxSequenceLength INT DEFAULT NULL, DROP alignmentScore, DROP alignmentScoreThreshold, DROP computeNeighborhoodConnectivity, DROP fastaInput, DROP metagenomes');
