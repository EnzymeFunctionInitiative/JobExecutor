
from datetime import datetime
from enum import Flag

import sqlalchemy

from sqlalchemy import String, func
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy.types import TypeDecorator

from constants import Status

class FlagEnumType(TypeDecorator):
    """ 
    SQLAlchemy does not know how to handle python Enum/Flag values as DB column
    values. This class is developing the custom handling of a str column 
    (stored as a VARCHAR or equivalent) and an associated python Flag object.

    This is general code that works for any python Flag Enum, but is intended 
    for the Status object and the status column in the DB. 
    """
    impl = String   # DB column is implemented as a SQLAlchemy String
    cache_ok = True

    def __init__(self, enum_class, *args, **kwargs):
        self.enum_class = enum_class
        super().__init__(*args, **kwargs)

    def process_bind_param(self, value: Flag, dialect):
        """ 
        Overwrite TypeDecorator.process_bind_param() method to implement custom
        handling for this object. Documentation:
        https://docs.sqlalchemy.org/en/20/core/custom_types.html#sqlalchemy.types.TypeDecorator.process_bind_param

        This is used to convert an instance of the python Flag class (e.g. 
        Status.QUEUED) into a string that can be used in the SQL DB (e.g. 
        "queued"). 
        """
        return value.__str__()

    def process_result_value(self, value, dialect) -> Flag:
        """
        Overwrite TypeDecorator.process_result_value() method to implement 
        custom handling for this object. Documentation:
        https://docs.sqlalchemy.org/en/20/core/custom_types.html#sqlalchemy.types.TypeDecorator.process_result_value

        This is used to convert a result-row column's value to the returned 
        python type, for example a status column value of "queued" in the DB is 
        converted to Status.QUEUED.
        """
        return self.enum_class.getFlag(value)

class Base(DeclarativeBase):
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
    
    # general parameters
    job_id: Mapped[int] = mapped_column("id", primary_key=True)
    user_id: Mapped[int | None]     # mapped to user_id from the migration files but "user" in the entity files
    uuid: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False)
    #status: Mapped[Status] = mapped_column(FlagEnumType(Status), nullable=False)
    timeCreated: Mapped[datetime | None]    # should be `= mapped_column(nullable=False)`?
    timeStarted: Mapped[datetime | None]
    timeCompleted: Mapped[datetime | None]
    efi_db_version: Mapped[str | None]
    email: Mapped[str | None]
    isPublic: Mapped[bool] = mapped_column(nullable=False)
    isExample: Mapped[bool | None]   # should this be nullable?
    parentJob_id: Mapped[int | None]
    schedulerJobId: Mapped[int | None]
    jobName: Mapped[str | None]
    results: Mapped[str | None] # NOTE: gonna change?
    job_type: Mapped[str] = mapped_column(nullable=False) # used as the polymorphic_on attribute
    __mapper_args__ = {
        "polymorphic_on": "job_type",
        "polymorphic_identity": "job",
    }

    def __repr__(self):
        if self.status in Status.COMPLETED:
            completed_string = f"timeStarted='{self.timeStarted}', timeCompleted='{self.timeCompleted}'"
        elif self.status == Status.RUNNING:
            completed_string = f"timeStarted='{self.timeStarted}'"
        else:
            completed_string = ""
        return (f"<self.__class__.__name__(id={self.job_id}," 
                + f" status='{self.status}'," 
                + f" efi_type='{self.efi_type}'," 
                + f" timeCreated='{self.timeCreated}'" 
                + f" {completed_string})>")

################################################################################
# Mixin Column Classes

# columns shared across multiple mixin classes:
# - neighborhoodSize and neighborhoodWindowSize

class AlignmentScoreParameters:
    alignmentScore: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )

class BlastSequenceParameters:
    blastSequence: Mapped[str | None] = mapped_column(
        use_existing_column=True
    )

# temp name for this. match to the Trait.php file on efi-web (assuming its made)
class SequenceLengthParameters:
    minLength: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )
    maxLength: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )

class ProteinFamilyAdditionParameters:
    families: Mapped[str | None] = mapped_column(
        use_existing_column=True
    )
    sequence_version: Mapped[str | None] = mapped_column(
        use_existing_column=True
    )
    fraction: Mapped[int | None] = mapped_column(    # NOTE: should this be a float? how is this handled on the backend?
        use_existing_column=True
    )
    numUnirefClusters: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )

class DomainBoundariesParameters:
    domain: Mapped[bool | None] = mapped_column(
        use_existing_column=True
    )
    domainRegion: Mapped[str | None] = mapped_column(
        use_existing_column=True
    )

class ExcludeFragmentsParameters:
    excludeFragments: Mapped[bool | None] = mapped_column(
        use_existing_column=True
    )

class FilterByTaxonomyParameters:
    taxSearch: Mapped[str | None] = mapped_column(
        use_existing_column=True
    )
    taxSearchName: Mapped[str | None] = mapped_column(
        use_existing_column=True
    )

class FilterByFamiliesParameters:
    filterByFamilies: Mapped[str | None] = mapped_column(
        use_existing_column=True
    )

class UserUploadedIdsParameters:
    numMatchedIds: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )
    numUnmatchedIds: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )

class FilenameParameters:
    uploadedFilename: Mapped[str | None] = mapped_column(
        use_existing_column=True
    )
    jobFilename: Mapped[str | None] = mapped_column(
        use_existing_column=True
    )
    updatedAt: Mapped[datetime | None] = mapped_column(
        use_existing_column=True
    )

class SequenceDatabaseParameters:
    blastEValue: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )
    maxBlastSequences: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )
    sequenceDatabase: Mapped[str | None] = mapped_column(
        use_existing_column=True
    )

class SearchParameters:
    searchType: Mapped[str | None] = mapped_column(
        use_existing_column=True
    )

class ESTGenerateJob:
    allByAllBlastEValue: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )
    # results columns
    numFamilyOverlap: Mapped[int | None] = mapped_column( 
        use_existing_column=True
    )
    numNonFamily: Mapped[int | None] = mapped_column( 
        use_existing_column=True
    )
    numUnirefFamilyOverlap: Mapped[int | None] = mapped_column( 
        use_existing_column=True
    )
    numComputedSequences: Mapped[int | None] = mapped_column( 
        use_existing_column=True
    )
    numUniqueSequences: Mapped[int | None] = mapped_column( 
        use_existing_column=True
    )
    numBlastEdges: Mapped[int | None] = mapped_column( 
        use_existing_column=True
    )

class GNTDiagramJob:
    neighborhoodWindowSize: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )

###############################################################################
# polymorphic_identity classes

class ESTGenerateFastaJob(
        Job, 
        ProteinFamilyAdditionParameters,
        ESTGenerateJob, 
        FilterByFamiliesParameters, 
        UserUploadedIdsParameters, 
        FilenameParameters
    ):
    """
    Inherits from the ESTGenerateJob class, adds parameters from various other
    mixin classes. 
    """
    inputFasta: Mapped[str | None]
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "est_generate_fasta"
    }

class ESTGenerateFamiliesJob(
        Job, 
     sed to compute the GNNs themselves.  The window size is for how many neighbors to retrieve for GNDs.   ProteinFamilyAdditionParameters,
        ESTGenerateJob,
        DomainBoundariesParameters,
        ExcludeFragmentsParameters, 
        FilterByTaxonomyParameters
    ):
    """
    """
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "est_generate_families"
    }

class ESTGenerateBlastJob(
        Job, 
        ESTGenerateJob,
        BlastSequenceParameters,
        ExcludeFragmentsParameters, 
        FilterByTaxonomyParameters,
        ProteinFamilyAdditionParameters,
        SequenceDatabaseParameters,
    ):
    """
    """
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "est_generate_blast"
    }

class ESTGenerateAccessionJob(
        Job, 
        ESTGenerateJob,
        DomainBoundariesParameters,
        ExcludeFragmentsParameters, 
        FilenameParameters,
        FilterByFamiliesParameters, 
        FilterByTaxonomyParameters,
        UserUploadedIdsParameters, 
        ProteinFamilyAdditionParameters,
    ):
    """
    """
    domainFamily: Mapped[str | None]
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "est_generate_accession"
    }

class ESTSSNFinalizationJob(
        Job, 
        AligmentScoreParameters,
        ExcludeFragmentsParameters, 
        FilterByTaxonomyParameters,
        SequenceLengthParameters,
    ):
    """
    """
    computeNeighborhoodConnectivity: Mapped[bool | None]
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "est_ssn_finalization"
    }

class ESTNeighborhoodConnectivityJob(Job, FilenameParameters):
    """
    """
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "est_neighborhood_connectivity"
    }

class ESTConvergenceRatioJob(
        Job, 
        AlignmentScoreParameters, 
        FilenameParameters
    ):
    """
    """
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "est_convergence_ratio"
    }

class ESTClusterAnalysisJob(Job, FilenameParameters):
    """
    """
    minSeqMSA: Mapped[int | None]
    maxSeqMSA: Mapped[int | None]
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "est_cluster_analysis"
    }

class ESTColorSSNJob(Job, FilenameParameters):
    """
    """
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "est_color_ssn"
    }

class GNTGNNJob(Job, GNTDiagramJob, FilenameParameters):
    """
    """
    cooccurrence: Mapped[float | None]
    neighborhood_size: Mapped[int | None]   # = mapped_column(
    #    use_existing_column=True
    #)
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "gnt_gnn"
    }

class GNTDiagramBlastJob(
        Job, 
        GNTDiagramJob,
        BlastSequenceParameters,
        ExcludeFragmentsParameters,
        SequenceDatabaseParameters,
    ):
    """
    """
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "gnt_diagram_blast"
    }

class GNTDiagramFastaJob(Job, GNTDiagramJob, FilenameParameters):
    """
    """
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "gnt_diagram_fasta"
    }

class GNTDiagramSequenceIdJob(
        Job, 
        GNTDiagramJob,
        ExcludeFragmentsParameters,
        FilenameParameters,
        SequenceDatabaseParameters
    ):
    """
    """
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "gnt_diagram_sequence_id"
    }

class GNTViewDiagramJob(Job, FilenameParameters):
    """
    """
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "gnt_view_diagram"
    }

class CGFPIdentifyJob(
        Job, 
        FilenameParameters,
        SearchParmeters,
        SequenceLengthParameters,
    ):
    """
    """
    referenceDatabase: Mapped[str | None]
    cdhitSequenceIdentity: Mapped[int | None]      # NOTE: should be a double?
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "cgfp_identify"
    }

class CGFPQuantifyJob(Job,SearchParmeters):
        
    """
    """
    metagenomes: Mapped[str | None]
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "cgfp_quantify"
    }

class TaxonomyAccessionJob(
        Job,
        ExcludeFragmentsParameters, 
        FilterByFamiliesParameters, 
        FilterByTaxonomyParameters,
        FilenameParameters, 
        SequenceDatabaseParameters
    ):  
    """
    """
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "taxonomy_accession"
    }

class TaxonomyFamiliesJob(
        Job,
        ExcludeFragmentsParameters, 
        FilterByFamiliesParameters, 
        FilterByTaxonomyParameters,
        SequenceLengthParameters,
    ):
    """
    """
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "taxonomy_families"
    }

class TaxonomyFastaJob(
        Job,
        ExcludeFragmentsParameters, 
        FilterByFamiliesParameters, 
        FilterByTaxonomyParameters,
        FilenameParameters
    ):
    """
    """
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "taxonomy_fasta"
    }

################################################################################

