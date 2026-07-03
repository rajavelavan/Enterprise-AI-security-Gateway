from fastapi import FastAPI
from app.core.config import settings
from app.api.router import router as chat_router
from app.telemetry.tracing import setup_tracing

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Setup OpenTelemetry tracing
setup_tracing(app)

# Include routers
app.include_router(chat_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": f"Welcome to the {settings.PROJECT_NAME}"}
