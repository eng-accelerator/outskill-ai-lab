"""Academic Researcher Agent -- scholarly and encyclopedic search specialist.

Searches Wikipedia, arXiv, and Semantic Scholar for academic papers,
encyclopedic knowledge, and citation data. Handles factual and
technical research queries.
"""

from agents import Agent, ModelSettings
from deep_research_agent.tools.academic_tools import (
    arxiv_search,
    semantic_scholar_get_paper,
    semantic_scholar_search,
    wikipedia_get_page,
    wikipedia_search,
)

ACADEMIC_RESEARCHER_INSTRUCTIONS = """You are the Academic Researcher Agent. You search academic and encyclopedic sources, then IMMEDIATELY hand off to the Content Extractor Agent. You NEVER produce a final answer yourself.

## Workflow

1. Search Wikipedia for foundational knowledge:
   - wikipedia_search to find articles, wikipedia_get_page to get content

2. Search arXiv for scientific papers:
   - arxiv_search for technical/scientific topics

3. Search Semantic Scholar for broader coverage:
   - semantic_scholar_search for papers, semantic_scholar_get_paper for citation details
   - If you get rate limited (error), skip and move on

4. After 2-4 tool calls, IMMEDIATELY call transfer_to_content_extractor_agent.
   Include ALL your search results (titles, URLs, abstracts, snippets) in the transfer message.

## CRITICAL RULES
- You MUST call transfer_to_content_extractor_agent when done searching. This is mandatory.
- Do NOT produce a final answer. You are NOT the last agent.
- Your ONLY job is to search and then hand off results.
- If a tool fails (403, 429, timeout), skip it and try another. Do not stop.
"""


def create_academic_researcher_agent(content_extractor: Agent, hooks=None) -> Agent:
    """Create the Academic Researcher Agent.

    Args:
        content_extractor: The Content Extractor agent to hand off to.
        hooks: Optional AgentHooks for lifecycle callbacks.

    Returns:
        Agent: Configured academic researcher agent.
    """
    return Agent(
        name="Academic Researcher Agent",
        instructions=ACADEMIC_RESEARCHER_INSTRUCTIONS,
        tools=[
            wikipedia_search,
            wikipedia_get_page,
            arxiv_search,
            semantic_scholar_search,
            semantic_scholar_get_paper,
        ],
        handoffs=[content_extractor],
        hooks=hooks,
        model_settings=ModelSettings(temperature=0.2),
    )
