"""Research Planner Agent -- decomposes queries and routes to researchers.

The entry point of the research pipeline. Analyzes the research query,
creates a structured research plan with sub-questions, and routes to
the appropriate specialist researcher agents.
"""

from agents import Agent, ModelSettings
from deep_research_agent.guardrails.input_validation import \
    research_input_guardrail
from deep_research_agent.tools.web_search_tools import tavily_web_search

RESEARCH_PLANNER_INSTRUCTIONS = """You are the Research Planner Agent. You MUST plan the research and then IMMEDIATELY hand off to a researcher agent using one of the transfer tools. You NEVER produce a final answer yourself.

## Workflow

1. Analyze the research query to classify it:
   - factual/encyclopedic -> route to Academic Researcher Agent
   - current events/trends -> route to News Researcher Agent
   - general/comparison/how-to -> route to Web Researcher Agent
   - technical/programming -> route to News Researcher Agent (has GitHub + StackExchange)
   - scientific/medical -> route to Academic Researcher Agent

2. Decompose the query into 3-5 sub-questions.

3. Optionally do ONE quick tavily_web_search for orientation.

4. IMMEDIATELY call one of these transfer tools:
   - transfer_to_web_researcher_agent
   - transfer_to_academic_researcher_agent
   - transfer_to_news_researcher_agent

   In your transfer message, include the research plan: query, sub-questions, and strategy.

## CRITICAL RULES
- You MUST call a transfer tool. Do NOT just describe what you would do.
- You are NOT the final agent. You CANNOT produce the research report.
- After your optional search, your VERY NEXT action must be calling a transfer tool.
- If you output text without calling a transfer tool, the pipeline will fail.
"""


def create_research_planner_agent(
    web_researcher: Agent,
    academic_researcher: Agent,
    news_researcher: Agent,
    hooks=None,
) -> Agent:
    """Create the Research Planner Agent with routing to researchers.

    Args:
        web_researcher: The Web Researcher agent for general web search.
        academic_researcher: The Academic Researcher agent for scholarly search.
        news_researcher: The News Researcher agent for news/community search.
        hooks: Optional AgentHooks for lifecycle callbacks.

    Returns:
        Agent: Configured research planner agent.
    """
    return Agent(
        name="Research Planner Agent",
        instructions=RESEARCH_PLANNER_INSTRUCTIONS,
        tools=[tavily_web_search],
        handoffs=[web_researcher, academic_researcher, news_researcher],
        input_guardrails=[research_input_guardrail],
        hooks=hooks,
        model_settings=ModelSettings(temperature=0.3),
    )
