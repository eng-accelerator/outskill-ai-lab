import agents as agents_sdk


def create_planner_agent(query_generator):
    return agents_sdk.Agent(
        name="Planner",
        model="gpt-4o",
        instructions="""You are a research planning expert. Your role is to:
1. Analyze the user's research request
2. Break it down into 3-5 clear sub-topics that need to be researched
3. Create a logical research structure

Output your plan as a list of specific sub-topics to research.
Then hand off to the Query Generator to create search queries.""",
        handoffs=[query_generator],
    )
