import asyncio

from agents import Agent, AgentHooks, ModelSettings, Runner, set_default_openai_key

from deep_research_agent.agents.planner import create_planner_agent
from deep_research_agent.agents.query_generator import create_query_generator_agent
from deep_research_agent.agents.retriever import create_retriever_agent
from deep_research_agent.agents.synthesizer import create_synthesizer_agent
from deep_research_agent.agents.writer import create_writer_agent
from deep_research_agent.utils.config import load_config


class StatusHooks(AgentHooks):
    def on_run_start(self, ctx):
        print(f"\n🚀 Starting: {ctx.agent.name}")

    def on_run_end(self, ctx, output):
        print(f"✅ Completed: {ctx.agent.name}")


async def main():
    config = load_config()

    if config["openai_api_key"]:
        set_default_openai_key(config["openai_api_key"])

    hooks = StatusHooks()

    writer = create_writer_agent(hooks)
    synthesizer = create_synthesizer_agent(writer, hooks)
    retriever = create_retriever_agent(synthesizer, hooks)
    query_generator = create_query_generator_agent(retriever, hooks)
    planner = create_planner_agent(query_generator, hooks)

    research_query = input("Enter your research topic: ")

    print("\n" + "=" * 80)
    print("STARTING RESEARCH WORKFLOW")
    print("=" * 80)

    result = await Runner.run(planner, research_query, max_turns=50)

    print("\n" + "=" * 80)
    print("RESEARCH REPORT")
    print("=" * 80 + "\n")
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
