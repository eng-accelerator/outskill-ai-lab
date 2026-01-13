from agents import Agent, ModelSettings


def create_query_generator_agent(retriever, hooks=None):
    return Agent(
        name="QueryGenerator",
        model="gpt-4o",
        instructions="""You are a search query optimization expert. Your role is to:
1. Take the research plan from the Planner
2. Generate 2-3 specific, targeted search queries for each sub-topic
3. Ensure queries are optimized for web search

Create queries that will retrieve comprehensive and relevant information.
Then hand off to the Retriever to fetch search results.""",
        handoffs=[retriever],
        hooks=hooks,
        model_settings=ModelSettings(timeout=60),
    )
