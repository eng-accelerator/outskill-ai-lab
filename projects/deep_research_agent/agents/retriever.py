import agents as agents_sdk


def create_retriever_agent(synthesizer, hooks=None):
    return agents_sdk.Agent(
        name="Retriever",
        model="gpt-4o",
        instructions="""You are a research retrieval expert. Your role is to:
1. Take the search queries from the Query Generator
2. Use the web_search tool to find relevant information
3. Execute searches for all queries
4. Collect all search results

Use the web search tool to gather information from credible sources.
Then hand off all results to the Synthesizer.""",
        tools=[agents_sdk.WebSearchTool()],
        handoffs=[synthesizer],
        hooks=hooks,
        model_settings=agents_sdk.ModelSettings(timeout=120),
    )
