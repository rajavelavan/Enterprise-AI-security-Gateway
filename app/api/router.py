"""API router for the AI Security Gateway ingress layer.

Defines endpoints for DLP-scanned prompt forwarding and administrative
operations such as dynamic keyword reloading.
"""

from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.dlp.composite_scanner import composite_scanner
from app.proxy.forwarder import forward_to_llm
from app.telemetry.tracing import get_tracer

logger = logging.getLogger(__name__)
router = APIRouter()
tracer = get_tracer(__name__)


# ──────────────────── Request / Response Models ────────────────────


class ChatPayload(BaseModel):
    """Incoming prompt payload to be scanned by the DLP engine."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=32_000,
        description=(
            "The raw user prompt to be scanned by the DLP engine "
            "before forwarding to the LLM."
        ),
        json_schema_extra={
            "example": "Summarize our Q3 earnings report."
        },
    )


class DLPFinding(BaseModel):
    """A single DLP finding detected in the prompt."""

    type: str = Field(
        ...,
        description=(
            "Category of the finding: KEYWORD, SSN, "
            "CREDIT_CARD, EMAIL, etc."
        ),
        json_schema_extra={"example": "KEYWORD"},
    )
    start: int = Field(
        ...,
        description=(
            "Start character index of the match in the original text."
        ),
        json_schema_extra={"example": 15},
    )
    end: int = Field(
        ...,
        description="End character index (exclusive) of the match.",
        json_schema_extra={"example": 23},
    )


class ChatResponse(BaseModel):
    """Response returned after DLP scanning and optional LLM forwarding."""

    status: str = Field(
        ...,
        description=(
            "Outcome of the DLP scan: 'success', 'redacted', or 'blocked'."
        ),
        json_schema_extra={"example": "success"},
    )
    message: str = Field(
        ...,
        description=(
            "The processed (and potentially redacted) response "
            "from the LLM or gateway."
        ),
        json_schema_extra={
            "example": "Processed: Summarize our Q3 earnings report."
        },
    )
    findings: list[DLPFinding] = Field(
        default=[],
        description=(
            "List of DLP findings detected in the original prompt "
            "(empty if clean)."
        ),
    )
    dlp_mode: str = Field(
        ...,
        description=(
            "The DLP policy mode that was applied: "
            "'block', 'redact', or 'audit'."
        ),
        json_schema_extra={"example": "redact"},
    )


class DLPViolationResponse(BaseModel):
    """Error response returned when a prompt is blocked by DLP policy."""

    detail: str = Field(
        ...,
        description=(
            "Human-readable description of the DLP policy violation."
        ),
        json_schema_extra={
            "example": (
                "DLP Violation: Sensitive content detected in payload."
            )
        },
    )


class KeywordReloadPayload(BaseModel):
    """Payload for dynamically reloading the DLP keyword dictionary."""

    keywords: list[str] = Field(
        ...,
        min_length=1,
        description=(
            "New list of sensitive keywords to load into "
            "the Aho-Corasick automaton."
        ),
        json_schema_extra={
            "example": ["CONFIDENTIAL", "SSN", "PASSWORD", "SECRET_KEY"]
        },
    )


class KeywordReloadResponse(BaseModel):
    """Confirmation response after keyword dictionary reload."""

    status: str = Field(
        ...,
        description="Result status of the reload operation.",
        json_schema_extra={"example": "ok"},
    )
    keyword_count: int = Field(
        ...,
        description="Number of keywords now loaded in the automaton.",
        json_schema_extra={"example": 12},
    )


# ──────────────────── Endpoints ────────────────────


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Scan and forward a prompt to the LLM",
    description=(
        "Accepts a raw prompt, runs it through the Aho-Corasick DFA "
        "keyword scanner and regex PII pattern scanner, then either "
        "blocks, redacts, or forwards the sanitized prompt to the "
        "configured external LLM provider based on the active "
        "DLP policy mode."
    ),
    tags=["Ingress — DLP"],
    responses={
        403: {
            "model": DLPViolationResponse,
            "description": (
                "The prompt was blocked due to a DLP policy violation."
            ),
        },
    },
)
async def process_chat(payload: ChatPayload) -> ChatResponse:
    """Scan the incoming prompt and forward to the LLM after DLP processing."""
    dlp_mode = settings.DLP_MODE

    with tracer.start_as_current_span("dlp_scan") as span:
        span.set_attribute("dlp.mode", dlp_mode)

        if dlp_mode == "block":
            # ── Block Mode: reject the entire request if any finding ──
            if not composite_scanner.is_safe(payload.message):
                span.set_attribute("dlp.action", "blocked")
                raise HTTPException(
                    status_code=403,
                    detail=(
                        "DLP Violation: Sensitive content "
                        "detected in payload."
                    ),
                )
            sanitized_message = payload.message
            findings_out: list[DLPFinding] = []
            status = "success"

        elif dlp_mode == "redact":
            # ── Redact Mode: mask sensitive content and forward ──
            sanitized_message, findings = composite_scanner.redact(
                payload.message, mask=settings.DLP_REDACTION_MASK
            )
            span.set_attribute("dlp.action", "redacted")
            span.set_attribute("dlp.findings_count", len(findings))
            findings_out = [
                DLPFinding(
                    type=f.get("type", "UNKNOWN"),
                    start=f["start"],
                    end=f["end"],
                )
                for f in findings
            ]
            status = "redacted" if findings else "success"

        else:
            # ── Audit Mode: log findings but forward original prompt ──
            findings = composite_scanner.scan(payload.message)
            span.set_attribute("dlp.action", "audit")
            span.set_attribute("dlp.findings_count", len(findings))
            sanitized_message = payload.message
            findings_out = [
                DLPFinding(
                    type=f.get("type", "UNKNOWN"),
                    start=f["start"],
                    end=f["end"],
                )
                for f in findings
            ]
            status = "success"

    # ── Forward to external LLM (or placeholder if no API key) ──
    with tracer.start_as_current_span("llm_processing"):
        if settings.LLM_API_KEY:
            try:
                llm_response = await forward_to_llm(sanitized_message)
                processed_message = (
                    llm_response.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", sanitized_message)
                )
            except (httpx.HTTPStatusError, httpx.TimeoutException) as exc:
                logger.exception("LLM forwarding failed")
                processed_message = (
                    f"LLM forwarding error: {exc}"
                )
        else:
            # No API key configured — return gateway-processed result
            processed_message = f"Processed: {sanitized_message}"

    return ChatResponse(
        status=status,
        message=processed_message,
        findings=findings_out,
        dlp_mode=dlp_mode,
    )


@router.post(
    "/admin/dlp/reload",
    response_model=KeywordReloadResponse,
    summary="Hot-reload the DLP keyword dictionary",
    description=(
        "Dynamically rebuilds the Aho-Corasick automaton with a new set "
        "of keywords without requiring a server restart. The new DFA with "
        "failure links is constructed in O(m) time where m is the total "
        "length of all keywords."
    ),
    tags=["Admin"],
)
async def reload_dlp_keywords(
    payload: KeywordReloadPayload,
) -> KeywordReloadResponse:
    """Rebuild the Aho-Corasick automaton with the provided keywords."""
    composite_scanner.reload_keywords(payload.keywords)
    return KeywordReloadResponse(
        status="ok",
        keyword_count=len(payload.keywords),
    )
