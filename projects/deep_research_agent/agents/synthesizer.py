"""Synthesizer Agent -- cross-references, evaluates, and synthesizes findings.

Receives all research findings from the searchers/extractors, evaluates
source credibility, cross-references claims, identifies knowledge gaps,
and produces a coherent synthesis for the report writer.
"""

from agents import Agent, ModelSettings
from deep_research_agent.tools.analysis_tools import (
    calculate_confidence_score,
    cross_reference_findings,
    evaluate_source_credibility,
    extract_key_claims,
    identify_knowledge_gaps,
)

SYNTHESIZER_INSTRUCTIONS = """You are the Synthesizer Agent. You evaluate sources, cross-reference findings, and then IMMEDIATELY hand off to the Report Writer Agent. You NEVER produce a final answer yourself.

## Workflow

1. Review all findings provided to you.
2. Use evaluate_source_credibility on the top 2-3 sources (URL, title, content snippet).
3. Use extract_key_claims on the most important content piece.
4. Optionally use cross_reference_findings or identify_knowledge_gaps.
5. IMMEDIATELY call transfer_to_report_writer_agent with your complete synthesis:
   - Key findings organized by theme
   - Source credibility assessments
   - Claims extracted and cross-referenced
   - Any knowledge gaps

## CRITICAL RULES
- You MUST call transfer_to_report_writer_agent when done. This is mandatory.
- Do NOT produce a final report yourself. The Report Writer does that.
- Keep your analysis tools to 2-4 calls, then hand off.
- Include ALL source URLs and content in the handoff for the Report Writer to cite.
"""


def create_synthesizer_agent(report_writer: Agent, hooks=None) -> Agent:
    """Create the Synthesizer Agent.

    Args:
        report_writer: The Report Writer agent to hand off to.
        hooks: Optional AgentHooks for lifecycle callbacks.

    Returns:
        Agent: Configured synthesizer agent.
    """
    return Agent(
        name="Synthesizer Agent",
        instructions=SYNTHESIZER_INSTRUCTIONS,
        tools=[
            evaluate_source_credibility,
            extract_key_claims,
            cross_reference_findings,
            identify_knowledge_gaps,
            calculate_confidence_score,
        ],
        handoffs=[report_writer],
        hooks=hooks,
        model_settings=ModelSettings(temperature=0.2),
    )
