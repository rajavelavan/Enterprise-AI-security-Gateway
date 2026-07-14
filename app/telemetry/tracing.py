"""OpenTelemetry distributed tracing configuration for the AI Security Gateway.

Sets up trace providers, span processors, and auto-instruments FastAPI
to capture request lifecycle spans for observability.
"""

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter


def setup_tracing(app: FastAPI) -> None:
    """Configure OpenTelemetry tracing and instrument the FastAPI application.

    Initializes a TracerProvider with a console exporter for development,
    registers it globally, and auto-instruments the given FastAPI app to
    capture HTTP request/response spans.

    Args:
        app: The FastAPI application instance to instrument.
    """
    # Set up the tracer provider
    provider = TracerProvider()

    # Configure the console exporter for initial development
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)

    # Register the tracer provider globally
    trace.set_tracer_provider(provider)

    # Instrument the FastAPI application
    FastAPIInstrumentor.instrument_app(app)


def get_tracer(name: str) -> trace.Tracer:
    """Return a named tracer instance from the global tracer provider.

    Args:
        name: Identifier for the tracer, typically ``__name__`` of the module.

    Returns:
        A Tracer instance bound to the given name.
    """
    return trace.get_tracer(name)
