import agents as agents_sdk

from deep_research_agent.agents import (create_planner_agent,
                                        create_query_generator_agent,
                                        create_retriever_agent,
                                        create_synthesizer_agent,
                                        create_writer_agent)
from deep_research_agent.utils import load_config


def main():
    config = load_config()
    
    if config["openai_api_key"]:
        agents_sdk.set_default_openai_key(config["openai_api_key"])
    
    writer = create_writer_agent()
    synthesizer = create_synthesizer_agent(writer)
    retriever = create_retriever_agent(synthesizer)
    query_generator = create_query_generator_agent(retriever)
    planner = create_planner_agent(query_generator)
    
    research_query = input("Enter your research topic: ")
    
    result = agents_sdk.Runner.run_sync(planner, research_query)
    
    print("\n" + "="*80)
    print("RESEARCH REPORT")
    print("="*80 + "\n")
    print(result.final_output)


if __name__ == "__main__":
    main()
