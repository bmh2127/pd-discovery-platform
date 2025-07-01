# corrected_pd_crew.py

from crewai import Agent, Crew, Task, Process, LLM
from crewai.project import CrewBase, agent, task, crew
from typing import List
import os
from dotenv import load_dotenv

from ..state_management import PDResearchState, NetworkAnalysisResult, ParadigmChallengeInsights, ValidationReport
from ..tools import (
    build_dopaminergic_network_tool,
    cross_validate_interactions_tool,
    batch_resolve_proteins_tool,
    get_research_overview_tool,
    execute_pd_workflow_tool
)

# Load environment variables
load_dotenv()

# ================================
# CORRECTED CREW DEFINITION
# ================================

@CrewBase
class PDParadigmChallengeCrew:
    """
    ✅ CORRECTED: A specialized crew for challenging the α-synuclein paradigm 
    in Parkinson's disease research through systematic dopaminergic network 
    discovery and cross-database validation
    """

    # ✅ Corrected: Use string paths, not 'config/' prefix
    agents_config = '../config/agents.yaml'
    tasks_config = '../config/tasks.yaml'

    def __init__(self):
        # ✅ Initialize LLM with error handling
        try:
            self.llm = LLM(
                model="gpt-4o-mini",
                api_key=os.getenv("OPENAI_API_KEY")
            )
        except Exception as e:
            print(f"Warning: LLM initialization failed: {e}")
            self.llm = None

    @agent
    def dopaminergic_network_specialist(self) -> Agent:
        """✅ Enhanced with better error handling and tool validation"""
        tools = [
            build_dopaminergic_network_tool,
            cross_validate_interactions_tool,
            get_research_overview_tool
        ]
        
        # ✅ Validate tools are callable
        validated_tools = [tool for tool in tools if callable(tool)]
        
        return Agent(
            config=self.agents_config['dopaminergic_network_specialist'],
            tools=validated_tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=False,  # ✅ Prevent unnecessary delegation
            max_iter=3,  # ✅ Limit iterations for reliability
            memory=True  # ✅ Enable memory for better context
        )

    @agent
    def cross_database_validator(self) -> Agent:
        """✅ Enhanced validator agent"""
        tools = [
            cross_validate_interactions_tool,
            batch_resolve_proteins_tool,
            get_research_overview_tool
        ]
        
        validated_tools = [tool for tool in tools if callable(tool)]
        
        return Agent(
            config=self.agents_config['cross_database_validator'],
            tools=validated_tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            memory=True
        )

    @agent
    def paradigm_challenge_analyst(self) -> Agent:
        """✅ Enhanced paradigm analyst"""
        tools = [
            build_dopaminergic_network_tool,
            cross_validate_interactions_tool,
            execute_pd_workflow_tool
        ]
        
        validated_tools = [tool for tool in tools if callable(tool)]
        
        return Agent(
            config=self.agents_config['paradigm_challenge_analyst'],
            tools=validated_tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            memory=True
        )

    @agent
    def research_orchestrator(self) -> Agent:
        """✅ Enhanced research orchestrator"""
        tools = [
            execute_pd_workflow_tool,
            get_research_overview_tool,
            batch_resolve_proteins_tool
        ]
        
        validated_tools = [tool for tool in tools if callable(tool)]
        
        return Agent(
            config=self.agents_config['research_orchestrator'],
            tools=validated_tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            memory=True
        )

    @task
    def systematic_network_discovery_task(self) -> Task:
        """✅ Enhanced with better context and dependencies"""
        return Task(
            config=self.tasks_config['systematic_network_discovery_task'],
            agent=self.dopaminergic_network_specialist(),
            tools=[
                build_dopaminergic_network_tool,
                get_research_overview_tool
            ],
            output_pydantic=NetworkAnalysisResult,
            context=[],  # ✅ No dependencies for first task
            async_execution=False  # ✅ Ensure sequential execution
        )

    @task
    def cross_database_validation_task(self) -> Task:
        """✅ Enhanced with proper dependencies"""
        return Task(
            config=self.tasks_config['cross_database_validation_task'],
            agent=self.cross_database_validator(),
            tools=[
                cross_validate_interactions_tool,
                batch_resolve_proteins_tool
            ],
            output_pydantic=ValidationReport,
            context=[self.systematic_network_discovery_task()],  # ✅ Depends on network task
            async_execution=False
        )

    @task
    def paradigm_challenge_analysis_task(self) -> Task:
        """✅ Enhanced with multiple dependencies"""
        return Task(
            config=self.tasks_config['paradigm_challenge_analysis_task'],
            agent=self.paradigm_challenge_analyst(),
            tools=[
                build_dopaminergic_network_tool,
                cross_validate_interactions_tool
            ],
            output_pydantic=ParadigmChallengeInsights,
            context=[
                self.systematic_network_discovery_task(),
                self.cross_database_validation_task()
            ],  # ✅ Depends on both previous tasks
            async_execution=False
        )

    @task
    def research_synthesis_task(self) -> Task:
        """✅ Enhanced synthesis with all dependencies"""
        return Task(
            config=self.tasks_config['research_synthesis_task'],
            agent=self.research_orchestrator(),
            tools=[
                execute_pd_workflow_tool,
                get_research_overview_tool
            ],
            output_pydantic=PDResearchState,
            context=[
                self.systematic_network_discovery_task(),
                self.cross_database_validation_task(),
                self.paradigm_challenge_analysis_task()
            ],  # ✅ Depends on all previous tasks
            async_execution=False
        )

    @crew
    def crew(self) -> Crew:
        """✅ Enhanced crew with proper configuration"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,  # ✅ Ensure sequential execution
            memory=True,  # ✅ Enable crew memory
            verbose=True,
            max_rpm=10,  # ✅ Rate limiting for API calls
            language="en",  # ✅ Explicit language setting
            step_callback=self._step_callback,  # ✅ Add step callback for monitoring
            manager_llm=self.llm,  # ✅ Use same LLM for manager
            embedder={
                "provider": "openai",
                "config": {
                    "model": "text-embedding-3-small"
                }
            }  # ✅ Configure embeddings for memory
        )

    def _step_callback(self, step_output):
        """✅ Step callback for monitoring crew execution"""
        try:
            if hasattr(step_output, 'raw'):
                print(f"🔄 Step completed: {step_output.raw[:100]}...")
            else:
                print(f"🔄 Step completed: {str(step_output)[:100]}...")
        except Exception as e:
            print(f"🔄 Step completed (callback error: {e})")

    def validate_setup(self) -> bool:
        """✅ Validate crew setup before execution"""
        try:
            # Check LLM
            if not self.llm:
                print("❌ LLM not initialized")
                return False
            
            # Check agents
            if len(self.agents) != 4:
                print(f"❌ Expected 4 agents, got {len(self.agents)}")
                return False
            
            # Check tasks
            if len(self.tasks) != 4:
                print(f"❌ Expected 4 tasks, got {len(self.tasks)}")
                return False
            
            # Check tools
            for agent in self.agents:
                if not agent.tools:
                    print(f"❌ Agent {agent.role} has no tools")
                    return False
            
            print("✅ Crew setup validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Crew validation failed: {e}")
            return False
