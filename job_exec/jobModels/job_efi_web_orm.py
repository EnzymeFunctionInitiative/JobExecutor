
from datetime import datetime
from enum import Flag
import json

from typing import ClassVar

import sqlalchemy

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped

from constants import Status
from jobModels.flag_enum_type import FlagEnumType

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

    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s)
    _parameter_attrs: ClassVar[set[str]] = {
        "job_id",
        "jobName",
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

    def get_parameters_dict(self) -> Dict[str, Any]:
        """
        Create a dictionary of attributes that should be written to a
        params.yaml file.
        """
        return {key: getattr(self, key) for key in self._parameter_attrs}

################################################################################
# Mixin Column Classes

# columns shared across multiple mixin classes:
# - neighborhoodSize and neighborhoodWindowSize

class AlignmentScoreParameters:
    alignmentScore: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s)
    _parameter_attrs: ClassVar[set[str]] = {"alignmentScore"}

class BlastSequenceParameters:
    blastSequence: Mapped[str | None] = mapped_column(
        use_existing_column=True
    )
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s)
    _parameter_attrs: ClassVar[set[str]] = {"blastSequence"}

# temp name for this. match to the Trait.php file on efi-web (assuming its made)
class SequenceLengthParameters:
    minLength: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )
    maxLength: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s)
    _parameter_attrs: ClassVar[set[str]] = {"minLength", "maxLength"}

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
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s)
    _parameter_attrs: ClassVar[set[str]] = {
        "families",
        "sequence_version",
        "fraction",
        "numUnirefClusters"
    }

class DomainBoundariesParameters:
    domain: Mapped[bool | None] = mapped_column(
        use_existing_column=True
    )
    domainRegion: Mapped[str | None] = mapped_column(
        use_existing_column=True
    )
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s)
    _parameter_attrs: ClassVar[set[str]] = {"domain", "domainRegion"}

class ExcludeFragmentsParameters:
    excludeFragments: Mapped[bool | None] = mapped_column(
        use_existing_column=True
    )
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s)
    _parameter_attrs: ClassVar[set[str]] = {"excludeFragments"}

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
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s)
    _parameter_attrs: ClassVar[set[str]] = {"filterByFamilies"}

class UserUploadedIdsParameters:
    # NOTE: these are results parameters?
    numMatchedIds: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )
    numUnmatchedIds: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )
    ## assign a class variable to contain parameters that have relevance to the
    ## nextflow pipeline(s)
    #_parameter_attrs: ClassVar[set[str]] = {"numMatchedIds", "numUnmatchedIds"}

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
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s)
    _parameter_attrs: ClassVar[set[str]] = {
        "uploadedFilename",
        "jobFilename",
        "updatedAt"
    }

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
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s)
    _parameter_attrs: ClassVar[set[str]] = {
        "blastEValue",
        "maxBlastSequences",
        "sequenceDatabase"
    }

class SearchParameters:
    searchType: Mapped[str | None] = mapped_column(
        use_existing_column=True
    )
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s)
    _parameter_attrs: ClassVar[set[str]] = {"searchType"}

class ESTGenerateJob:
    allByAllBlastEValue: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )
    # results columns, not important parameters for nextflow pipelines
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
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s)
    _parameter_attrs: ClassVar[set[str]] = {"allByAllBlastEValue"}

class GNTDiagramJob:
    neighborhoodWindowSize: Mapped[int | None] = mapped_column(
        use_existing_column=True
    )
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s)
    _parameter_attrs: ClassVar[set[str]] = {"neighborhoodWindowSize"}

###############################################################################
# polymorphic_identity classes

class ESTGenerateFastaJob(
        Job,
        ESTGenerateJob,
        FilenameParameters
        FilterByFamiliesParameters,
        ProteinFamilyAdditionParameters,
        UserUploadedIdsParameters,
    ):
    """
    """
    inputFasta: Mapped[str | None]
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "est_generate_fasta"
    }
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s); gathers all mixin classes' parameters too
    _parameter_attrs: ClassVar[set[str]] = Job._parameter_attrs.union(
        ESTGenerateJob._parameter_attrs,
        FilenameParameters._parameter_attrs
        FilterByFamiliesParameters._parameter_attrs,
        ProteinFamilyAdditionParameters._parameter_attrs,
        UserUploadedIdsParameters._parameter_attrs,
        {"inputFasta"}
    )

class ESTGenerateFamiliesJob(
        Job,
        ESTGenerateJob,
        DomainBoundariesParameters,
        ExcludeFragmentsParameters,
        FilterByTaxonomyParameters,
        ProteinFamilyAdditionParameters,
    ):
    """
    """
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "est_generate_families"
    }
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s); gathers all mixin classes' parameters too
    _parameter_attrs: ClassVar[set[str]] = Job._parameter_attrs.union(
        ESTGenerateJob._parameter_attrs,
        DomainBoundariesParameters._parameter_attrs,
        ExcludeFragmentsParameters._parameter_attrs,
        FilterByTaxonomyParameters._parameter_attrs,
        ProteinFamilyAdditionParameters._parameter_attrs,
    )

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
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s); gathers all mixin classes' parameters too
    _parameter_attrs: ClassVar[set[str]] = Job._parameter_attrs.union(
        ESTGenerateJob._parameter_attrs,
        BlastSequenceParameters._parameter_attrs,
        ExcludeFragmentsParameters._parameter_attrs,
        FilterByTaxonomyParameters._parameter_attrs,
        ProteinFamilyAdditionParameters._parameter_attrs,
        SequenceDatabaseParameters._parameter_attrs,
    )

class ESTGenerateAccessionJob(
        Job,
        ESTGenerateJob,
        DomainBoundariesParameters,
        ExcludeFragmentsParameters,
        FilenameParameters,
        FilterByFamiliesParameters,
        FilterByTaxonomyParameters,
        ProteinFamilyAdditionParameters,
        UserUploadedIdsParameters,
    ):
    """
    """
    domainFamily: Mapped[str | None]
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "est_generate_accession"
    }
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s); gathers all mixin classes' parameters too
    _parameter_attrs: ClassVar[set[str]] = Job._parameter_attrs.union(
        ESTGenerateJob._parameter_attrs,
        DomainBoundariesParameters._parameter_attrs,
        ExcludeFragmentsParameters._parameter_attrs,
        FilenameParameters._parameter_attrs,
        FilterByFamiliesParameters._parameter_attrs,
        FilterByTaxonomyParameters._parameter_attrs,
        ProteinFamilyAdditionParameters._parameter_attrs,
        UserUploadedIdsParameters._parameter_attrs,
    )

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
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s); gathers all mixin classes' parameters too
    _parameter_attrs: ClassVar[set[str]] = Job._parameter_attrs.union(
        AligmentScoreParameters._parameter_attrs,
        ExcludeFragmentsParameters._parameter_attrs,
        FilterByTaxonomyParameters._parameter_attrs,
        SequenceLengthParameters._parameter_attrs,
        {"computeNeighborhoodConnectivity"}
    }

class ESTNeighborhoodConnectivityJob(Job, FilenameParameters):
    """
    """
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "est_neighborhood_connectivity"
    }
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s); gathers all mixin classes' parameters too
    _parameter_attrs: ClassVar[set[str]] = Job._parameter_attrs.union(
        FilenameParameters._parameter_attrs,
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
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s); gathers all mixin classes' parameters too
    _parameter_attrs: ClassVar[set[str]] = Job._parameter_attrs.union(
        AlignmentScoreParameters._parameter_attrs,
        FilenameParameters._parameter_attrs,
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
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s); gathers all mixin classes' parameters too
    _parameter_attrs: ClassVar[set[str]] = Job._parameter_attrs.union(
        FilenameParameters._parameter_attrs,
        {"minSeqMSA","maxSeqMSA"}
    }

class ESTColorSSNJob(Job, FilenameParameters):
    """
    """
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "est_color_ssn"
    }
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s); gathers all mixin classes' parameters too
    _parameter_attrs: ClassVar[set[str]] = Job._parameter_attrs.union(
        FilenameParameters._parameter_attrs,
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
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s); gathers all mixin classes' parameters too
    _parameter_attrs: ClassVar[set[str]] = Job._parameter_attrs.union(
        GNTDiagramJob._parameter_attrs,
        FilenameParameters._parameter_attrs,
        {"cooccurrence","neighborhood_size"}
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
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s); gathers all mixin classes' parameters too
    _parameter_attrs: ClassVar[set[str]] = Job._parameter_attrs.union(
        GNTDiagramJob._parameter_attrs,
        BlastSequenceParameters._parameter_attrs,
        ExcludeFragmentsParameters._parameter_attrs,
        SequenceDatabaseParameters._parameter_attrs,
    }

class GNTDiagramFastaJob(Job, GNTDiagramJob, FilenameParameters):
    """
    """
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "gnt_diagram_fasta"
    }
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s); gathers all mixin classes' parameters too
    _parameter_attrs: ClassVar[set[str]] = Job._parameter_attrs.union(
        GNTDiagramJob._parameter_attrs,
        FilenameParameters._parameter_attrs,
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
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s); gathers all mixin classes' parameters too
    _parameter_attrs: ClassVar[set[str]] = Job._parameter_attrs.union(
        GNTDiagramJob._parameter_attrs,
        ExcludeFragmentsParameters._parameter_attrs,
        FilenameParameters._parameter_attrs,
        SequenceDatabaseParameters._parameter_attrs,
    }

class GNTViewDiagramJob(Job, FilenameParameters):
    """
    """
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "gnt_view_diagram"
    }
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s); gathers all mixin classes' parameters too
    _parameter_attrs: ClassVar[set[str]] = Job._parameter_attrs.union(
        FilenameParameters._parameter_attrs,
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
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s); gathers all mixin classes' parameters too
    _parameter_attrs: ClassVar[set[str]] = Job._parameter_attrs.union(
        FilenameParameters._parameter_attrs,
        SearchParmeters._parameter_attrs,
        SequenceLengthParameters._parameter_attrs,
        {"referenceDatabase","cdhitSequenceIdentity"}
    }

class CGFPQuantifyJob(Job,SearchParmeters):
    """
    """
    metagenomes: Mapped[str | None]
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "cgfp_quantify"
    }
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s); gathers all mixin classes' parameters too
    _parameter_attrs: ClassVar[set[str]] = Job._parameter_attrs.union(
        SearchParmeters._parameter_attrs,
        {"metagenomes"}
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
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s); gathers all mixin classes' parameters too
    _parameter_attrs: ClassVar[set[str]] = Job._parameter_attrs.union(
        ExcludeFragmentsParameters._parameter_attrs,
        FilterByFamiliesParameters._parameter_attrs,
        FilterByTaxonomyParameters._parameter_attrs,
        FilenameParameters._parameter_attrs,
        SequenceDatabaseParameters._parameter_attrs,
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
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s); gathers all mixin classes' parameters too
    _parameter_attrs: ClassVar[set[str]] = Job._parameter_attrs.union(
        ExcludeFragmentsParameters._parameter_attrs,
        FilterByFamiliesParameters._parameter_attrs,
        FilterByTaxonomyParameters._parameter_attrs,
        SequenceLengthParameters._parameter_attrs,
    }

class TaxonomyFastaJob(
        Job,
        ExcludeFragmentsParameters,
        FilenameParameters,
        FilterByFamiliesParameters,
        FilterByTaxonomyParameters,
    ):
    """
    """
    __mapper_args__ = {
        "polymorphic_load": "selectin",
        "polymorphic_identity": "taxonomy_fasta"
    }
    # assign a class variable to contain parameters that have relevance to the
    # nextflow pipeline(s); gathers all mixin classes' parameters too
    _parameter_attrs: ClassVar[set[str]] = Job._parameter_attrs.union(
        ExcludeFragmentsParameters._parameter_attrs,
        FilenameParameters._parameter_attrs,
        FilterByFamiliesParameters._parameter_attrs,
        FilterByTaxonomyParameters._parameter_attrs,
    }

################################################################################

