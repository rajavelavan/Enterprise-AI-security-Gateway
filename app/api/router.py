from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.dlp.scanner import dlp_scanner
from app.telemetry.tracing import get_tracer

router = APIRouter()
tracer = get_tracer(__name__)

class ChatPayload(BaseModel):
    message: str

class ChatResponse(BaseModel):
    status: str
    message: str

@router.post("/chat", response_model=ChatResponse)
async def process_chat(payload: ChatPayload):
    # Start a nested span for the DLP scanning process
    with tracer.start_as_current_span("dlp_scan"):
        is_safe = dlp_scanner.is_safe(payload.message)
        
    if not is_safe:
        with tracer.start_as_current_span("dlp_violation"):
            # We can log or handle the violation here
            pass
        raise HTTPException(status_code=403, detail="DLP Violation: Sensitive content detected in payload.")

    with tracer.start_as_current_span("llm_processing"):
        # Placeholder for actual LLM processing in future phases
        processed_message = f"Processed: {payload.message}"

    return ChatResponse(status="success", message=processed_message)
