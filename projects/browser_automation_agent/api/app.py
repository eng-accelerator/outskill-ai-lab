"""FastAPI application for the Browser Automation Agent.

Serves the browser automation pipeline as a web API with CORS
support and SSE streaming for real-time agent activity updates.

Usage:
    PYTHONPATH=projects uv run uvicorn browser_automation_agent.api.app:app --reload --port 8002
"""

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from browser_automation_agent.api.routers.automation import router as automation_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: load env vars on startup.

    Args:
        app: The FastAPI application instance.
    """
    load_dotenv()
    logger.info("Browser Automation Agent API starting up")
    yield
    logger.info("Browser Automation Agent API shutting down")


app = FastAPI(
    title="Browser Automation Agent API",
    description="Multi-agent browser automation pipeline with real-time SSE streaming",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(automation_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        dict: Status indicator.
    """
    return {"status": "ok"}
