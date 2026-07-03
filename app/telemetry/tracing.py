from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from fastapi import FastAPI

def setup_tracing(app: FastAPI) -> None:
    # Set up the tracer provider
    provider = TracerProvider()
    
    # Configure the console exporter for initial development
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    
    # Register the tracer provider globally
    trace.set_tracer_provider(provider)
    
    # Instrument the FastAPI application
    FastAPIInstrumentor.instrument_app(app)
    
def get_tracer(name: str):
    return trace.get_tracer(name)
