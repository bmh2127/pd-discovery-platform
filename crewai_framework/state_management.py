# state_management.py
"""
State management for PD Discovery Platform - Systematic Parkinson's Disease Research
Comprehensive Pydantic v2 models for managing paradigm-challenging research workflow state
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationInfo
from datetime import datetime
from enum import Enum

# ================================
# ENUMS FOR STANDARDIZED VALUES
# ================================

class DiscoveryMode(str, Enum):
    """Network discovery modes"""
    MINIMAL = "minimal"
    STANDARD = "standard" 
    COMPREHENSIVE = "comprehensive"
    HYPOTHESIS_FREE = "hypothesis_free"

class ConfidenceLevel(str, Enum):
    """Research confidence levels"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"

class ParadigmChallengeStrength(str, Enum):
    """Strength of paradigm challenge evidence"""
    INSUFFICIENT = "insufficient"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    COMPELLING = "compelling"

class ResearchPriority(str, Enum):
    """Research priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ValidationStatus(str, Enum):
    """Validation status for research findings"""
    PENDING = "pending"
    VALIDATED = "validated"
    FAILED = "failed"
    REQUIRES_RETRY = "requires_retry"

# ================================
# CORE DATA MODELS
# ================================

class ProteinEntity(BaseModel):
    """Individual protein entity with standardized identifiers"""
    gene_symbol: str = Field(description="Canonical gene symbol (e.g., SNCA, PRKN)")
    protein_name: str = Field(description="Full protein name")
    uniprot_id: Optional[str] = Field(description="UniProt identifier", default=None)
    ensembl_id: Optional[str] = Field(description="Ensembl gene identifier", default=None)
    aliases: List[str] = Field(description="Alternative gene symbols", default_factory=list)
    confidence_score: float = Field(description="Entity resolution confidence", ge=0.0, le=1.0, default=1.0)

class ProteinInteraction(BaseModel):
    """Protein-protein interaction with evidence"""
    source_protein: str = Field(description="Source protein gene symbol")
    target_protein: str = Field(description="Target protein gene symbol")
    interaction_type: str = Field(description="Type of interaction (physical, functional, etc.)")
    confidence_score: float = Field(description="Interaction confidence", ge=0.0, le=1.0)
    evidence_sources: List[str] = Field(description="Databases supporting interaction", default_factory=list)
    paradigm_relevance: bool = Field(description="Relevant to paradigm challenge", default=False)
    pathology_synthesis_connection: bool = Field(description="Direct pathology-synthesis connection", default=False)

class FunctionalCluster(BaseModel):
    """Functional protein cluster analysis"""
    cluster_name: str = Field(description="Cluster identifier (e.g., synthesis, pathology)")
    proteins: List[str] = Field(description="Proteins in cluster")
    cluster_type: str = Field(description="Type of functional cluster")
    connectivity_score: float = Field(description="Internal connectivity strength", ge=0.0, le=1.0)
    external_connections: Dict[str, int] = Field(description="Connections to other clusters", default_factory=dict)

class HubProtein(BaseModel):
    """Hub protein with connectivity analysis"""
    protein: str = Field(description="Protein gene symbol")
    connections: int = Field(description="Number of connections", ge=0)
    betweenness_centrality: float = Field(description="Network centrality measure", ge=0.0, default=0.0)
    paradigm_importance: float = Field(description="Importance for paradigm challenge", ge=0.0, le=1.0, default=0.0)
    novel_discovery: bool = Field(description="Previously unknown hub status", default=False)

class NovelConnection(BaseModel):
    """Novel or unexpected protein connection"""
    interaction: ProteinInteraction
    novelty_score: float = Field(description="How unexpected this connection is", ge=0.0, le=1.0)
    paradigm_challenge_potential: float = Field(description="Potential to challenge paradigms", ge=0.0, le=1.0)
    experimental_validation_priority: ResearchPriority = ResearchPriority.MEDIUM
    literature_support: int = Field(description="Number of supporting publications", ge=0, default=0)

# ================================
# NETWORK ANALYSIS RESULTS
# ================================

class NetworkAnalysisResult(BaseModel):
    """Results from systematic dopaminergic network discovery"""
    discovery_mode: DiscoveryMode = Field(description="Discovery mode used for network building")
    confidence_threshold: float = Field(description="Confidence threshold for interactions", ge=0.0, le=1.0)
    total_proteins: int = Field(description="Total proteins in the network", ge=0)
    total_interactions: int = Field(description="Total interactions discovered", ge=0)
    
    # Detailed protein and interaction data
    proteins: List[ProteinEntity] = Field(description="All proteins in network", default_factory=list)
    interactions: List[ProteinInteraction] = Field(description="All protein interactions", default_factory=list)
    
    # Network topology analysis
    hub_proteins: List[HubProtein] = Field(description="Hub proteins with high connectivity", default_factory=list)
    novel_proteins: List[str] = Field(description="Novel proteins discovered through analysis", default_factory=list)
    unexpected_connections: List[NovelConnection] = Field(description="Unexpected high-confidence connections", default_factory=list)
    functional_clusters: Dict[str, FunctionalCluster] = Field(description="Functional protein clusters", default_factory=dict)
    
    # Paradigm-challenging evidence
    paradigm_evidence_count: int = Field(description="Number of paradigm-challenging connections found", ge=0, default=0)
    pathology_synthesis_connections: List[ProteinInteraction] = Field(description="Direct pathology-synthesis interactions", default_factory=list)
    network_confidence: ConfidenceLevel = Field(description="Overall network confidence assessment", default=ConfidenceLevel.MODERATE)
    
    # Analysis metadata
    analysis_timestamp: datetime = Field(description="When analysis was completed", default_factory=datetime.now)
    database_sources: List[str] = Field(description="Databases used for discovery", default_factory=list)

    @field_validator('paradigm_evidence_count', mode='after')
    @classmethod
    def validate_paradigm_evidence(cls, v: int, info: ValidationInfo) -> int:
        """Ensure paradigm evidence count matches actual connections"""
        if info.data and 'pathology_synthesis_connections' in info.data:
            expected_count = len(info.data['pathology_synthesis_connections'])
            if v != expected_count:
                # Allow some flexibility but warn about mismatches
                return max(v, expected_count)
        return v

# ================================
# VALIDATION RESULTS
# ================================

class CrossValidationEvidence(BaseModel):
    """Evidence from cross-database validation"""
    interaction: ProteinInteraction
    supporting_databases: List[str] = Field(description="Databases confirming interaction")
    confidence_scores: Dict[str, float] = Field(description="Confidence per database", default_factory=dict)
    consensus_confidence: float = Field(description="Consensus confidence across databases", ge=0.0, le=1.0)
    validation_status: ValidationStatus = ValidationStatus.PENDING

class ValidationReport(BaseModel):
    """Results from cross-database validation analysis"""
    databases_validated: List[str] = Field(description="Databases used for validation")
    total_interactions_validated: int = Field(description="Total interactions submitted for validation", ge=0)
    cross_validated_interactions: int = Field(description="Interactions confirmed across databases", ge=0)
    validation_success_rate: float = Field(description="Percentage of interactions cross-validated", ge=0.0, le=1.0)
    
    # Detailed validation evidence
    convergent_evidence: List[CrossValidationEvidence] = Field(description="Interactions with convergent evidence", default_factory=list)
    protein_resolution_rate: float = Field(description="Success rate of protein entity resolution", ge=0.0, le=1.0, default=0.0)
    research_confidence: ConfidenceLevel = Field(description="Overall research confidence based on validation", default=ConfidenceLevel.LOW)
    
    # Priority validations for experimental follow-up
    priority_validations: List[Dict[str, Any]] = Field(description="Highest priority interactions for experimental validation", default_factory=list)
    
    # Database-specific metrics
    database_coverage: Dict[str, float] = Field(description="Coverage percentage per database", default_factory=dict)
    database_agreement: Dict[str, float] = Field(description="Agreement scores between databases", default_factory=dict)
    
    # Validation metadata
    validation_timestamp: datetime = Field(description="When validation was completed", default_factory=datetime.now)
    validation_parameters: Dict[str, Any] = Field(description="Parameters used for validation", default_factory=dict)

    @field_validator('validation_success_rate', mode='after')
    @classmethod
    def calculate_success_rate(cls, v: float, info: ValidationInfo) -> float:
        """Calculate validation success rate from counts"""
        if info.data and 'total_interactions_validated' in info.data and 'cross_validated_interactions' in info.data:
            total = info.data['total_interactions_validated']
            validated = info.data['cross_validated_interactions']
            if total > 0:
                calculated_rate = validated / total
                return calculated_rate
        return v

# ================================
# PARADIGM CHALLENGE ANALYSIS
# ================================

class TemporalDisruptionHypothesis(BaseModel):
    """Hypothesis about temporal sequence of molecular disruptions"""
    early_disruption_stage: str = Field(description="Early disruption mechanism")
    late_disruption_stage: str = Field(description="Late disruption mechanism")
    evidence_strength: float = Field(description="Strength of temporal evidence", ge=0.0, le=1.0)
    supporting_interactions: List[str] = Field(description="Interactions supporting hypothesis", default_factory=list)
    clinical_implications: List[str] = Field(description="Clinical implications of temporal sequence", default_factory=list)

class ExperimentalValidationPriority(BaseModel):
    """Priority experimental validation target"""
    target: str = Field(description="Target protein or interaction")
    priority_level: ResearchPriority = Field(description="Priority level for validation")
    rationale: str = Field(description="Scientific rationale for priority")
    suggested_experiments: List[str] = Field(description="Suggested experimental approaches", default_factory=list)
    expected_outcome: str = Field(description="Expected experimental outcome", default="")
    resource_requirements: Dict[str, str] = Field(description="Required resources and expertise", default_factory=dict)

class ParadigmChallengeInsights(BaseModel):
    """Analysis of paradigm-challenging evidence"""
    alpha_synuclein_challenge_strength: ParadigmChallengeStrength = Field(description="Strength of evidence challenging α-synuclein paradigm")
    direct_pathology_synthesis_connections: int = Field(description="Number of direct pathology-synthesis connections", ge=0)
    temporal_disruption_hypothesis: TemporalDisruptionHypothesis = Field(description="Evidence for early dopaminergic disruption")
    paradigm_challenge_score: float = Field(description="Quantitative paradigm challenge strength (0-1)", ge=0.0, le=1.0)
    alternative_mechanism: str = Field(description="Alternative disease mechanism hypothesis")
    
    # Detailed paradigm analysis
    alpha_synuclein_network_position: Dict[str, Any] = Field(description="Analysis of SNCA's network position", default_factory=dict)
    dopaminergic_disruption_evidence: List[str] = Field(description="Evidence for early dopaminergic disruption", default_factory=list)
    paradigm_shift_implications: List[str] = Field(description="Implications of paradigm shift", default_factory=list)
    
    # Experimental validation priorities
    experimental_validation_priorities: List[ExperimentalValidationPriority] = Field(description="Priority experiments for paradigm testing", default_factory=list)
    clinical_implications: List[str] = Field(description="Clinical implications of paradigm challenge", default_factory=list)
    therapeutic_implications: List[str] = Field(description="Therapeutic implications", default_factory=list)
    
    # Analysis metadata
    analysis_timestamp: datetime = Field(description="When paradigm analysis was completed", default_factory=datetime.now)
    confidence_assessment: ConfidenceLevel = Field(description="Confidence in paradigm challenge", default=ConfidenceLevel.LOW)

    @field_validator('paradigm_challenge_score', mode='after')
    @classmethod
    def validate_challenge_score(cls, v: float, info: ValidationInfo) -> float:
        """Ensure paradigm challenge score aligns with strength assessment"""
        if info.data and 'alpha_synuclein_challenge_strength' in info.data:
            strength = info.data['alpha_synuclein_challenge_strength']
            if strength == ParadigmChallengeStrength.INSUFFICIENT and v > 0.2:
                return 0.1
            elif strength == ParadigmChallengeStrength.COMPELLING and v < 0.8:
                return 0.9
        return v

# ================================
# RESEARCH SYNTHESIS RESULTS
# ================================

class ResearchTarget(BaseModel):
    """Priority research target for experimental validation"""
    protein: str = Field(description="Target protein gene symbol")
    interaction_partner: Optional[str] = Field(description="Interaction partner if applicable", default=None)
    priority_level: ResearchPriority = Field(description="Research priority level")
    rationale: str = Field(description="Scientific rationale for prioritization")
    paradigm_relevance: float = Field(description="Relevance to paradigm challenge", ge=0.0, le=1.0)
    translational_potential: float = Field(description="Clinical translation potential", ge=0.0, le=1.0)
    feasibility_score: float = Field(description="Experimental feasibility", ge=0.0, le=1.0)

class ExperimentalValidationPlan(BaseModel):
    """Comprehensive experimental validation strategy"""
    cellular_models: List[str] = Field(description="Recommended cellular model systems", default_factory=list)
    animal_models: List[str] = Field(description="Recommended animal model systems", default_factory=list)
    molecular_techniques: List[str] = Field(description="Required molecular techniques", default_factory=list)
    validation_timeline: Dict[str, str] = Field(description="Validation timeline and milestones", default_factory=dict)
    resource_requirements: Dict[str, Any] = Field(description="Required resources and expertise", default_factory=dict)
    success_criteria: List[str] = Field(description="Criteria for successful validation", default_factory=list)

class ClinicalTranslationPotential(BaseModel):
    """Assessment of clinical translation potential"""
    biomarker_potential: Dict[str, Any] = Field(description="Biomarker development potential", default_factory=dict)
    therapeutic_targets: List[str] = Field(description="Potential therapeutic targets", default_factory=list)
    diagnostic_applications: List[str] = Field(description="Potential diagnostic applications", default_factory=list)
    development_timeline: str = Field(description="Estimated development timeline", default="")
    regulatory_pathway: str = Field(description="Regulatory approval pathway", default="")
    commercial_viability: float = Field(description="Commercial viability assessment", ge=0.0, le=1.0, default=0.0)

# ================================
# COMPREHENSIVE RESEARCH STATE
# ================================

class PDResearchState(BaseModel):
    """Complete state of PD paradigm challenge research analysis"""
    
    # Core research parameters
    research_question: str = Field(description="Original research question")
    confidence_threshold: float = Field(description="Confidence threshold for analysis", ge=0.0, le=1.0, default=0.7)
    discovery_mode: DiscoveryMode = Field(description="Network discovery mode", default=DiscoveryMode.COMPREHENSIVE)
    
    # Analysis results
    network_analysis: Optional[NetworkAnalysisResult] = Field(description="Network discovery results", default=None)
    validation_report: Optional[ValidationReport] = Field(description="Cross-database validation results", default=None)
    paradigm_insights: Optional[ParadigmChallengeInsights] = Field(description="Paradigm challenge analysis", default=None)
    
    # Research synthesis
    research_priorities: List[ResearchTarget] = Field(description="Prioritized research recommendations", default_factory=list)
    experimental_validation_plan: Optional[ExperimentalValidationPlan] = Field(description="Comprehensive experimental validation strategy", default=None)
    clinical_translation_potential: Optional[ClinicalTranslationPotential] = Field(description="Assessment of clinical translation potential", default=None)
    
    # Quality and confidence assessment
    research_confidence: ConfidenceLevel = Field(description="Overall research confidence assessment", default=ConfidenceLevel.LOW)
    validation_passed: bool = Field(description="Whether validation criteria were met", default=False)
    paradigm_challenge_strength: ParadigmChallengeStrength = Field(description="Overall paradigm challenge strength", default=ParadigmChallengeStrength.INSUFFICIENT)
    
    # Flow control and error handling
    iterations: int = Field(description="Number of analysis iterations", ge=0, default=0)
    max_iterations: int = Field(description="Maximum allowed iterations", ge=1, default=3)
    errors: List[str] = Field(description="Errors encountered during analysis", default_factory=list)
    warnings: List[str] = Field(description="Warnings generated during analysis", default_factory=list)
    
    # Metadata
    analysis_start_time: datetime = Field(description="When analysis was initiated", default_factory=datetime.now)
    analysis_completion_time: Optional[datetime] = Field(description="When analysis was completed", default=None)
    analysis_duration: Optional[float] = Field(description="Analysis duration in seconds", default=None)
    database_sources: List[str] = Field(description="Databases used in analysis", default_factory=list)
    
    # Research configuration
    max_proteins_per_cluster: int = Field(description="Maximum proteins per functional cluster", ge=1, default=50)
    min_interaction_confidence: float = Field(description="Minimum interaction confidence", ge=0.0, le=1.0, default=0.4)
    paradigm_challenge_threshold: float = Field(description="Threshold for paradigm challenge significance", ge=0.0, le=1.0, default=0.5)

    @model_validator(mode='after')
    def validate_analysis_completion(self):
        """Validate analysis completion and calculate duration"""
        if self.analysis_start_time and self.analysis_completion_time:
            duration = (self.analysis_completion_time - self.analysis_start_time).total_seconds()
            self.analysis_duration = duration
        return self

    @field_validator('research_confidence', mode='after')
    @classmethod
    def calculate_overall_confidence(cls, v: ConfidenceLevel, info: ValidationInfo) -> ConfidenceLevel:
        """Calculate overall research confidence based on component analyses"""
        if not info.data:
            return v
            
        confidence_factors = []
        
        # Network analysis confidence
        if info.data.get('network_analysis'):
            network_conf = info.data['network_analysis'].network_confidence
            if network_conf == ConfidenceLevel.HIGH:
                confidence_factors.append(0.9)
            elif network_conf == ConfidenceLevel.MODERATE:
                confidence_factors.append(0.6)
            else:
                confidence_factors.append(0.3)
        
        # Validation confidence
        if info.data.get('validation_report'):
            val_conf = info.data['validation_report'].research_confidence
            if val_conf == ConfidenceLevel.HIGH:
                confidence_factors.append(0.9)
            elif val_conf == ConfidenceLevel.MODERATE:
                confidence_factors.append(0.6)
            else:
                confidence_factors.append(0.3)
        
        # Paradigm challenge confidence
        if info.data.get('paradigm_insights'):
            para_conf = info.data['paradigm_insights'].confidence_assessment
            if para_conf == ConfidenceLevel.HIGH:
                confidence_factors.append(0.9)
            elif para_conf == ConfidenceLevel.MODERATE:
                confidence_factors.append(0.6)
            else:
                confidence_factors.append(0.3)
        
        # Calculate overall confidence
        if confidence_factors:
            avg_confidence = sum(confidence_factors) / len(confidence_factors)
            if avg_confidence >= 0.8:
                return ConfidenceLevel.HIGH
            elif avg_confidence >= 0.6:
                return ConfidenceLevel.MODERATE
            else:
                return ConfidenceLevel.LOW
        
        return v

    def mark_completion(self):
        """Mark analysis as completed and calculate duration"""
        self.analysis_completion_time = datetime.now()
        if self.analysis_start_time:
            self.analysis_duration = (self.analysis_completion_time - self.analysis_start_time).total_seconds()

    def add_error(self, error_message: str):
        """Add error message to error list"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.errors.append(f"[{timestamp}] {error_message}")

    def add_warning(self, warning_message: str):
        """Add warning message to warning list"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.warnings.append(f"[{timestamp}] {warning_message}")

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of research state"""
        return {
            "research_question": self.research_question,
            "confidence_level": self.research_confidence,
            "paradigm_challenge_strength": self.paradigm_challenge_strength,
            "validation_passed": self.validation_passed,
            "iterations_completed": self.iterations,
            "errors_count": len(self.errors),
            "warnings_count": len(self.warnings),
            "analysis_duration": self.analysis_duration,
            "has_network_analysis": self.network_analysis is not None,
            "has_validation_report": self.validation_report is not None,
            "has_paradigm_insights": self.paradigm_insights is not None,
            "research_priorities_count": len(self.research_priorities)
        }

# ================================
# UTILITY FUNCTIONS
# ================================

def create_default_research_state(research_question: str) -> PDResearchState:
    """Create a default research state for new analysis"""
    return PDResearchState(
        research_question=research_question,
        confidence_threshold=0.7,
        discovery_mode=DiscoveryMode.COMPREHENSIVE,
        max_iterations=3,
        database_sources=["string", "biogrid", "pride"]
    )

def validate_research_state(state: PDResearchState) -> List[str]:
    """Validate research state completeness and consistency"""
    validation_errors = []
    
    # Check basic requirements
    if not state.research_question:
        validation_errors.append("Research question is required")
    
    if state.confidence_threshold < 0.0 or state.confidence_threshold > 1.0:
        validation_errors.append("Confidence threshold must be between 0.0 and 1.0")
    
    # Check analysis completeness
    if state.validation_passed:
        if not state.network_analysis:
            validation_errors.append("Network analysis required for passed validation")
        if not state.validation_report:
            validation_errors.append("Validation report required for passed validation")
        if not state.paradigm_insights:
            validation_errors.append("Paradigm insights required for passed validation")
    
    # Check consistency
    if state.network_analysis and state.validation_report:
        network_interactions = state.network_analysis.total_interactions
        validated_interactions = state.validation_report.total_interactions_validated
        if validated_interactions > network_interactions:
            validation_errors.append("Cannot validate more interactions than discovered")
    
    return validation_errors

# ================================
# EXAMPLE USAGE
# ================================

if __name__ == "__main__":
    # Example of creating and using the state management system
    
    # Create a new research state
    research_state = create_default_research_state(
        "Find evidence that dopaminergic network disruption precedes α-synuclein aggregation in Parkinson's disease"
    )
    
    print("Created research state:")
    print(f"Research Question: {research_state.research_question}")
    print(f"Confidence Threshold: {research_state.confidence_threshold}")
    print(f"Discovery Mode: {research_state.discovery_mode}")
    
    # Validate the state
    validation_errors = validate_research_state(research_state)
    if validation_errors:
        print(f"Validation errors: {validation_errors}")
    else:
        print("✅ Research state validation passed")
    
    # Example of creating mock analysis results
    network_result = NetworkAnalysisResult(
        discovery_mode=DiscoveryMode.COMPREHENSIVE,
        confidence_threshold=0.7,
        total_proteins=25,
        total_interactions=150,
        paradigm_evidence_count=5,
        network_confidence=ConfidenceLevel.HIGH
    )
    
    research_state.network_analysis = network_result
    
    # Mark completion and get summary
    research_state.mark_completion()
    summary = research_state.get_summary()
    
    print("\nResearch Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")