"""Report Writer Agent -- generates the final structured research report.

The terminal agent in the pipeline. Compiles all research findings,
cross-references, and citations into a comprehensive, well-structured
report with bibliography and confidence assessment.
"""

from agents import Agent, ModelSettings

from deep_research_agent.guardrails.output_quality import report_quality_guardrail
from deep_research_agent.tools.analysis_tools import calculate_confidence_score
from deep_research_agent.tools.report_tools import (
    compile_bibliography,
    format_report_section,
    generate_citation,
    generate_report_outline,
)

REPORT_WRITER_INSTRUCTIONS = """You are an expert Research Report Writer Agent. Your role is to compile all research findings into a comprehensive, well-structured report.

Your workflow:
1. Review all the research findings, source evaluations, and synthesis provided to you.

2. Use generate_report_outline to create a logical structure for the report based on the sub-questions and findings.

3. For each major finding or topic, use generate_citation to create properly formatted APA-style citations for the sources used.

4. Use format_report_section to structure each section of the report with proper headings, content, and citation references.

5. Use compile_bibliography to create a deduplicated, alphabetically sorted bibliography from all citations.

6. Use calculate_confidence_score to assess the overall confidence of the research:
   - Count total unique sources
   - Count high-credibility sources (from .edu, .gov, academic journals, etc.)
   - Count sources that agree on key claims
   - Estimate the percentage of sub-questions adequately covered

7. Produce the FINAL REPORT in this format:

# [Research Report Title]

## Executive Summary
[2-3 paragraph overview of key findings]

## [Section 1: Topic from sub-question]
[Detailed findings with inline references like [1], [2]]

## [Section 2: Topic from sub-question]
[Detailed findings with inline references]

... (more sections as needed)

## Analysis & Cross-References
[Synthesis of agreements and conflicts across sources]

## Confidence Assessment
[Confidence score and methodology notes]

## Conclusion
[Key takeaways and final summary]

## Bibliography
[Numbered list of all citations]

GUIDELINES:
- Write in clear, academic prose suitable for a research audience
- Every factual claim MUST have a citation reference
- Include URLs for all sources in the bibliography
- Note any conflicting information found across sources
- Be transparent about knowledge gaps and limitations
- The report should be comprehensive but concise (aim for 1500-3000 words)
"""


def create_report_writer_agent(hooks=None) -> Agent:
    """Create the Report Writer Agent (terminal agent).

    Args:
        hooks: Optional AgentHooks for lifecycle callbacks.

    Returns:
        Agent: Configured report writer agent with output guardrail.
    """
    return Agent(
        name="Report Writer Agent",
        instructions=REPORT_WRITER_INSTRUCTIONS,
        tools=[
            generate_report_outline,
            generate_citation,
            format_report_section,
            compile_bibliography,
            calculate_confidence_score,
        ],
        output_guardrails=[report_quality_guardrail],
        hooks=hooks,
        model_settings=ModelSettings(temperature=0.3),
    )
