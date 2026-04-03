"""FastAPI application for the Cybersecurity Threat Detection Agent.

Serves the multi-agent threat pipeline with CORS and SSE streaming
for real-time phase and tool activity.

Usage:
    PYTHONPATH=projects uv run uvicorn cybersecurity_threat_detection_agent.api.app:app --reload --port 8005
"""

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cybersecurity_threat_detection_agent.api.routers.threat import router as threat_router

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
    logger.info("Cybersecurity Threat Detection Agent API starting up")
    yield
    logger.info("Cybersecurity Threat Detection Agent API shutting down")


app = FastAPI(
    title="Cybersecurity Threat Detection Agent API",
    description="Multi-agent threat detection pipeline with real-time SSE streaming",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5177", "http://127.0.0.1:5177"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(threat_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Liveness probe for load balancers and orchestration.

    Returns:
        dict[str, str]: Fixed status payload.
    """
    return {"status": "ok"}
