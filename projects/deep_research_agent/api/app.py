"""FastAPI application for the Deep Research Agent.

Serves the research pipeline as a web API with CORS support and
SSE streaming for real-time agent activity updates.

Usage:
    PYTHONPATH=projects uv run uvicorn deep_research_agent.api.app:app --reload --port 8001
"""

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from deep_research_agent.api.routers.research import router as research_router

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
    logger.info("Deep Research Agent API starting up")
    yield
    logger.info("Deep Research Agent API shutting down")


app = FastAPI(
    title="Deep Research Agent API",
    description="Multi-agent research pipeline with real-time SSE streaming",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        dict: Status indicator.
    """
    return {"status": "ok"}
