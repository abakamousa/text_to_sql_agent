# backend/utils/logger.py
import logging
import sys
import os
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
"""from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor"""
# === Project-specific constants ===
PROJECT_NAME = "TextToSQLAgent"

# === Initialize OpenTelemetry Tracer ===
resource = Resource(attributes={"service.name": PROJECT_NAME})
#trace.set_tracer_provider(TracerProvider(resource=resource))
#tracer = trace.get_tracer(__name__)

# === Configure Azure Monitor Exporter ===
"""instrumentation_key = os.getenv("APPINSIGHTS_INSTRUMENTATIONKEY")
if instrumentation_key:
    exporter = AzureMonitorTraceExporter(connection_string=f"InstrumentationKey={instrumentation_key}")
    span_processor = BatchSpanProcessor(exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)"""

# === Configure Python Logger ===
logger = logging.getLogger(PROJECT_NAME)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s | %(levelname)s | %(task)s | %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# === Instrument logging to integrate with OpenTelemetry ===
#LoggingInstrumentor().instrument(set_logging_format=True)

# === Helper function for centralized logging ===
def log_with_task(level: int, message: str, task: str = "General"):
    """
    Log a message with a specific task context.
    This adds a 'task' field for consistent formatting and OpenTelemetry integration.
    """
    extra = {"task": task}
    logger.log(level, message, extra=extra)
