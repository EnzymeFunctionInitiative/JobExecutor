
from datetime import datetime
from enum import Enum

import sqlalchemy

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy.types import TypeDecorator

from constants import Status

# NOTE: generalize this to non-Status enums too
class FlagEnumType(TypeDecorator):
    """ 
    SQLAlchemy does not know how to handle python Enum/Flag values as DB column
    values. This class is developing the custom handling of a str column 
    (stored as a VARCHAR or equivalent) and an associated python Flag object.

    This is general code that works for any python Flag Enum, but is intended 
    for the Status object and the status column in the DB. 
    """
    impl = str   # DB column is implemented as a SQLAlchemy str 
    cache_ok = True

    def __init__(self, enum_class, *args, **kwargs):
        self.enum_class = enum_class
        super().__init__(*args, **kwargs)

    # NOTE: generalize this to non-Status enums too
    def process_bind_param(self, value, dialect):
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
        python type, for example a status column value of "queued" in the DB is 
        converted to Status.QUEUED.
        """
        if value is None:
            return None
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
    # placeholder columns
    jobName: Mapped[str | None]      # in symfony, this is associated with ESTGenerateJob
    results: Mapped[str | None] # NOTE: gonna change
   
    job_type: Mapped[str] = mapped_column(nullable=False) # used as the polymorphic_on attribute
    __mapper_args__ = {
        "polymorphic_on": "job_type",
        "polymorphic_identity": "job",
    }

    #def __repr__(self):
    #    if self.status in Status.COMPLETED:
    #        completed_string = f"timeStarted='{self.timeStarted}', timeCompleted='{self.timeCompleted}'"
    #    elif self.status == Status.RUNNING:
    #        completed_string = f"timeStarted='{self.timeStarted}'"
    #    else:
    #        completed_string = ""
    #    return (f"<self.__class__.__name__(id={self.job_id}," 
    #            + f" status='{self.status}'," 
    #            + f" efi_type='{self.efi_type}'," 
    #            + f" timeCreated='{self.timeCreated}'" 
    #            + f" {completed_string})>")

################################################################################
# Mixin Column Classes

class ProteinFamilyAdditionParameters:
    families: Mapped[str | None] = mapped_column(
        use_existing_column=True
    )
    sequence_version: Mapped[str | None] = mapped_column(    # NOTE: should this be an enum uniprot, uniref50, uniref90? Is this redundant with blastDatabase?
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
    domainRegion: Mapped[str | None] = mapped_column(         # NOTE: should be an enum of "n-terminal", "c-terminal", "central", or "domain"?
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

class SequenceDatabaseParameters:
    sequenceDatabase: Mapped[str | None] = mapped_column(
        use_existing_column=True
    )
    exclude_fragments: Mapped[bool | None] = mapped_column(
        use_existing_column=True
    )

#class ESTGenerateJob(Job, ProteinFamilyAdditionParameters):
class ESTGenerateJob:
    """
    Inherits from Job class, adds ProteinFamilyAdditionParameters since any 
    EST input path can use those fields. Does not get polymorph'd on.
    """
    allByAllBlastEValue: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )
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
    
    #__mapper_args__ = {
    #    'polymorphic_abstract=True'
    #}

#class GNTDiagramJob(Job):
class GNTDiagramJob:
    """
    Inherits from Job class, used as parent class to GNTDiagramBlast, 
    GNTDiagramFasta, and GNTDiagramSequenceId. Does not get polymorph'd on.
    """
    neighborhood_size: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )
    #__mapper_args__ = {
    #    'polymorphic_abstract=True'
    #}

#class TaxonomyJob(
#        Job,
#        ExcludeFragmentsParameters, 
#        FilterByFamiliesParameters, 
#        FilterByTaxonomyParameters,
#    ):
#    """
#    """
#    __mapper_args__ = {
#        'polymorphic_abstract=True'
#    }

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
        ProteinFamilyAdditionParameters,
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
        ProteinFamilyAdditionParameters,
        ESTGenerateJob,
        ExcludeFragmentsParameters, 
        FilterByTaxonomyParameters,
    ):
    """
    """
    blastQuery: Mapped[str | None]
    blastMaxSequences: Mapped[int | None]
    blastDatabase: Mapped[str | None]        # NOTE: str of uniprot, uniref50, uniref90. should it be an enum? 
    blastEValue: Mapped[int | None]         # NOTE: should be a double OR a string of the input floating point value to avoid number representation concerns
    numBlastSeqRetr: Mapped[int | None]
    # NOTE:
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "est_generate_blast"
    }

class ESTGenerateAccessionJob(
        Job, 
        ProteinFamilyAdditionParameters,
        ESTGenerateJob,
        DomainBoundariesParameters,
        ExcludeFragmentsParameters, 
        FilterByFamiliesParameters, 
        FilterByTaxonomyParameters,
        FilenameParameters,
        UserUploadedIdsParameters, 
    ):
    """
    """
    accessionIds: Mapped[str | None] = mapped_column(
        use_existing_column=True
    )
    domainFamily: Mapped[str | None]
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "est_generate_accession"
    }

class ESTSSNFinalizationJob(
        Job, 
        ExcludeFragmentsParameters, 
        FilterByTaxonomyParameters,
    ):
    """
    """
    alignmentScoreThreshold: Mapped[float | None]
    minLength: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )
    maxLength: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )
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

class ESTConvergenceRatioJob(Job, FilenameParameters):
    """
    """
    alignmentScore: Mapped[float | None]    # potentially redundant with alignmentScoreThreshold?
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

class GNTGNNJob(Job, FilenameParameters):
    """
    """
    cooccurrence: Mapped[float | None]
    neighborhood_size: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "gnt_gnn"
    }

class GNTDiagramSequenceIdJob(Job, GNTDiagramJob, SequenceDatabaseParameters):
    """
    """
    accessionIds: Mapped[str | None] = mapped_column(
        use_existing_column=True    # NOTE: reused from ESTGenerateAccessionJob
    )
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "gnt_diagram_sequence_id"
    }

class GNTDiagramFastaJob(Job, GNTDiagramJob):
    """
    """
    fastaInput: Mapped[str | None] = mapped_column(
        use_existing_column=True
    )
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "gnt_diagram_fasta"
    }

class GNTDiagramBlastJob(Job, GNTDiagramJob, SequenceDatabaseParameters):
    """
    """
    maxBlastSequences: Mapped[int | None]
    blastSequence: Mapped[float | None]      # NOTE: is this really the sequence string or a file path where that sequence is written to
    eValue: Mapped[int | None]     # NOTE: should be a Double? should be redundant with some other column?
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "gnt_diagram_blast"
    }

class GNTViewDiagramJob(Job, FilenameParameters):
    """
    """
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "gnt_view_diagram"
    }

class CGFPIdentifyJob(Job, FilenameParameters):
    """
    """
    referenceDatabase: Mapped[str | None]
    cdhitSequenceIdentity: Mapped[int | None]      # NOTE: should be a double?
    searchType: Mapped[str | None] = mapped_column(
        use_existing_column=True
    )
    minLength: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )
    maxLength: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "cgfp_identify"
    }

class CGFPQuantifyJob(Job):
    """
    """
    metagenomes: Mapped[str | None]
    searchType: Mapped[str | None] = mapped_column(
        use_existing_column=True
    )
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
    accessionIds: Mapped[str | None] = mapped_column(
        use_existing_column=True    # NOTE: reused from ESTGenerateAccessionJob
    )
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "taxonomy_accession"
    }

class TaxonomyFamiliesJob(
        Job,
        ExcludeFragmentsParameters, 
        FilterByFamiliesParameters, 
        FilterByTaxonomyParameters,
    ):
    """
    """
    minLength: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )
    maxLength: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )
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
    fastaInput: Mapped[str | None] = mapped_column(
        use_existing_column=True
    )
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "taxonomy_fasta"
    }

################################################################################

"""
QUESTIONS/STATEMENTS: 
 ' id INT AUTO_INCREMENT NOT NULL",                     # moved to "job_id" attribute in 

 ' user_id INT DEFAULT NULL',                           # why is this nullable?
 " uuid CHAR(36) NOT NULL COMMENT '(DC2Type:guid)'",    # why is this not nullable but user_id is?
 ' timeCreated DATETIME DEFAULT NULL',                  # why is this nullable? the fact the job is in the table means its been created?
 ' efi_db_version VARCHAR(255) DEFAULT NULL',           # why is this nullable? 

 ' inputFasta LONGTEXT DEFAULT NULL',                   # I don't think LONGTEXT should be here; theres no reason to allow users to input up to 4GB worth of fasta file into the job table. This needs to map to a file path whether they input their fasta file in the textbox or upload it. So users can put a huge string into the text box but it all gets written to file, whose path is input to this field 
 ' blastSequence LONGTEXT DEFAULT NULL',
 ' metagenomes LONGTEXT DEFAULT NULL',                  # I don't think LONGTEXT should be here; theres no reason to allow users to input up to 4GB worth of fasta file into the job table. This needs to map to a file path whether they input their fasta file in the textbox or upload it. So users can put a huge string into the text box but it all gets written to file, whose path is input to this field 

 ' allByAllBlastEValue INT DEFAULT NULL',               # just fix the UI...
 ' eValue INT DEFAULT NULL',        # just fix the UI...
 ' fraction INT DEFAULT NULL',      # should this be an INT? just update the UI to make the value more clear
 ' alignmentScore DOUBLE PRECISION DEFAULT NULL",       # stash doubles as strings instead? 
 
 ' excludeFragments TINYINT(1) DEFAULT NULL',
 ' exclude_fragments TINYINT(1) DEFAULT NULL',          # entity files SequenceDatabaseTrait.php and ExcludeFragmentsTrait.php both contain references to an excludeFragments column... is this redundant with that column? or are two instances of the column needed? 
 

"""

"""
$this->addSql('CREATE TABLE Job (
    
    # Job
    id INT AUTO_INCREMENT NOT NULL,
    user_id INT DEFAULT NULL,
    uuid CHAR(36) NOT NULL,
    status VARCHAR(255) NOT NULL,
	timeCreated DATETIME DEFAULT NULL,
	timeStarted DATETIME DEFAULT NULL,
	timeCompleted DATETIME DEFAULT NULL,
	efi_db_version VARCHAR(255) DEFAULT NULL,
	email VARCHAR(255) DEFAULT NULL,
	isPublic TINYINT(1) NOT NULL,
	isExample TINYINT(1) DEFAULT NULL,
	parentJob_id INT DEFAULT NULL,
	jobName VARCHAR(255) DEFAULT NULL,  # should not be here?
	results JSON DEFAULT NULL,
	job_type VARCHAR(255) NOT NULL,     # polymorph'd on
	
    # ProteinFamilyAdditionTrait
	families TEXT DEFAULT NULL,
	sequence_version VARCHAR(255) DEFAULT NULL,
	fraction INT DEFAULT NULL,
    numUnirefClusters INT DEFAULT NULL,
    
    # DomainBoundariesTrait
	domain TINYINT(1) DEFAULT NULL,
	domainRegion VARCHAR(255) DEFAULT NULL,

    # ExcludeFragmentsTrait
	excludeFragments TINYINT(1) DEFAULT NULL,

    # FilterByTaxonomyTrait
	taxSearch VARCHAR(255) DEFAULT NULL,
	taxSearchName VARCHAR(255) DEFAULT NULL,

    # FilterByFamiliesTrait
	filterByFamilies VARCHAR(255) DEFAULT NULL,
   
    # UserUploadedIdsTrait
	numMatchedIds INT DEFAULT NULL,
	numUnmatchedIds INT DEFAULT NULL,

    # FilenameTrait
	uploadedFilename VARCHAR(255) DEFAULT NULL,

    # SequenceDatabaseTrait
	sequenceDatabase VARCHAR(255) DEFAULT NULL,
	exclude_fragments TINYINT(1) DEFAULT NULL,  # redundant with excludeFragments

    # ESTGenerateJob
	allByAllBlastEValue INT DEFAULT NULL,
    numFamilyOverlap INT DEFAULT NULL,
	numNonFamily INT DEFAULT NULL,
	numUnirefFamilyOverlap INT DEFAULT NULL,
	numComputedSequences INT DEFAULT NULL,
	numUniqueSequences INT DEFAULT NULL,
	numBlastEdges INT DEFAULT NULL,

    # ESTGenerateFastaJob
	inputFasta LONGTEXT DEFAULT NULL,   !!!

    # ESTGenerateBlastJob
    blastQuery TEXT DEFAULT NULL,
	blastMaxSequences INT DEFAULT NULL,
	blastDatabase VARCHAR(255) DEFAULT NULL,
	blastEValue INT DEFAULT NULL,
	numBlastSeqRetr INT DEFAULT NULL,

    # ESTGenerateAccessionJob
	accessionIds VARCHAR(255) DEFAULT NULL,
	domainFamily VARCHAR(255) DEFAULT NULL,

    # ESTSSNFinalizationJob
	alignmentScoreThreshold DOUBLE PRECISION DEFAULT NULL,
	minLength INT DEFAULT NULL,
	maxLength INT DEFAULT NULL,
	computeNeighborhoodConnectivity TINYINT(1) DEFAULT NULL,

    # ESTNeighborhoodConnectivityJob

    # ESTConvergenceRatioJob
    alignmentScore DOUBLE PRECISION DEFAULT NULL,   # potentially redundant with alignmentScoreThreshold?

    # ESTClusterAnalysisJob
	minSeqMSA INT DEFAULT NULL,
	maxSeqMSA INT DEFAULT NULL,

    # ESTColorSSNJob

    # GNTGNNJob
	cooccurrence DOUBLE PRECISION DEFAULT NULL,
	neighborhood_size INT DEFAULT NULL,

    # GNTDiagramJob

    # GNTDiagramSequenceIdJob

    # GNTDiagramFastaJob
	fastaInput VARCHAR(255) DEFAULT NULL,   # shouldn't this be redundant with uploadedFilename?

    # GNTDiagramBlastJob
	maxBlastSequences INT DEFAULT NULL,
	blastSequence LONGTEXT DEFAULT NULL,    # should not be LongText
	eValue INT DEFAULT NULL,                # can this be made redundant with some other E-value column?

    # GNTViewDiagramJob

    # CGFPIdentifyJob
	referenceDatabase VARCHAR(255) DEFAULT NULL,
	cdhitSequenceIdentity INT DEFAULT NULL,
	searchType VARCHAR(255) DEFAULT NULL,
	minLength INT DEFAULT NULL,
	maxLength INT DEFAULT NULL,

    # CGFPQuantifyJob
	metagenomes LONGTEXT DEFAULT NULL,  # !!!
	searchType VARCHAR(255) DEFAULT NULL,



	INDEX IDX_C395A618A76ED395 (user_id),
	INDEX IDX_C395A6184A4533A0 (parentJob_id),
	PRIMARY KEY(id)) DEFAULT CHARACTER SET utf8mb4 COLLATE `utf8mb4_unicode_ci` ENGINE = InnoDB');
$this->addSql('ALTER TABLE Job ADD CONSTRAINT FK_C395A618A76ED395 FOREIGN KEY (user_id) REFERENCES users (id)');
$this->addSql('ALTER TABLE Job ADD CONSTRAINT FK_C395A6184A4533A0 FOREIGN KEY (parentJob_id) REFERENCES Job (id)');

"""









