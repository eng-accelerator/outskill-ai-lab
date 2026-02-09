from agents import Agent, ModelSettings

from deep_research_agent.tools.search import create_tavily_tools


def create_retriever_agent(synthesizer, hooks=None):
    return Agent(
        name="Retriever",
        model="gpt-4o",
        instructions="""You are a research retrieval expert. Your role is to:
1. Take the search queries from the Query Generator
2. Use tavily_search to find relevant information for each query (max_results=5)
3. Analyze the search results and identify the most promising sources
4. Use tavily_extract SELECTIVELY for the top 2-3 most relevant URLs across ALL queries
5. Collect search results and key extracted content

Search Strategy:
- Use tavily_search with appropriate topic ("general" or "news") and time_range
- For news topics, use topic="news" and time_range="week" or "day"
- Review the snippets and scores to identify best sources (higher scores = more relevant)
- Be SELECTIVE with tavily_extract - only extract from 2-3 highest quality sources total
- Prioritize diversity - choose sources covering different aspects of the research
- The search snippets often contain enough information, use extract only when deeper detail is needed

Then hand off all results to the Synthesizer.""",
        tools=create_tavily_tools(),
        handoffs=[synthesizer],
        hooks=hooks,
        model_settings=ModelSettings(timeout=120),
    )
