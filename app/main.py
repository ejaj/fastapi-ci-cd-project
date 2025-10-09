from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

# 1) Set up tracer provider that prints spans to your terminal
provider = TracerProvider(resource=Resource.create({
    "service.name": "xyz-frontend",           # shows up as service name
    "deployment.environment": "local",
}))
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)

app = FastAPI()

def rename_home(span, scope):
    if scope.get("path") == "/":
        span.update_name("homepage")  # optional rename for "/"
FastAPIInstrumentor.instrument_app(app, server_request_hook=rename_home)


@app.get("/")
async def home():
    return {"message": "Hello from xyz"}

@app.get("/health")
async def health():
    return {"status": "ok"}
