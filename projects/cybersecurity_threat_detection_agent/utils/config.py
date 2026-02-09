"""Configuration loader for the Cybersecurity Threat Detection Agent.

Loads OpenRouter API credentials and model settings from environment variables.
"""

import os

from dotenv import load_dotenv


def load_config() -> dict[str, str | None]:
    """Load configuration from environment variables.

    Returns:
        dict[str, str | None]: Configuration dictionary with keys:
            - openrouter_api_key: OpenRouter API key for LLM access
            - openrouter_base_url: OpenRouter API base URL
            - model_name: Default model to use via OpenRouter
    """
    load_dotenv()
    return {
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY"),
        "openrouter_base_url": os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ),
        "model_name": os.getenv("OPENROUTER_MODEL", "openai/gpt-5-mini"),
    }
