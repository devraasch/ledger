import os

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

from app.infrastructure.database.connection import engine

SERVICE_NAME = "ledger-event-sourcing-api"
_configured = False


def setup_tracing(app: FastAPI) -> None:
    global _configured

    if _configured:
        return

    provider = TracerProvider(
        resource=Resource.create({"service.name": SERVICE_NAME}),
    )
    if os.getenv("OTEL_CONSOLE_EXPORTER", "false").lower() == "true":
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine)
    _configured = True
