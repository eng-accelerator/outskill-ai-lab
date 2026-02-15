"""Configuration loader for the Browser Automation Agent.

Loads Stagehand, OpenRouter, and model API credentials
from environment variables.
"""

import os

from dotenv import load_dotenv


def load_config() -> dict[str, str | None]:
    """Load configuration from environment variables.

    Returns:
        dict[str, str | None]: Configuration dictionary with keys:
            - model_api_key: API key for Stagehand's internal LLM
            - openrouter_api_key: OpenRouter API key for agent orchestration
            - openrouter_base_url: OpenRouter API base URL
            - model_name: Default model to use via OpenRouter
    """
    load_dotenv()
    return {
        "model_api_key": os.getenv("MODEL_API_KEY"),
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY"),
        "openrouter_base_url": os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ),
        "model_name": os.getenv("OPENROUTER_MODEL", "openai/gpt-4.1-mini"),
    }
