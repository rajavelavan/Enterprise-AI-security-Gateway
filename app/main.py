"""Enterprise AI Security Gateway — FastAPI application entry point.

Initializes the FastAPI app with rich OpenAPI metadata, sets up
OpenTelemetry tracing, and registers API route handlers.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.api.router import router as chat_router
from app.core.config import settings
from app.telemetry.tracing import setup_tracing

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "**Enterprise AI Security Gateway** — a stateless interception "
        "proxy that scans, redacts, and forwards prompts to external "
        "LLM providers while enforcing Data Loss Prevention (DLP) "
        "policies.\n\n"
        "## Architecture\n"
        "- **Aho-Corasick DFA** with failure links for "
        "O(n+m+z) keyword detection\n"
        "- **Regex PII Scanner** for structured patterns "
        "(SSN, credit cards, emails, API keys)\n"
        "- **Composite Scanner** combining both engines "
        "with overlap merging\n"
        "- **Three DLP Modes**: `block` · `redact` · `audit`\n"
        "- **Stateless Proxy Forwarding** to external LLM "
        "providers via httpx\n"
        "- **OpenTelemetry** distributed tracing for "
        "full observability"
    ),
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Security Engineering Team",
        "email": "security@enterprise.com",
    },
    license_info={
        "name": "MIT",
    },
    openapi_tags=[
        {
            "name": "Ingress — DLP",
            "description": (
                "Core endpoints for intercepting incoming prompts, "
                "scanning them through the Aho-Corasick DFA and regex "
                "PII engines, and forwarding sanitized content to "
                "external LLM providers."
            ),
        },
        {
            "name": "Admin",
            "description": (
                "Administrative endpoints for managing the DLP engine "
                "at runtime, including hot-reloading the keyword "
                "dictionary."
            ),
        },
    ],
)

# Setup OpenTelemetry tracing
setup_tracing(app)

# Include routers
app.include_router(chat_router, prefix=settings.API_V1_STR)


@app.get(
    "/",
    summary="Health check",
    description=(
        "Returns a welcome message confirming the gateway is running."
    ),
    tags=["Health"],
)
async def root() -> dict[str, str]:
    """Return a welcome message confirming the gateway is operational."""
    return {"message": f"Welcome to the {settings.PROJECT_NAME}"}
