from dotenv import load_dotenv
import json
from datetime import datetime
from crewai.flow.flow import Flow, start, listen, router
from typing import Dict, List

from crew import PreclinicalNeuroscienceResearchCrew
from state_management import ResearchState, LearningPath, ResearchResource, ResearchQuality
from parsing import ResearchDataParser


# Load environment variables
load_dotenv()

class PreclinicalResearchFlow(Flow[ResearchState]):
    """
    Advanced research flow with quality guardrails, validation, and adaptive workflows
    for preclinical neuroscience research. Now enhanced with robust ResearchDataParser.
    """

    def __init__(self, research_topic: str, quality_threshold: float = 3.0):
        super().__init__()
        self.state.research_topic = research_topic
        self.state.quality_threshold = quality_threshold
        self.crew_instance = PreclinicalNeuroscienceResearchCrew()
        self.crew = self.crew_instance.crew()
        
        # Initialize the robust parser
        self.parser = ResearchDataParser()

    @start()
    def initiate_research(self):
        """Start the research process and execute the complete crew workflow"""
        print(f"---INITIATING RESEARCH FOR: {self.state.research_topic}---")
        
        # Validate research topic
        if not self.state.research_topic or len(self.state.research_topic.strip()) < 5:
            self.state.errors.append("Research topic is too short or empty")
            return self._create_failure_report("Invalid research topic provided")
        
        print(f"Research topic validated: {self.state.research_topic}")
        
        # Execute the complete crew workflow
        print("---EXECUTING COMPLETE RESEARCH CREW WORKFLOW---")
        
        try:
            # Execute the entire crew workflow once
            print("Executing crew with all tasks...")
            result = self.crew.kickoff(
                inputs={"research_topic": self.state.research_topic}
            )
            
            print("Parsing task outputs from crew execution...")
            
            # Parse outputs from each task
            if hasattr(result, 'tasks_output') and result.tasks_output:
                # Extract literature resources from first task
                literature_task_output = result.tasks_output[0] if len(result.tasks_output) > 0 else None
                if literature_task_output:
                    if hasattr(literature_task_output, 'pydantic') and literature_task_output.pydantic:
                        try:
                            literature_output = literature_task_output.pydantic
                            if hasattr(literature_output, 'resources'):
                                literature_resources = literature_output.resources
                            else:
                                literature_resources = [literature_output] if not isinstance(literature_output, list) else literature_output
                        except Exception as e:
                            print(f"Literature pydantic parsing failed: {e}")
                            literature_resources = self.parser._parse_literature_output(literature_task_output.raw)
                    else:
                        literature_resources = self.parser._parse_literature_output(literature_task_output.raw)
                else:
                    literature_resources = []
                
                # Extract code resources from second task
                code_task_output = result.tasks_output[1] if len(result.tasks_output) > 1 else None
                if code_task_output:
                    if hasattr(code_task_output, 'pydantic') and code_task_output.pydantic:
                        try:
                            code_output = code_task_output.pydantic
                            if hasattr(code_output, 'resources'):
                                code_resources = code_output.resources
                            else:
                                code_resources = [code_output] if not isinstance(code_output, list) else code_output
                        except Exception as e:
                            print(f"Code pydantic parsing failed: {e}")
                            code_resources = self.parser._parse_code_output(code_task_output.raw)
                    else:
                        code_resources = self.parser._parse_code_output(code_task_output.raw)
                else:
                    code_resources = []
                
                # Extract educational resources from third task
                educational_task_output = result.tasks_output[2] if len(result.tasks_output) > 2 else None
                if educational_task_output:
                    if hasattr(educational_task_output, 'pydantic') and educational_task_output.pydantic:
                        try:
                            educational_output = educational_task_output.pydantic
                            if hasattr(educational_output, 'resources'):
                                educational_resources = educational_output.resources
                            else:
                                educational_resources = [educational_output] if not isinstance(educational_output, list) else educational_output
                        except Exception as e:
                            print(f"Educational pydantic parsing failed: {e}")
                            educational_resources = self.parser._parse_educational_output(educational_task_output.raw)
                    else:
                        educational_resources = self.parser._parse_educational_output(educational_task_output.raw)
                else:
                    educational_resources = []
                
                # Extract learning path from fourth task
                synthesis_task_output = result.tasks_output[3] if len(result.tasks_output) > 3 else None
                if synthesis_task_output:
                    if hasattr(synthesis_task_output, 'pydantic') and synthesis_task_output.pydantic:
                        try:
                            learning_path = synthesis_task_output.pydantic
                            # If it's already a LearningPath object, use it directly
                            if hasattr(learning_path, 'topic') and hasattr(learning_path, 'resources'):
                                print(f"Successfully extracted learning path: {learning_path.topic}")
                            else:
                                # Otherwise try to parse it
                                if isinstance(learning_path, dict):
                                    learning_path = self.parser._parse_learning_path_from_dict(learning_path)
                                else:
                                    learning_path = self.parser._parse_synthesis_output(str(learning_path))
                        except Exception as e:
                            print(f"Synthesis pydantic parsing failed: {e}")
                            learning_path = self.parser._parse_synthesis_output(synthesis_task_output.raw)
                    else:
                        learning_path = self.parser._parse_synthesis_output(synthesis_task_output.raw)
                else:
                    learning_path = None
                    
            else:
                # Fallback: try to parse from single result
                print("No individual task outputs found, attempting to parse from combined result...")
                literature_resources = self.parser._parse_literature_output(result.raw)
                code_resources = self.parser._parse_code_output(result.raw)
                educational_resources = self.parser._parse_educational_output(result.raw)
                learning_path = self.parser._parse_synthesis_output(result.raw)
            
            # Validate and store resources
            validated_literature = self._validate_resource_quality(literature_resources, "academic literature")
            validated_code = self._validate_code_quality(code_resources)
            validated_educational = self._validate_educational_quality(educational_resources)
            
            self.state.literature_resources = validated_literature
            self.state.code_resources = validated_code
            self.state.educational_resources = validated_educational
            
            if learning_path and self._validate_learning_path(learning_path):
                self.state.integrated_learning_path = learning_path
                print(f"✅ Learning path validated and stored: {learning_path.topic}")
            else:
                print(f"❌ Learning path validation failed or path is None")
                if learning_path:
                    print(f"Learning path object: {type(learning_path)}")
                    print(f"Has topic: {hasattr(learning_path, 'topic')}")
                    print(f"Has resources: {hasattr(learning_path, 'resources')}")
                    if hasattr(learning_path, 'resources'):
                        print(f"Resources count: {len(learning_path.resources) if learning_path.resources else 0}")
            
            print(f"Found {len(validated_literature)} literature, {len(validated_code)} code, {len(validated_educational)} educational resources")
            
            # Perform final validation and return results
            print("---PERFORMING FINAL VALIDATION---")
            validation_results = self._perform_comprehensive_validation()
            
            # Save detailed results to JSON file
            final_result = None
            if validation_results["passed"]:
                self.state.validation_passed = True
                print("---RESEARCH COMPLETED SUCCESSFULLY---")
                final_result = self._create_success_report()
            else:
                print("---RESEARCH COMPLETED WITH ISSUES---")
                final_result = self._create_partial_success_report(validation_results)
            
            # Save to JSON file for easy access
            self._save_detailed_results_to_file(final_result)
            
            return final_result
            
        except Exception as e:
            self.state.errors.append(f"Crew execution failed: {str(e)}")
            print(f"Error during crew execution: {e}")
            return self._create_failure_report(f"Crew execution failed: {str(e)}")

    @listen("topic_validation_failed")
    def handle_topic_validation_failure(self):
        """Handle invalid research topics"""
        print("---TOPIC VALIDATION FAILED---")
        self.state.errors.append("Invalid research topic provided")
        return "research_failed"

    @listen("discover_literature")
    def discover_academic_literature(self):
        """Execute the complete crew workflow and extract all task outputs"""
        print("---EXECUTING COMPLETE RESEARCH CREW WORKFLOW---")
        
        try:
            # Execute the entire crew workflow once
            print("Executing crew with all tasks...")
            result = self.crew.kickoff(
                inputs={"research_topic": self.state.research_topic}
            )
            
            print("Parsing task outputs from crew execution...")
            
            # Parse outputs from each task
            if hasattr(result, 'tasks_output') and result.tasks_output:
                # Extract literature resources from first task
                literature_task_output = result.tasks_output[0] if len(result.tasks_output) > 0 else None
                if literature_task_output:
                    if hasattr(literature_task_output, 'pydantic') and literature_task_output.pydantic:
                        try:
                            literature_output = literature_task_output.pydantic
                            if hasattr(literature_output, 'resources'):
                                literature_resources = literature_output.resources
                            else:
                                literature_resources = [literature_output] if not isinstance(literature_output, list) else literature_output
                        except Exception as e:
                            print(f"Literature pydantic parsing failed: {e}")
                            literature_resources = self.parser._parse_literature_output(literature_task_output.raw)
                    else:
                        literature_resources = self.parser._parse_literature_output(literature_task_output.raw)
                else:
                    literature_resources = []
                
                # Extract code resources from second task
                code_task_output = result.tasks_output[1] if len(result.tasks_output) > 1 else None
                if code_task_output:
                    if hasattr(code_task_output, 'pydantic') and code_task_output.pydantic:
                        try:
                            code_output = code_task_output.pydantic
                            if hasattr(code_output, 'resources'):
                                code_resources = code_output.resources
                            else:
                                code_resources = [code_output] if not isinstance(code_output, list) else code_output
                        except Exception as e:
                            print(f"Code pydantic parsing failed: {e}")
                            code_resources = self.parser._parse_code_output(code_task_output.raw)
                    else:
                        code_resources = self.parser._parse_code_output(code_task_output.raw)
                else:
                    code_resources = []
                
                # Extract educational resources from third task
                educational_task_output = result.tasks_output[2] if len(result.tasks_output) > 2 else None
                if educational_task_output:
                    if hasattr(educational_task_output, 'pydantic') and educational_task_output.pydantic:
                        try:
                            educational_output = educational_task_output.pydantic
                            if hasattr(educational_output, 'resources'):
                                educational_resources = educational_output.resources
                            else:
                                educational_resources = [educational_output] if not isinstance(educational_output, list) else educational_output
                        except Exception as e:
                            print(f"Educational pydantic parsing failed: {e}")
                            educational_resources = self.parser._parse_educational_output(educational_task_output.raw)
                    else:
                        educational_resources = self.parser._parse_educational_output(educational_task_output.raw)
                else:
                    educational_resources = []
                
                # Extract learning path from fourth task
                synthesis_task_output = result.tasks_output[3] if len(result.tasks_output) > 3 else None
                if synthesis_task_output:
                    if hasattr(synthesis_task_output, 'pydantic') and synthesis_task_output.pydantic:
                        try:
                            learning_path = synthesis_task_output.pydantic
                            # If it's already a LearningPath object, use it directly
                            if hasattr(learning_path, 'topic') and hasattr(learning_path, 'resources'):
                                print(f"Successfully extracted learning path: {learning_path.topic}")
                            else:
                                # Otherwise try to parse it
                                if isinstance(learning_path, dict):
                                    learning_path = self.parser._parse_learning_path_from_dict(learning_path)
                                else:
                                    learning_path = self.parser._parse_synthesis_output(str(learning_path))
                        except Exception as e:
                            print(f"Synthesis pydantic parsing failed: {e}")
                            learning_path = self.parser._parse_synthesis_output(synthesis_task_output.raw)
                    else:
                        learning_path = self.parser._parse_synthesis_output(synthesis_task_output.raw)
                else:
                    learning_path = None
                    
            else:
                # Fallback: try to parse from single result
                print("No individual task outputs found, attempting to parse from combined result...")
                literature_resources = self.parser._parse_literature_output(result.raw)
                code_resources = self.parser._parse_code_output(result.raw)
                educational_resources = self.parser._parse_educational_output(result.raw)
                learning_path = self.parser._parse_synthesis_output(result.raw)
            
            # Validate and store resources
            validated_literature = self._validate_resource_quality(literature_resources, "academic literature")
            validated_code = self._validate_code_quality(code_resources)
            validated_educational = self._validate_educational_quality(educational_resources)
            
            self.state.literature_resources = validated_literature
            self.state.code_resources = validated_code
            self.state.educational_resources = validated_educational
            
            if learning_path and self._validate_learning_path(learning_path):
                self.state.integrated_learning_path = learning_path
            
            print(f"Found {len(validated_literature)} literature, {len(validated_code)} code, {len(validated_educational)} educational resources")
            
            # Check if we have sufficient resources
            if not validated_literature and not validated_code and not validated_educational:
                self.state.errors.append("No high-quality resources found in any category")
                return "research_failed"
            
            if len(validated_literature) < 2 or len(validated_code) < 1 or len(validated_educational) < 2:
                print("Insufficient resources found, but some results available - proceeding with validation")
            
            return "validate_final_output"
            
        except Exception as e:
            self.state.errors.append(f"Crew execution failed: {str(e)}")
            print(f"Error during crew execution: {e}")
            return "research_failed"

    @listen("discover_code")
    def handle_code_discovery_legacy(self):
        """Legacy method - code discovery now handled in main crew execution"""
        print("---CODE DISCOVERY ALREADY COMPLETED---")
        return "curate_educational_content"

    @listen("curate_educational_content")
    def handle_educational_curation_legacy(self):
        """Legacy method - educational curation now handled in main crew execution"""
        print("---EDUCATIONAL CURATION ALREADY COMPLETED---")
        return "synthesize_knowledge"

    @listen("synthesize_knowledge")
    def handle_synthesis_legacy(self):
        """Legacy method - synthesis now handled in main crew execution"""
        print("---KNOWLEDGE SYNTHESIS ALREADY COMPLETED---")
        return "validate_final_output"

    @router("validate_final_output")
    def route_final_validation(self):
        """Route based on final validation results"""
        print("---PERFORMING FINAL VALIDATION---")
        
        # Comprehensive validation checks
        validation_results = self._perform_comprehensive_validation()
        
        if validation_results["passed"]:
            self.state.validation_passed = True
            return "research_complete"
        elif self.state.iterations < self.state.max_iterations:
            return "retry_research"
        else:
            return "research_failed_max_attempts"

    @listen("retry_research")
    def retry_research_with_feedback(self):
        """Retry research with improved parameters based on previous failures"""
        print("---RETRYING RESEARCH WITH IMPROVED PARAMETERS---")
        
        self.state.iterations += 1
        
        # Adjust quality threshold and resource limits based on failures
        if "quality_failed" in " ".join(self.state.errors):
            self.state.quality_threshold = max(2.5, self.state.quality_threshold - 0.3)
            print(f"Lowered quality threshold to {self.state.quality_threshold}")
        
        if "No" in " ".join(self.state.errors) and "found" in " ".join(self.state.errors):
            self.state.max_resources_per_category += 5
            print(f"Increased max resources to {self.state.max_resources_per_category}")
        
        # Clear previous errors and resources
        self.state.errors = []
        self.state.literature_resources = []
        self.state.code_resources = []
        self.state.educational_resources = []
        
        return "discover_literature"

    @listen("research_complete")
    def finalize_research_output(self):
        """Finalize and structure the research output"""
        print("---RESEARCH COMPLETED SUCCESSFULLY---")
        
        # Generate final report
        final_report = {
            "research_topic": self.state.research_topic,
            "total_resources": len(self.state.literature_resources) + 
                             len(self.state.code_resources) + 
                             len(self.state.educational_resources),
            "literature_count": len(self.state.literature_resources),
            "code_count": len(self.state.code_resources),
            "educational_count": len(self.state.educational_resources),
            "learning_path": self.state.integrated_learning_path.dict() if self.state.integrated_learning_path else None,
            "average_quality_score": self._calculate_average_quality(),
            "iterations_required": self.state.iterations + 1,
            "parser_used": "ResearchDataParser"  # Indicate robust parser was used
        }
        
        print("Research Summary:")
        print(json.dumps(final_report, indent=2))
        
        return final_report

    @listen("research_failed")
    @listen("research_failed_max_attempts")
    @listen("literature_quality_failed")
    @listen("code_quality_failed") 
    @listen("educational_quality_failed")
    @listen("synthesis_quality_failed")
    @listen("literature_discovery_failed")
    @listen("code_discovery_failed")
    @listen("educational_curation_failed")
    @listen("synthesis_failed")
    def handle_research_failure(self):
        """Handle various types of research failures"""
        print("---RESEARCH FAILED---")
        
        failure_report = {
            "research_topic": self.state.research_topic,
            "failure_reasons": self.state.errors,
            "iterations_attempted": self.state.iterations + 1,
            "partial_results": {
                "literature_found": len(self.state.literature_resources),
                "code_found": len(self.state.code_resources),
                "educational_found": len(self.state.educational_resources)
            },
            "parser_used": "ResearchDataParser"
        }
        
        print("Failure Report:")
        print(json.dumps(failure_report, indent=2))
        
        return failure_report

    # ================================
    # VALIDATION AND QUALITY METHODS
    # ================================

    def _validate_resource_quality(self, resources: List[ResearchResource], resource_type: str) -> List[ResearchResource]:
        """Validate resource quality against threshold"""
        validated = []
        for resource in resources:
            if resource.quality.overall_score >= self.state.quality_threshold:
                validated.append(resource)
            else:
                print(f"Filtered out low-quality {resource_type}: {resource.title} (score: {resource.quality.overall_score})")
        
        return validated[:self.state.max_resources_per_category]

    def _validate_code_quality(self, resources: List[ResearchResource]) -> List[ResearchResource]:
        """Additional validation for code implementations"""
        validated = []
        for resource in resources:
            # Check implementation quality specifically
            if (resource.quality.implementation_quality >= self.state.quality_threshold and 
                resource.quality.overall_score >= self.state.quality_threshold):
                validated.append(resource)
        
        return validated[:self.state.max_resources_per_category]

    def _validate_educational_quality(self, resources: List[ResearchResource]) -> List[ResearchResource]:
        """Additional validation for educational effectiveness"""
        validated = []
        for resource in resources:
            # Check educational value specifically
            if (resource.quality.educational_value >= self.state.quality_threshold and 
                resource.quality.overall_score >= self.state.quality_threshold):
                validated.append(resource)
        
        return validated[:self.state.max_resources_per_category]

    def _validate_learning_path(self, learning_path: LearningPath) -> bool:
        """Validate completeness and quality of learning path"""
        if not learning_path or not learning_path.resources:
            return False
        
        # Check for balanced resource types - more flexible validation
        resource_types = [r.resource_type.lower() for r in learning_path.resources]
        
        # Check for academic literature (papers, reviews, articles)
        has_papers = any(any(term in rt for term in ["paper", "review", "article", "systematic", "meta-analysis"]) 
                        for rt in resource_types)
        
        # Check for code implementations (repositories, notebooks, tutorials)
        has_code = any(any(term in rt for term in ["repository", "notebook", "implementation", "code"]) 
                      for rt in resource_types)
        
        # Check for educational content (tutorials, blogs, courses, educational materials)
        has_tutorials = any(any(term in rt for term in ["tutorial", "blog", "course", "educational", "guide", "notebook"]) 
                           for rt in resource_types)
        
        print(f"Learning path validation - Papers: {has_papers}, Code: {has_code}, Tutorials: {has_tutorials}")
        print(f"Resource types found: {resource_types}")
        
        return has_papers and has_code and has_tutorials

    def _perform_comprehensive_validation(self) -> Dict[str, any]:
        """Perform comprehensive validation of all research outputs"""
        results = {"passed": True, "issues": []}
        
        # Check minimum resource counts
        if len(self.state.literature_resources) < 3:
            results["issues"].append("Insufficient literature resources")
            results["passed"] = False
        
        if len(self.state.code_resources) < 2:
            results["issues"].append("Insufficient code implementations")
            results["passed"] = False
        
        if len(self.state.educational_resources) < 3:
            results["issues"].append("Insufficient educational resources")
            results["passed"] = False
        
        # Check learning path quality
        if not self.state.integrated_learning_path:
            results["issues"].append("No integrated learning path generated")
            results["passed"] = False
        
        # Check average quality
        avg_quality = self._calculate_average_quality()
        if avg_quality < self.state.quality_threshold:
            results["issues"].append(f"Average quality {avg_quality} below threshold {self.state.quality_threshold}")
            results["passed"] = False
        
        return results

    def _calculate_average_quality(self) -> float:
        """Calculate average quality score across all resources"""
        all_resources = (self.state.literature_resources + 
                        self.state.code_resources + 
                        self.state.educational_resources)
        
        if not all_resources:
            return 0.0
        
        total_score = sum(r.quality.overall_score for r in all_resources)
        return total_score / len(all_resources)

    # ================================
    # CONTEXT CREATION METHODS
    # ================================

    def _create_literature_context(self) -> str:
        """Create context from discovered literature for code discovery"""
        if not self.state.literature_resources:
            return ""
        
        context_parts = []
        for resource in self.state.literature_resources[:5]:  # Top 5 papers
            context_parts.append(f"- {resource.title}: {resource.description}")
        
        return "Academic Literature Context:\n" + "\n".join(context_parts)

    def _create_full_research_context(self) -> str:
        """Create comprehensive context from all discovered resources"""
        context_parts = []
        
        if self.state.literature_resources:
            context_parts.append("Literature Resources:")
            for resource in self.state.literature_resources[:3]:
                context_parts.append(f"- {resource.title}")
        
        if self.state.code_resources:
            context_parts.append("\nCode Resources:")
            for resource in self.state.code_resources[:3]:
                context_parts.append(f"- {resource.title}")
        
        return "\n".join(context_parts)

    # ================================
    # FALLBACK METHODS FOR COMPATIBILITY
    # ================================
    
    def _create_default_learning_path(self) -> LearningPath:
        """Create a default learning path when synthesis fails completely"""
        return self.parser._create_default_learning_path()

    def _create_success_report(self):
        """Create a comprehensive success report with all detailed resources"""
        
        # Convert all resources to dictionaries for JSON serialization
        literature_details = []
        for resource in self.state.literature_resources:
            literature_details.append({
                "title": resource.title,
                "url": resource.url,
                "resource_type": resource.resource_type,
                "description": resource.description,
                "quality_assessment": {
                    "academic_rigor": resource.quality.academic_rigor,
                    "implementation_quality": resource.quality.implementation_quality,
                    "educational_value": resource.quality.educational_value,
                    "relevance_score": resource.quality.relevance_score,
                    "overall_score": resource.quality.overall_score
                },
                "prerequisites": resource.prerequisites,
                "difficulty_level": resource.difficulty_level
            })
        
        code_details = []
        for resource in self.state.code_resources:
            code_details.append({
                "title": resource.title,
                "url": resource.url,
                "resource_type": resource.resource_type,
                "description": resource.description,
                "quality_assessment": {
                    "academic_rigor": resource.quality.academic_rigor,
                    "implementation_quality": resource.quality.implementation_quality,
                    "educational_value": resource.quality.educational_value,
                    "relevance_score": resource.quality.relevance_score,
                    "overall_score": resource.quality.overall_score
                },
                "prerequisites": resource.prerequisites,
                "difficulty_level": resource.difficulty_level
            })
        
        educational_details = []
        for resource in self.state.educational_resources:
            educational_details.append({
                "title": resource.title,
                "url": resource.url,
                "resource_type": resource.resource_type,
                "description": resource.description,
                "quality_assessment": {
                    "academic_rigor": resource.quality.academic_rigor,
                    "implementation_quality": resource.quality.implementation_quality,
                    "educational_value": resource.quality.educational_value,
                    "relevance_score": resource.quality.relevance_score,
                    "overall_score": resource.quality.overall_score
                },
                "prerequisites": resource.prerequisites,
                "difficulty_level": resource.difficulty_level
            })
        
        # Get learning path details
        learning_path_details = None
        if self.state.integrated_learning_path:
            learning_path_details = {
                "topic": self.state.integrated_learning_path.topic,
                "sequence": self.state.integrated_learning_path.sequence,
                "estimated_time": self.state.integrated_learning_path.estimated_time,
                "learning_objectives": self.state.integrated_learning_path.learning_objectives,
                "resources": []
            }
            
            # Add detailed resource information to learning path
            for resource in self.state.integrated_learning_path.resources:
                learning_path_details["resources"].append({
                    "title": resource.title,
                    "url": resource.url,
                    "resource_type": resource.resource_type,
                    "description": resource.description,
                    "quality_assessment": {
                        "academic_rigor": resource.quality.academic_rigor,
                        "implementation_quality": resource.quality.implementation_quality,
                        "educational_value": resource.quality.educational_value,
                        "relevance_score": resource.quality.relevance_score,
                        "overall_score": resource.quality.overall_score
                    },
                    "prerequisites": resource.prerequisites,
                    "difficulty_level": resource.difficulty_level
                })
        
        return {
            "status": "success",
            "research_topic": self.state.research_topic,
            "summary": {
                "total_resources": len(self.state.literature_resources) + 
                                 len(self.state.code_resources) + 
                                 len(self.state.educational_resources),
                "literature_count": len(self.state.literature_resources),
                "code_count": len(self.state.code_resources),
                "educational_count": len(self.state.educational_resources),
                "average_quality_score": self._calculate_average_quality(),
                "validation_passed": self.state.validation_passed
            },
            "detailed_results": {
                "literature_resources": literature_details,
                "code_resources": code_details,
                "educational_resources": educational_details,
                "learning_path": learning_path_details
            },
            "metadata": {
                "parser_used": "ResearchDataParser",
                "quality_threshold": self.state.quality_threshold,
                "iterations_required": self.state.iterations + 1
            }
        }

    def _create_partial_success_report(self, validation_results):
        """Create a comprehensive partial success report with all detailed resources"""
        
        # Convert all resources to dictionaries for JSON serialization
        literature_details = []
        for resource in self.state.literature_resources:
            literature_details.append({
                "title": resource.title,
                "url": resource.url,
                "resource_type": resource.resource_type,
                "description": resource.description,
                "quality_assessment": {
                    "academic_rigor": resource.quality.academic_rigor,
                    "implementation_quality": resource.quality.implementation_quality,
                    "educational_value": resource.quality.educational_value,
                    "relevance_score": resource.quality.relevance_score,
                    "overall_score": resource.quality.overall_score
                },
                "prerequisites": resource.prerequisites,
                "difficulty_level": resource.difficulty_level
            })
        
        code_details = []
        for resource in self.state.code_resources:
            code_details.append({
                "title": resource.title,
                "url": resource.url,
                "resource_type": resource.resource_type,
                "description": resource.description,
                "quality_assessment": {
                    "academic_rigor": resource.quality.academic_rigor,
                    "implementation_quality": resource.quality.implementation_quality,
                    "educational_value": resource.quality.educational_value,
                    "relevance_score": resource.quality.relevance_score,
                    "overall_score": resource.quality.overall_score
                },
                "prerequisites": resource.prerequisites,
                "difficulty_level": resource.difficulty_level
            })
        
        educational_details = []
        for resource in self.state.educational_resources:
            educational_details.append({
                "title": resource.title,
                "url": resource.url,
                "resource_type": resource.resource_type,
                "description": resource.description,
                "quality_assessment": {
                    "academic_rigor": resource.quality.academic_rigor,
                    "implementation_quality": resource.quality.implementation_quality,
                    "educational_value": resource.quality.educational_value,
                    "relevance_score": resource.quality.relevance_score,
                    "overall_score": resource.quality.overall_score
                },
                "prerequisites": resource.prerequisites,
                "difficulty_level": resource.difficulty_level
            })
        
        # Get learning path details
        learning_path_details = None
        if self.state.integrated_learning_path:
            learning_path_details = {
                "topic": self.state.integrated_learning_path.topic,
                "sequence": self.state.integrated_learning_path.sequence,
                "estimated_time": self.state.integrated_learning_path.estimated_time,
                "learning_objectives": self.state.integrated_learning_path.learning_objectives,
                "resources": []
            }
            
            # Add detailed resource information to learning path
            for resource in self.state.integrated_learning_path.resources:
                learning_path_details["resources"].append({
                    "title": resource.title,
                    "url": resource.url,
                    "resource_type": resource.resource_type,
                    "description": resource.description,
                    "quality_assessment": {
                        "academic_rigor": resource.quality.academic_rigor,
                        "implementation_quality": resource.quality.implementation_quality,
                        "educational_value": resource.quality.educational_value,
                        "relevance_score": resource.quality.relevance_score,
                        "overall_score": resource.quality.overall_score
                    },
                    "prerequisites": resource.prerequisites,
                    "difficulty_level": resource.difficulty_level
                })
        
        return {
            "status": "partial_success",
            "research_topic": self.state.research_topic,
            "summary": {
                "total_resources": len(self.state.literature_resources) + 
                                 len(self.state.code_resources) + 
                                 len(self.state.educational_resources),
                "literature_count": len(self.state.literature_resources),
                "code_count": len(self.state.code_resources),
                "educational_count": len(self.state.educational_resources),
                "average_quality_score": self._calculate_average_quality(),
                "validation_passed": False,
                "validation_issues": validation_results["issues"]
            },
            "detailed_results": {
                "literature_resources": literature_details,
                "code_resources": code_details,
                "educational_resources": educational_details,
                "learning_path": learning_path_details
            },
            "metadata": {
                "parser_used": "ResearchDataParser",
                "quality_threshold": self.state.quality_threshold,
                "iterations_required": self.state.iterations + 1
            }
        }

    def _create_failure_report(self, error_message):
        """Create a failure report"""
        return {
            "status": "failed",
            "research_topic": self.state.research_topic,
            "error_message": error_message,
            "errors": self.state.errors,
            "partial_results": {
                "literature_found": len(self.state.literature_resources),
                "code_found": len(self.state.code_resources),
                "educational_found": len(self.state.educational_resources)
            },
            "parser_used": "ResearchDataParser"
        }

    def _save_detailed_results_to_file(self, result):
        """Save detailed results to both JSON and Markdown files for easy access"""
        import os
        import json
        from datetime import datetime

        # Create a directory for results if it doesn't exist
        results_dir = "research_results"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        # Create a unique filename based on the current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        base_filename = f"{self.state.research_topic}_{timestamp}"
        
        # Save JSON file
        json_filepath = os.path.join(results_dir, f"{base_filename}.json")
        with open(json_filepath, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Generate and save Markdown report
        markdown_content = self._generate_markdown_report(result)
        markdown_filepath = os.path.join(results_dir, f"{base_filename}.md")
        with open(markdown_filepath, 'w') as f:
            f.write(markdown_content)

        print(f"📊 Results saved:")
        print(f"   📋 JSON: {json_filepath}")
        print(f"   📝 Markdown: {markdown_filepath}")
        
        # Also print a summary to console
        print("\n" + "="*80)
        print("📖 RESEARCH SUMMARY")
        print("="*80)
        print(self._generate_console_summary(result))

    def _generate_markdown_report(self, result):
        """Generate a comprehensive markdown report from the research results"""
        
        # Header
        report = f"""# Research Report: {result['research_topic'].title()}

*Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*

---

## 📊 Executive Summary

**Status:** {result['status'].replace('_', ' ').title()}  
**Total Resources Found:** {result['summary']['total_resources']}  
**Average Quality Score:** {result['summary']['average_quality_score']:.2f}/5.0  
**Validation Status:** {'✅ Passed' if result['summary']['validation_passed'] else '❌ Failed'}

### Resource Breakdown
- 📚 **Literature Resources:** {result['summary']['literature_count']}
- 💻 **Code Resources:** {result['summary']['code_count']}  
- 🎓 **Educational Resources:** {result['summary']['educational_count']}

---

"""

        # Learning Path Section
        if result['detailed_results'].get('learning_path'):
            lp = result['detailed_results']['learning_path']
            report += f"""## 🛤️ Recommended Learning Path

**Topic:** {lp['topic']}  
**Estimated Time:** {lp['estimated_time']}

### Learning Objectives
"""
            for i, objective in enumerate(lp['learning_objectives'], 1):
                report += f"{i}. {objective}\n"
            
            report += f"""
### Learning Sequence
"""
            for i, step in enumerate(lp['sequence'], 1):
                report += f"{i}. **{step}**\n"
            
            report += "\n---\n\n"

        # Literature Resources
        if result['detailed_results']['literature_resources']:
            report += """## 📚 Academic Literature Resources

"""
            for i, resource in enumerate(result['detailed_results']['literature_resources'], 1):
                quality = resource['quality_assessment']
                report += f"""### {i}. {resource['title']}

**Type:** {resource['resource_type']}  
**URL:** [{resource['url']}]({resource['url']})  
**Difficulty:** {resource['difficulty_level']}

**Description:**  
{resource['description']}

**Quality Assessment:**
- 🎓 Academic Rigor: {quality['academic_rigor']}/5
- 🔧 Implementation Quality: {quality['implementation_quality']}/5  
- 📖 Educational Value: {quality['educational_value']}/5
- 🎯 Relevance Score: {quality['relevance_score']}/5
- ⭐ **Overall Score: {quality['overall_score']}/5**

**Prerequisites:**
"""
                for prereq in resource['prerequisites']:
                    report += f"- {prereq}\n"
                
                report += "\n---\n\n"

        # Code Resources
        if result['detailed_results']['code_resources']:
            report += """## 💻 Code Implementation Resources

"""
            for i, resource in enumerate(result['detailed_results']['code_resources'], 1):
                quality = resource['quality_assessment']
                report += f"""### {i}. {resource['title']}

**Type:** {resource['resource_type']}  
**URL:** [{resource['url']}]({resource['url']})  
**Difficulty:** {resource['difficulty_level']}

**Description:**  
{resource['description']}

**Quality Assessment:**
- 🎓 Academic Rigor: {quality['academic_rigor']}/5
- 🔧 Implementation Quality: {quality['implementation_quality']}/5  
- 📖 Educational Value: {quality['educational_value']}/5
- 🎯 Relevance Score: {quality['relevance_score']}/5
- ⭐ **Overall Score: {quality['overall_score']}/5**

**Prerequisites:**
"""
                for prereq in resource['prerequisites']:
                    report += f"- {prereq}\n"
                
                report += "\n---\n\n"

        # Educational Resources
        if result['detailed_results']['educational_resources']:
            report += """## 🎓 Educational Resources

"""
            for i, resource in enumerate(result['detailed_results']['educational_resources'], 1):
                quality = resource['quality_assessment']
                report += f"""### {i}. {resource['title']}

**Type:** {resource['resource_type']}  
**URL:** [{resource['url']}]({resource['url']})  
**Difficulty:** {resource['difficulty_level']}

**Description:**  
{resource['description']}

**Quality Assessment:**
- 🎓 Academic Rigor: {quality['academic_rigor']}/5
- 🔧 Implementation Quality: {quality['implementation_quality']}/5  
- 📖 Educational Value: {quality['educational_value']}/5
- 🎯 Relevance Score: {quality['relevance_score']}/5
- ⭐ **Overall Score: {quality['overall_score']}/5**

**Prerequisites:**
"""
                for prereq in resource['prerequisites']:
                    report += f"- {prereq}\n"
                
                report += "\n---\n\n"

        # Metadata
        report += f"""## 🔧 Technical Details

**Parser Used:** {result['metadata']['parser_used']}  
**Quality Threshold:** {result['metadata']['quality_threshold']}  
**Iterations Required:** {result['metadata']['iterations_required']}

---

*This report was automatically generated by the Preclinical Neuroscience Research Platform*
"""

        return report

    def _generate_console_summary(self, result):
        """Generate a concise summary for console output"""
        summary = f"""
🔬 Research Topic: {result['research_topic'].title()}
📊 Status: {result['status'].replace('_', ' ').title()}
📈 Quality Score: {result['summary']['average_quality_score']:.2f}/5.0

📚 Resources Found:
   Literature: {result['summary']['literature_count']} papers
   Code: {result['summary']['code_count']} repositories  
   Educational: {result['summary']['educational_count']} resources
   Total: {result['summary']['total_resources']} resources

🎯 Top Literature Findings:"""
        
        # Show top 3 literature resources
        lit_resources = result['detailed_results']['literature_resources'][:3]
        for i, resource in enumerate(lit_resources, 1):
            summary += f"""
   {i}. {resource['title'][:60]}{'...' if len(resource['title']) > 60 else ''}
      Score: {resource['quality_assessment']['overall_score']}/5 | {resource['difficulty_level']}"""

        summary += f"""

💻 Top Code Resources:"""
        
        # Show top 3 code resources
        code_resources = result['detailed_results']['code_resources'][:3]
        for i, resource in enumerate(code_resources, 1):
            summary += f"""
   {i}. {resource['title'][:60]}{'...' if len(resource['title']) > 60 else ''}
      Score: {resource['quality_assessment']['overall_score']}/5 | {resource['difficulty_level']}"""

        if result['detailed_results'].get('learning_path'):
            lp = result['detailed_results']['learning_path']
            summary += f"""

🛤️ Learning Path: {lp['estimated_time']} ({len(lp['learning_objectives'])} objectives)
"""

        return summary

# ================================
# USAGE EXAMPLE
# ================================

def main():
    """Example usage of the enhanced preclinical research flow"""
    
    # Initialize flow with research topic
    research_flow = PreclinicalResearchFlow(
        research_topic="Protein-protein interaction network analysis for neurodegeneration target discovery",
        quality_threshold=3.5
    )
    
    # Execute the research flow
    print("Starting enhanced preclinical neuroscience research flow...")
    print("Now using ResearchDataParser for robust parsing...")
    result = research_flow.kickoff()
    
    print("\nResearch Flow Completed!")
    print("Final Result:")
    print(json.dumps(result, indent=2, default=str))
    
    # Access final state
    print("\nFinal State Summary:")
    print(f"- Literature Resources: {len(research_flow.state.literature_resources)}")
    print(f"- Code Resources: {len(research_flow.state.code_resources)}")
    print(f"- Educational Resources: {len(research_flow.state.educational_resources)}")
    print(f"- Validation Passed: {research_flow.state.validation_passed}")
    print(f"- Iterations Required: {research_flow.state.iterations + 1}")
    print("- Parser Used: ResearchDataParser (robust fallback)")

if __name__ == "__main__":
    main()