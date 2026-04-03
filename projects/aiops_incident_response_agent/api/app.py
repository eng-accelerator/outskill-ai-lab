"""FastAPI application for the AI Ops Incident Response Agent.

Serves the multi-agent incident pipeline with CORS and SSE streaming
for real-time phase and tool activity.

Usage:
    PYTHONPATH=projects uv run uvicorn aiops_incident_response_agent.api.app:app --reload --port 8004
"""

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aiops_incident_response_agent.api.routers.incident import router as incident_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load environment variables at startup and log lifecycle.

    Args:
        app: The FastAPI application instance.

    Yields:
        None: Control returns to FastAPI between startup and shutdown.
    """
    load_dotenv()
    logger.info("AI Ops Incident Response Agent API starting up")
    yield
    logger.info("AI Ops Incident Response Agent API shutting down")


app = FastAPI(
    title="AI Ops Incident Response Agent API",
    description="Multi-agent incident response pipeline with real-time SSE streaming",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5176", "http://127.0.0.1:5176"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(incident_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Liveness probe for load balancers and orchestration.

    Returns:
        dict[str, str]: Fixed status payload.
    """
    return {"status": "ok"}
