from agents import Agent, ModelSettings
from deep_research_agent.tools.citation_formatter import create_citation_tool


def create_writer_agent(hooks=None):
    return Agent(
        name="Writer",
        model="gpt-4o",
        instructions="""You are a research report writer. Your role is to:
1. Take the synthesized information from the Synthesizer
2. Create a comprehensive research report with:
   - Executive Summary
   - Main Findings (organized by topic)
   - Key Insights
   - Conclusion
3. Use proper citations throughout [using the format_citation tool]
4. Ensure professional formatting in Markdown

Create a well-structured, comprehensive research report.""",
        tools=[create_citation_tool()],
        hooks=hooks,
        model_settings=ModelSettings(timeout=90),
    )
