import os

from dotenv import load_dotenv


def load_config():
    load_dotenv()
    return {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "openai_base_url": os.getenv("OPENAI_BASE_URL"),
        "tavily_api_key": os.getenv("TAVILY_API_KEY"),
    }
