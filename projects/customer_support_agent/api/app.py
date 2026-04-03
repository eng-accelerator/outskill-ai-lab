"""FastAPI application for the Customer Support Agent.

Serves the multi-agent support pipeline with CORS and SSE streaming
for real-time phase and tool activity.

Usage:
    PYTHONPATH=projects uv run uvicorn customer_support_agent.api.app:app --reload --port 8003
"""

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from customer_support_agent.api.routers.support import router as support_router

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
    logger.info("Customer Support Agent API starting up")
    yield
    logger.info("Customer Support Agent API shutting down")


app = FastAPI(
    title="Customer Support Agent API",
    description="Multi-agent customer support pipeline with real-time SSE streaming",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5175", "http://127.0.0.1:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(support_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Liveness probe for load balancers and orchestration.

    Returns:
        dict[str, str]: Fixed status payload.
    """
    return {"status": "ok"}
