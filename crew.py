from crewai import Agent, Crew, Task, Process, LLM
from crewai.project import CrewBase, agent, task, crew
from typing import List
import os
from dotenv import load_dotenv

from state_management import LearningPath, ResearchResource, LiteratureResources, CodeResources, EducationalResources
from tools import academic_search_tool, code_search_tool, educational_search_tool, research_tool, firecrawl_extract_tool

# Load environment variables
load_dotenv()
# ================================
# CREW DEFINITION
# ================================

@CrewBase
class PreclinicalNeuroscienceResearchCrew:
    """A specialized crew for conducting comprehensive research in preclinical neuroscience,
    discovering academic literature, code implementations, and educational resources"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        # Initialize LLM
        self.llm = LLM(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY")
        )

    @agent
    def academic_literature_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['academic_literature_specialist'],
            tools=[academic_search_tool, firecrawl_extract_tool],
            llm=self.llm,
            verbose=True
        )

    @agent
    def code_implementation_hunter(self) -> Agent:
        return Agent(
            config=self.agents_config['code_implementation_hunter'],
            tools=[code_search_tool, firecrawl_extract_tool],
            llm=self.llm,
            verbose=True
        )

    @agent
    def educational_content_curator(self) -> Agent:
        return Agent(
            config=self.agents_config['educational_content_curator'],
            tools=[educational_search_tool, firecrawl_extract_tool],
            llm=self.llm,
            verbose=True
        )

    @agent
    def knowledge_synthesizer_orchestrator(self) -> Agent:
        return Agent(
            config=self.agents_config['knowledge_synthesizer_orchestrator'],
            tools=[research_tool, firecrawl_extract_tool],
            llm=self.llm,
            verbose=True
        )

    @task
    def literature_discovery_task(self) -> Task:
        return Task(
            config=self.tasks_config['literature_discovery_task'],
            agent=self.academic_literature_specialist(),
            tools=[academic_search_tool, firecrawl_extract_tool],
            output_pydantic=LiteratureResources
        )

    @task
    def code_discovery_task(self) -> Task:
        return Task(
            config=self.tasks_config['code_discovery_task'],
            agent=self.code_implementation_hunter(),
            tools=[code_search_tool, firecrawl_extract_tool],
            output_pydantic=CodeResources
        )

    @task
    def educational_curation_task(self) -> Task:
        return Task(
            config=self.tasks_config['educational_curation_task'],
            agent=self.educational_content_curator(),
            tools=[educational_search_tool, firecrawl_extract_tool],
            output_pydantic=EducationalResources
        )

    @task
    def knowledge_synthesis_task(self) -> Task:
        return Task(
            config=self.tasks_config['knowledge_synthesis_task'],
            agent=self.knowledge_synthesizer_orchestrator(),
            tools=[research_tool, firecrawl_extract_tool],
            output_pydantic=LearningPath
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=False,  # Temporarily disabled due to ChromaDB issue
            verbose=True
        )
