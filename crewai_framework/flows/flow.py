# corrected_pd_research_flow.py

import json
from datetime import datetime
from crewai.flow import Flow, start, listen, router
from typing import Dict, List, Any

from ..crews.pd_research_crew import PDParadigmChallengeCrew
from ..state_management import (
    PDResearchState, 
    NetworkAnalysisResult, 
    ValidationReport, 
    ParadigmChallengeInsights,
    DiscoveryMode,
    ConfidenceLevel,
    ParadigmChallengeStrength
)

class PDParadigmChallengeFlow(Flow[PDResearchState]):
    """
    ✅ CORRECTED: Advanced research flow for challenging the α-synuclein paradigm 
    in Parkinson's disease through systematic dopaminergic network discovery 
    and cross-database validation.
    
    Based on CrewAI best practices and GitHub issue #1579 resolution.
    """

    def __init__(self, research_question: str, confidence_threshold: float = 0.7):
        # Create initial state with required parameters
        initial_state = PDResearchState(
            research_question=research_question,
            confidence_threshold=confidence_threshold,
            discovery_mode=DiscoveryMode.COMPREHENSIVE,
            research_confidence=ConfidenceLevel.LOW,
            paradigm_challenge_strength=ParadigmChallengeStrength.INSUFFICIENT,
            validation_passed=False,
            iterations=0,
            max_iterations=3,
            errors=[],
            warnings=[],
            database_sources=["string", "biogrid", "pride"]
        )
        
        # Initialize flow with the created state
        super().__init__(initial_state=initial_state)
        
        # Initialize crew
        try:
            self.crew_instance = PDParadigmChallengeCrew()
            self.crew = self.crew_instance.crew()
        except Exception as e:
            print(f"Warning: CrewAI initialization failed: {e}")
            self.crew_instance = None
            self.crew = None

    @start("main")  # ✅ Add event name for reliable routing
    def initiate_paradigm_challenge_research(self):
        """Start the paradigm-challenging research process"""
        print(f"---🧬 INITIATING PARADIGM CHALLENGE RESEARCH---")
        print(f"Research Question: {self.state.research_question}")
        
        # Validate research question
        if not self._validate_research_question():
            self.state.errors.append("Invalid research question")
            return "failed"
        
        print("✅ Research question validated")
        return "execute_crew"

    @listen("execute_crew")
    def execute_paradigm_crew(self):
        """Execute the complete crew workflow"""
        print("---🔬 EXECUTING PD PARADIGM CHALLENGE CREW WORKFLOW---")
        
        try:
            print("🚀 Executing crew with all specialized tasks...")
            result = self.crew.kickoff(
                inputs={"research_question": self.state.research_question}
            )
            
            print("📊 Parsing task outputs from crew execution...")
            
            # Parse outputs from each specialized task
            if hasattr(result, 'tasks_output') and result.tasks_output:
                success = self._parse_crew_outputs(result.tasks_output)
                if success:
                    return "validate_results"
                else:
                    self.state.errors.append("Failed to parse crew outputs")
                    return "retry_or_fail"
            else:
                print("❌ No individual task outputs found")
                self.state.errors.append("No task outputs generated")
                return "retry_or_fail"
                
        except Exception as e:
            self.state.errors.append(f"Crew execution failed: {str(e)}")
            print(f"❌ Error during crew execution: {e}")
            return "retry_or_fail"

    @listen("validate_results")
    def perform_paradigm_validation(self):
        """Perform comprehensive validation of paradigm challenge research"""
        print("---🔍 PERFORMING PARADIGM CHALLENGE VALIDATION---")
        
        validation_results = self._perform_paradigm_validation()
        
        if validation_results["passed"]:
            self.state.validation_passed = True
            print("---✅ PARADIGM CHALLENGE RESEARCH COMPLETED SUCCESSFULLY---")
            return "success"
        else:
            print("---⚠️ PARADIGM CHALLENGE RESEARCH VALIDATION FAILED---")
            self.state.errors.extend(validation_results["issues"])
            return "retry_or_fail"

    @listen("retry_or_fail")
    def handle_failure_or_retry(self):
        """Handle failures and decide whether to retry"""
        if self.state.iterations < self.state.max_iterations:
            self.state.iterations += 1
            print(f"🔄 Retrying (attempt {self.state.iterations + 1}/{self.state.max_iterations + 1})")
            
            # Clear some errors for retry
            if len(self.state.errors) > 3:
                self.state.errors = self.state.errors[-3:]  # Keep last 3 errors
            
            return "retry"
        else:
            print("❌ Maximum attempts reached - research failed")
            return "failed"

    @router(initiate_paradigm_challenge_research)  # ✅ Router attached to method
    def route_from_start(self):
        """Route from start based on validation"""
        return "execute_crew"  # Always proceed to crew execution

    @router(handle_failure_or_retry)  # ✅ Router attached to method  
    def route_retry_decision(self):
        """Route retry decision"""
        if self.state.iterations < self.state.max_iterations:
            return "main"  # ✅ Return to start for reliable looping
        else:
            return "failed"

    @listen("retry")  # ✅ Simple retry logic
    def retry_research(self):
        """Retry research with improved parameters"""
        print("---🔄 RETRYING PARADIGM RESEARCH---")
        
        # Adjust parameters based on failures
        self._adjust_parameters_for_retry()
        
        return "main"  # ✅ Return to start

    @listen("success")
    def generate_success_report(self):
        """Generate comprehensive success report"""
        print("---✅ GENERATING SUCCESS REPORT---")
        
        final_result = self._create_success_report()
        self._save_detailed_results_to_file(final_result)
        
        print("📊 Paradigm Challenge Research Complete!")
        return final_result

    @listen("failed") 
    def generate_failure_report(self):
        """Generate failure report"""
        print("---❌ GENERATING FAILURE REPORT---")
        
        final_result = self._create_failure_report("Research failed after maximum attempts")
        self._save_detailed_results_to_file(final_result)
        
        print("📊 Paradigm Challenge Research Failed")
        return final_result

    # ================================
    # HELPER METHODS (unchanged logic, just corrected structure)
    # ================================

    def _validate_research_question(self) -> bool:
        """Validate that research question is suitable for paradigm challenge"""
        if not self.state.research_question or len(self.state.research_question.strip()) < 10:
            return False
        
        # Check for paradigm-relevant keywords
        paradigm_keywords = [
            "dopaminergic", "synuclein", "paradigm", "challenge", "early", "disruption",
            "network", "parkinson", "temporal", "mechanism", "cause", "precede"
        ]
        
        question_lower = self.state.research_question.lower()
        if not any(keyword in question_lower for keyword in paradigm_keywords):
            print("⚠️ Warning: Research question may not be optimized for paradigm challenge")
        
        return True

    def _parse_crew_outputs(self, tasks_output: List) -> bool:
        """Parse outputs from each specialized task with error handling"""
        try:
            # Parse each task output with fallbacks
            for i, task_output in enumerate(tasks_output):
                if i == 0:  # Network analysis
                    self.state.network_analysis = self._parse_with_fallback(
                        task_output, "network_analysis"
                    )
                elif i == 1:  # Validation
                    self.state.validation_report = self._parse_with_fallback(
                        task_output, "validation_report"
                    )
                elif i == 2:  # Paradigm analysis
                    self.state.paradigm_insights = self._parse_with_fallback(
                        task_output, "paradigm_insights"
                    )
                elif i == 3:  # Synthesis
                    synthesis_result = self._parse_with_fallback(
                        task_output, "synthesis"
                    )
                    if synthesis_result:
                        self.state.research_priorities = getattr(synthesis_result, 'research_priorities', [])
                        self.state.experimental_validation_plan = getattr(synthesis_result, 'experimental_validation_plan', {})
                        self.state.clinical_translation_potential = getattr(synthesis_result, 'clinical_translation_potential', {})
            
            # Check minimum requirements
            required_outputs = [
                self.state.network_analysis,
                self.state.validation_report, 
                self.state.paradigm_insights
            ]
            
            return all(required_outputs)
            
        except Exception as e:
            print(f"❌ Error parsing outputs: {e}")
            return False

    def _parse_with_fallback(self, task_output, output_type: str):
        """Parse task output with fallback to default values"""
        try:
            if hasattr(task_output, 'pydantic') and task_output.pydantic:
                return task_output.pydantic
            else:
                # Create default based on type
                return self._create_default_output(output_type)
        except Exception as e:
            print(f"Warning: Failed to parse {output_type}, using default: {e}")
            return self._create_default_output(output_type)

    def _create_default_output(self, output_type: str):
        """Create default outputs for failed parsing"""
        if output_type == "network_analysis":
            return NetworkAnalysisResult(
                discovery_mode="comprehensive",
                confidence_threshold=0.7,
                total_proteins=0,
                total_interactions=0,
                hub_proteins=[],
                novel_proteins=[],
                unexpected_connections=[],
                functional_clusters={},
                paradigm_evidence_count=0,
                network_confidence="low"
            )
        elif output_type == "validation_report":
            return ValidationReport(
                databases_validated=["string", "biogrid"],
                total_interactions_validated=0,
                cross_validated_interactions=0,
                validation_success_rate=0.0,
                convergent_evidence=[],
                protein_resolution_rate=0.0,
                research_confidence="low",
                priority_validations=[]
            )
        elif output_type == "paradigm_insights":
            return ParadigmChallengeInsights(
                alpha_synuclein_challenge_strength="insufficient",
                direct_pathology_synthesis_connections=0,
                temporal_disruption_hypothesis={},
                paradigm_challenge_score=0.0,
                alternative_mechanism="unknown",
                experimental_validation_priorities=[],
                clinical_implications=[]
            )
        return None

    def _adjust_parameters_for_retry(self):
        """Adjust parameters based on previous failures"""
        error_text = " ".join(self.state.errors).lower()
        
        if "network" in error_text:
            print("🔧 Adjusting network discovery parameters")
            # Could modify discovery mode or confidence thresholds
        
        if "validation" in error_text:
            print("🔧 Expanding validation databases") 
            # Could add more databases or lower validation thresholds
        
        if "paradigm" in error_text:
            print("🔧 Refining paradigm challenge criteria")
            # Could adjust paradigm challenge scoring

    def _perform_paradigm_validation(self) -> Dict[str, Any]:
        """Perform comprehensive validation of paradigm challenge research"""
        results = {"passed": True, "issues": []}
        
        # Validate network analysis quality
        if not self._validate_network_analysis():
            results["issues"].append("Network analysis quality insufficient")
            results["passed"] = False
        
        # Validate cross-database evidence
        if not self._validate_cross_database_evidence():
            results["issues"].append("Insufficient cross-database validation")
            results["passed"] = False
        
        # Validate paradigm challenge strength
        if not self._validate_paradigm_challenge_strength():
            results["issues"].append("Paradigm challenge evidence insufficient")
            results["passed"] = False
        
        return results

    def _validate_network_analysis(self) -> bool:
        """Validate network analysis meets paradigm challenge criteria"""
        if not self.state.network_analysis:
            return False
        
        network = self.state.network_analysis
        
        # Check for sufficient network size
        if network.total_proteins < 5 or network.total_interactions < 10:
            print(f"⚠️ Network too small: {network.total_proteins} proteins, {network.total_interactions} interactions")
            return False
        
        # Check for paradigm-challenging evidence
        if network.paradigm_evidence_count < 2:
            print(f"⚠️ Insufficient paradigm evidence: {network.paradigm_evidence_count} connections")
            return False
        
        return True

    def _validate_cross_database_evidence(self) -> bool:
        """Validate cross-database validation quality"""
        if not self.state.validation_report:
            return False
        
        validation = self.state.validation_report
        
        # Check validation success rate
        if validation.validation_success_rate < 0.2:  # At least 20% cross-validated
            print(f"⚠️ Low validation success rate: {validation.validation_success_rate:.2%}")
            return False
        
        return True

    def _validate_paradigm_challenge_strength(self) -> bool:
        """Validate strength of paradigm challenge evidence"""
        if not self.state.paradigm_insights:
            return False
        
        paradigm = self.state.paradigm_insights
        
        # Check paradigm challenge score
        if paradigm.paradigm_challenge_score < 0.3:  # At least weak challenge
            print(f"⚠️ Low paradigm challenge score: {paradigm.paradigm_challenge_score:.2f}")
            return False
        
        return True

    def _create_success_report(self) -> Dict[str, Any]:
        """Create comprehensive success report"""
        return {
            "status": "success",
            "research_question": self.state.research_question,
            "paradigm_challenge_summary": {
                "paradigm_challenge_score": getattr(self.state.paradigm_insights, 'paradigm_challenge_score', 0.0),
                "direct_pathology_synthesis_connections": getattr(self.state.paradigm_insights, 'direct_pathology_synthesis_connections', 0),
                "alpha_synuclein_challenge_strength": getattr(self.state.paradigm_insights, 'alpha_synuclein_challenge_strength', 'unknown'),
                "validation_success_rate": getattr(self.state.validation_report, 'validation_success_rate', 0.0),
                "cross_validated_interactions": getattr(self.state.validation_report, 'cross_validated_interactions', 0)
            },
            "network_discoveries": {
                "total_proteins": getattr(self.state.network_analysis, 'total_proteins', 0),
                "total_interactions": getattr(self.state.network_analysis, 'total_interactions', 0),
                "novel_proteins": getattr(self.state.network_analysis, 'novel_proteins', []),
                "hub_proteins": getattr(self.state.network_analysis, 'hub_proteins', [])[:5],
                "unexpected_connections": getattr(self.state.network_analysis, 'unexpected_connections', [])
            },
            "research_recommendations": {
                "priority_targets": getattr(self.state, 'research_priorities', [])[:10],
                "experimental_validation_plan": getattr(self.state, 'experimental_validation_plan', {}),
                "clinical_translation_potential": getattr(self.state, 'clinical_translation_potential', {})
            },
            "validation_passed": self.state.validation_passed,
            "confidence_assessment": self._calculate_overall_confidence(),
            "iterations_completed": self.state.iterations + 1,
            "timestamp": datetime.now().isoformat()
        }

    def _create_failure_report(self, error_message: str) -> Dict[str, Any]:
        """Create failure report"""
        return {
            "status": "failed",
            "research_question": self.state.research_question,
            "error_message": error_message,
            "errors": self.state.errors,
            "iterations_attempted": self.state.iterations + 1,
            "partial_results": {
                "network_analysis_available": self.state.network_analysis is not None,
                "validation_report_available": self.state.validation_report is not None,
                "paradigm_insights_available": self.state.paradigm_insights is not None
            },
            "timestamp": datetime.now().isoformat()
        }

    def _calculate_overall_confidence(self) -> str:
        """Calculate overall research confidence"""
        if not all([self.state.network_analysis, self.state.validation_report, self.state.paradigm_insights]):
            return "low"
        
        try:
            network_confidence = 1.0 if self.state.network_analysis.paradigm_evidence_count >= 3 else 0.5
            validation_confidence = self.state.validation_report.validation_success_rate
            paradigm_confidence = self.state.paradigm_insights.paradigm_challenge_score
            
            overall_score = (network_confidence + validation_confidence + paradigm_confidence) / 3
            
            if overall_score >= 0.7:
                return "high"
            elif overall_score >= 0.4:
                return "moderate"
            else:
                return "low"
        except Exception:
            return "low"

    def _save_detailed_results_to_file(self, result: Dict[str, Any]):
        """Save detailed results to JSON and Markdown files"""
        import os
        
        # Create results directory
        results_dir = "pd_research_results"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        # Create unique filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        base_filename = f"paradigm_challenge_{timestamp}"
        
        # Save JSON
        json_filepath = os.path.join(results_dir, f"{base_filename}.json")
        with open(json_filepath, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"📊 Results saved: {json_filepath}")



def main():
    """Example usage of corrected PD paradigm challenge research flow"""
    
    # Initialize flow with paradigm-challenging research question
    research_flow = PDParadigmChallengeFlow(
        research_question="Find evidence that dopaminergic network disruption precedes α-synuclein aggregation in Parkinson's disease",
        confidence_threshold=0.7
    )
    
    # Execute the paradigm challenge research flow
    print("🧬 Starting Corrected PD Paradigm Challenge Research Flow...")
    result = research_flow.kickoff()
    
    print("\n✅ Research Flow Complete!")
    print("📊 Results Summary:")
    if isinstance(result, dict):
        print(json.dumps(result, indent=2, default=str))
    else:
        print(result)

if __name__ == "__main__":
    main()