"""Stateless proxy forwarder to external LLM providers.

Forwards DLP-sanitized prompts to the configured LLM endpoint using
httpx async HTTP client with OpenTelemetry span tracing.
"""

from __future__ import annotations

import httpx

from app.core.config import settings
from app.telemetry.tracing import get_tracer

tracer = get_tracer(__name__)


async def forward_to_llm(sanitized_message: str) -> dict:
    """Forward the sanitized prompt to the configured external LLM provider.

    This is a stateless pass-through — each request creates its own
    HTTP client, maintaining the stateless proxy architecture. No
    session cookies or connection pools are reused across requests.

    Args:
        sanitized_message: The DLP-scanned and potentially redacted prompt.

    Returns:
        The raw JSON response from the LLM provider.

    Raises:
        httpx.HTTPStatusError: If the LLM provider returns an error status.
        httpx.TimeoutException: If the LLM provider does not respond in time.

    """
    with tracer.start_as_current_span("llm_forward") as span:
        span.set_attribute("llm.provider", settings.LLM_BASE_URL)
        span.set_attribute("llm.model", settings.LLM_MODEL)

        headers = {
            "Authorization": f"Bearer {settings.LLM_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.LLM_MODEL,
            "messages": [{"role": "user", "content": sanitized_message}],
        }

        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
            response = await client.post(
                settings.LLM_BASE_URL,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()

            result = response.json()
            span.set_attribute("llm.response_status", response.status_code)
            return result
