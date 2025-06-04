
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
    SQLAlchemy model for the EFI-Web 'Job' table. 
    """
    __tablename__ = 'Job'

    # SQLalchemy ORM 2.0x notes: PEP484 type annotations used with `Mapped`
    # enables skipping the `mapped_column()` call. The `Mapped` annotation can
    # be used to set datatype _and_ nullability for the column. Default for 
    # nullable is True for non-primary key columns.
    job_id: Mapped[int] = mapped_column("id", primary_key=True)
    uuid: Mapped[str] = mapped_column(nullable=False)
    user: Mapped[int] = mapped_column("user_id")    # , nullable=False
    status: Mapped[Status] = mapped_column(FlagEnumType(Status), nullable=False)
    timeCreated: Mapped[datetime | None] = mapped_column(
        server_default=func.now()   # NOTE: do I need this???
    )
    timeStarted: Mapped[datetime | None]
    timeCompleted: Mapped[datetime | None]
    efi_db_version: Mapped[str | None]
    email: Mapped[str | None]
    isPublic: Mapped[int] = mapped_column(nullable=False)   # NOTE: Should be boolean?
    parentJob_id: Mapped[int | None]
    job_type: Mapped[str] = mapped_column(nullable=False)   # NOTE: change this to an enum
    
    results: Mapped[str | None] # NOTE: gonna change?
   
    ### input parameter columns
    # ESTGenerateJob; EST-general parameters
    allByAllBlastEValue: Mapped[int | None]    # NOTE: should be a double
    jobName: Mapped[str | None]     # NOTE: why is this specific to EST? Shouldn't GNT also have a jobName column?

    # ESTGenerateBlastJob; blast input path
    blastQuery: Mapped[str | None]
    blastMaxSequences: Mapped[int | None]
    blastDatabase: Mapped[str | None]   # str of uniprot, uniref50, uniref90. should it be an enum? 
    blastEValue: Mapped[int | None]     # NOTE: should be a Double?
   
    # ESTGenerateFastaJob; fasta input path
    inputFasta: Mapped[str | None]      # is this a file path or the actual full fasta file contents stored in the table?

    # ESTGenerateAccessionJob; accession IDs input path
    accessionIds: Mapped[str | None]
    domainFamily: Mapped[str | None]

    # ExcludeFragmentsTrait; fragment filtering parameters
    excludeFragments: Mapped[int | None]    # NOTE: should this be a boolean?

    # ProteinFamilyAdditionTrait; adding families to whatever job; covers the families 
    families: Mapped[str | None]
    sequence_version: Mapped[str | None]    # NOTE: should this be an enum uniprot, uniref50, uniref90?
    fraction: Mapped[int | None]    # NOTE: should this be a float? how is this handled on the backend?

    # FilterByTaxonomyTrait
    taxSearch: Mapped[str | None]
    taxSearchName: Mapped[str | None]

    # DomainBoundariesTrait; domain filtering parameters
    domain: Mapped[int | None]
    domainRegion: Mapped[str | None]    # NOTE: should be an enum of "n-terminal", "c-terminal", "central", or "domain"

    # FilterByFamiliesTrait; Families input path and filtering parameters
    filterByFamilies: Mapped[str | None]
    
    # FilenameTrait; no idea what this is used for...
    filename: Mapped[str | None] # NOTE: !!! very ambiguous column name...

    # ESTClusterAnalysisJob; 
    minSeqMSA: Mapped[int | None]
    maxSeqMSA: Mapped[int | None]

    # ESTConvergenceRatioJob; 
    alignmentScore: Mapped[float | None]

    # ESTSSNFinalizationJob;
    alignmentScoreThreshold: Mapped[float | None]
    minLength: Mapped[int | None]
    maxLength: Mapped[int | None]
    computeNeighborhoodConnectivity: Mapped[int | None]     # NOTE: should this be a boolean?

    # GNTGNNJob; 
    cooccurrence: Mapped[float | None]
    neighborhood_size: Mapped[int | None]

    # GNTDiagramBlastJob; 
    maxBlastSequences: Mapped[int | None]
    blastSequence: Mapped[str | None]      # NOTE: is this really the sequence string or a file path where that sequence is written to
    eValue: Mapped[int | None]     # NOTE: should be a Double?

    # GNTDiagramFastaJob; 
    fastaInput: Mapped[str | None]

    # GNTDiagramSequenceIdJob;
    #accessionIds: Mapped[str | None] # NOTE: reused from ESTGenerateAccessionJob 

    # CGFPIdentifyJob; 
    referenceDatabase: Mapped[str | None]
    cdhitSequenceIdentity: Mapped[int | None]      # NOTE: should be a double?
    searchType: Mapped[str | None]
    #minLength: Mapped[int | None]  # NOTE: reused from ESTSSNFinalizationJob
    #maxLength: Mapped[int | None]  # NOTE: reused from ESTSSNFinalizationJob

    # CGFPQuantifyJob; 
    metagenomes: Mapped[str | None]     # NOTE: what is this supposed to be used for? should it be a filepath
    #searchType: Mapped[str | None]      # NOTE: reused for CGFPIdentifyJob

    # SequenceDatabaseTrait; 
    sequenceDatabase: Mapped[str | None]
    exclude_fragments: Mapped[int | None]   # redundant with the excludeFragments column?


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

