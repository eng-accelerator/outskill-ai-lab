from agents import Agent, ModelSettings


def create_planner_agent(query_generator, hooks=None):
    return Agent(
        name="Planner",
        model="gpt-4o",
        instructions="""You are a research planning expert. Your role is to:
1. Analyze the user's research request
2. Break it down into 3-5 clear sub-topics that need to be researched
3. Create a logical research structure

Output your plan as a list of specific sub-topics to research.
Then hand off to the Query Generator to create search queries.""",
        handoffs=[query_generator],
        hooks=hooks,
        model_settings=ModelSettings(timeout=60),
    )
