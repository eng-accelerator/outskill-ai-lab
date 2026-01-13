from agents import Agent, ModelSettings


def create_synthesizer_agent(writer, hooks=None):
    return Agent(
        name="Synthesizer",
        model="gpt-4o",
        instructions="""You are an information synthesis expert. Your role is to:
1. Analyze all search results from the Retriever
2. Filter out irrelevant or low-quality information
3. Identify key themes and insights
4. Organize information by topic
5. Remove duplicates and redundant content
6. Prioritize the most important findings

Create a well-organized synthesis of all findings.
Then hand off to the Writer to create the final report.""",
        handoffs=[writer],
        hooks=hooks,
        model_settings=ModelSettings(timeout=90),
    )
