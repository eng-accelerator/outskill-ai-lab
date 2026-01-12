import asyncio

import agents as agents_sdk

from deep_research_agent.agents import (create_planner_agent,
                                        create_query_generator_agent,
                                        create_retriever_agent,
                                        create_synthesizer_agent,
                                        create_writer_agent)
from deep_research_agent.utils import load_config


class StatusHooks(agents_sdk.AgentHooks):
    def on_run_start(self, ctx):
        print(f"\n🚀 Starting: {ctx.agent.name}")
    
    def on_run_end(self, ctx, output):
        print(f"✅ Completed: {ctx.agent.name}")


async def main():
    config = load_config()
    
    if config["openai_api_key"]:
        agents_sdk.set_default_openai_key(config["openai_api_key"])
    
    hooks = StatusHooks()
    
    writer = create_writer_agent(hooks)
    synthesizer = create_synthesizer_agent(writer, hooks)
    retriever = create_retriever_agent(synthesizer, hooks)
    query_generator = create_query_generator_agent(retriever, hooks)
    planner = create_planner_agent(query_generator, hooks)
    
    research_query = input("Enter your research topic: ")
    
    print("\n" + "="*80)
    print("STARTING RESEARCH WORKFLOW")
    print("="*80)
    
    result = await agents_sdk.Runner.run(planner, research_query, max_turns=50)
    
    print("\n" + "="*80)
    print("RESEARCH REPORT")
    print("="*80 + "\n")
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
