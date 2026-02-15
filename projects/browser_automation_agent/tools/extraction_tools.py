"""Extraction tools for pulling structured data from web pages.

Wraps Stagehand's session.extract method as OpenAI Agents SDK
function tools for extracting structured and unstructured data
from the current page.
"""

import json
import logging
from datetime import datetime, timezone

from agents import RunContextWrapper, function_tool
from browser_automation_agent.models.result import ExtractionResult
from browser_automation_agent.models.task import BrowserContext

logger = logging.getLogger(__name__)


@function_tool
async def extract_page_data(
    ctx: RunContextWrapper[BrowserContext],
    instruction: str,
    output_schema: str,
) -> str:
    """Extract structured data from the current page using a JSON schema.

    Uses Stagehand's session.extract with a JSON schema to pull
    structured, typed data from the page content. The schema defines
    the shape of the expected output.

    Args:
        ctx: Run context containing the browser session.
        instruction: Natural language description of what data to extract
            (e.g. "extract the top 10 posts with title, URL, and points").
        output_schema: JSON string defining the expected output schema
            (e.g. '{"type":"object","properties":{"posts":{"type":"array",...}}}').

    Returns:
        str: JSON string with the extracted data matching the schema.
    """
    session = ctx.context.session
    assert session is not None, "Browser session not initialized"

    logger.info("Extracting data: instruction=%s", instruction)

    schema = json.loads(output_schema)
    response = await session.extract(instruction=instruction, schema=schema)

    extracted_data = response.data.result
    data_str = (
        json.dumps(extracted_data, indent=2)
        if not isinstance(extracted_data, str)
        else extracted_data
    )

    # Record extraction in context
    extraction = ExtractionResult(
        url=ctx.context.current_url,
        instruction=instruction,
        data=data_str,
        schema_used=True,
    )
    ctx.context.extraction_results.append(extraction)

    output = {
        "success": response.success,
        "instruction": instruction,
        "data": extracted_data,
        "url": ctx.context.current_url,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        "Extraction complete: instruction=%s, success=%s", instruction, response.success
    )
    return json.dumps(output, indent=2)


@function_tool
async def extract_text(
    ctx: RunContextWrapper[BrowserContext],
    instruction: str,
) -> str:
    """Extract simple text content from the current page.

    A convenience wrapper around Stagehand's session.extract that uses
    a simple text schema. Useful when you just need to pull out a piece
    of text without defining a complex schema.

    Args:
        ctx: Run context containing the browser session.
        instruction: Natural language description of what text to extract
            (e.g. "extract the page title", "extract the main heading").

    Returns:
        str: JSON string with the extracted text.
    """
    session = ctx.context.session
    assert session is not None, "Browser session not initialized"

    logger.info("Extracting text: instruction=%s", instruction)

    simple_schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string"},
        },
        "required": ["text"],
    }

    response = await session.extract(instruction=instruction, schema=simple_schema)

    extracted_data = response.data.result
    data_str = (
        json.dumps(extracted_data, indent=2)
        if not isinstance(extracted_data, str)
        else extracted_data
    )

    # Record extraction in context
    extraction = ExtractionResult(
        url=ctx.context.current_url,
        instruction=instruction,
        data=data_str,
        schema_used=False,
    )
    ctx.context.extraction_results.append(extraction)

    output = {
        "success": response.success,
        "instruction": instruction,
        "data": extracted_data,
        "url": ctx.context.current_url,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        "Text extraction complete: instruction=%s, success=%s",
        instruction,
        response.success,
    )
    return json.dumps(output, indent=2)
