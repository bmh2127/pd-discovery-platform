# state_management.py
from typing import Optional, List
from pydantic import BaseModel, Field


class ResearchQuality(BaseModel):
    """Quality assessment for research resources"""
    academic_rigor: int = Field(description="Academic rigor score (1-5)", ge=1, le=5)
    implementation_quality: int = Field(description="Implementation quality score (1-5)", ge=1, le=5)
    educational_value: int = Field(description="Educational value score (1-5)", ge=1, le=5)
    relevance_score: int = Field(description="Relevance to preclinical neuroscience (1-5)", ge=1, le=5)
    overall_score: float = Field(description="Overall quality score", ge=1.0, le=5.0)

class ResearchResource(BaseModel):
    """Individual research resource"""
    title: str
    url: str
    resource_type: str = Field(description="paper, repository, tutorial, blog, video")
    description: str
    quality: ResearchQuality
    prerequisites: List[str] = []
    difficulty_level: str = Field(description="beginner, intermediate, advanced")

class LiteratureResources(BaseModel):
    """Wrapper for literature discovery task output"""
    resources: List[ResearchResource] = Field(description="List of academic literature resources")

class CodeResources(BaseModel):
    """Wrapper for code discovery task output"""
    resources: List[ResearchResource] = Field(description="List of code implementation resources")

class EducationalResources(BaseModel):
    """Wrapper for educational curation task output"""
    resources: List[ResearchResource] = Field(description="List of educational resources")

class LearningPath(BaseModel):
    """Structured learning pathway"""
    topic: str
    resources: List[ResearchResource]
    sequence: List[str] = Field(description="Ordered list of resource titles for optimal learning")
    estimated_time: str = Field(description="Estimated completion time")
    learning_objectives: List[str]

class ResearchState(BaseModel):
    """State for the preclinical neuroscience research flow"""
    research_topic: str = ""
    literature_resources: List[ResearchResource] = []
    code_resources: List[ResearchResource] = []
    educational_resources: List[ResearchResource] = []
    integrated_learning_path: Optional[LearningPath] = None
    quality_threshold: float = 3.0
    max_resources_per_category: int = 15
    iterations: int = 0
    max_iterations: int = 3
    errors: List[str] = []
    validation_passed: bool = False