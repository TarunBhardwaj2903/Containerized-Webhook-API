import hmac
import hashlib
import time
import uuid
import logging
from contextlib import asynccontextmanager
from typing import Optional, Annotated

from fastapi import FastAPI, HTTPException, Request, Response, Header, Depends, Query, status
from fastapi.responses import JSONResponse, PlainTextResponse, HTMLResponse
from pydantic import ValidationError

from app.config import settings
from app.models import WebhookRequest, MessageListResponse
from app.storage import init_db, insert_message, get_messages as db_get_messages, get_stats as db_get_stats
from app.logging_utils import setup_logging
from app.metrics import metrics
from app.ui import dashboard_html

# Setup Logging
logger = setup_logging(settings.LOG_LEVEL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if not settings.WEBHOOK_SECRET:
        logger.error("WEBHOOK_SECRET not set!")
        raise RuntimeError("WEBHOOK_SECRET env var is required")
    
    logger.info("Starting up...")
    init_db()
    yield
    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(lifespan=lifespan)

# Middleware for structured logging and metrics
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as exc:
        # Unhandled exception
        logger.error(f"Unhandled exception: {exc}")
        status_code = 500
        response = JSONResponse(content={"detail": "Internal Server Error"}, status_code=500)
    
    duration = (time.time() - start_time) * 1000
    
    # Update metrics
    metrics.inc_http_request(request.url.path, str(status_code))
    metrics.observe_latency(duration)
    
    # Log
    extra = {
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status": status_code,
        "latency_ms": round(duration, 3)
    }
    
    # Add webhook specific log fields if set in request state
    if hasattr(request.state, "webhook_log_extra"):
        extra.update(request.state.webhook_log_extra)
        
    logger.info("Request finished", extra=extra)
    
    return response

# Routes

@app.get("/", response_class=HTMLResponse)
async def root():
    return dashboard_html

@app.post("/webhook")
async def webhook(
    request: Request,
    x_signature: Annotated[Optional[str], Header()] = None
):
    # 1. Read Raw Body
    body_bytes = await request.body()
    
    # 2. Check Signature
    if not x_signature:
        metrics.inc_webhook_request("invalid_signature")
        request.state.webhook_log_extra = {"result": "invalid_signature"}
        return JSONResponse(status_code=401, content={"detail": "invalid signature"})
        
    expected_sig = hmac.new(
        settings.WEBHOOK_SECRET.encode(),
        body_bytes,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(x_signature, expected_sig):
        metrics.inc_webhook_request("invalid_signature")
        request.state.webhook_log_extra = {"result": "invalid_signature"}
        return JSONResponse(status_code=401, content={"detail": "invalid signature"})

    # 3. Parse and Validate JSON
    try:
        # We validated signature on raw bytes, now parse as JSON
        json_body = await request.json()
        webhook_req = WebhookRequest(**json_body)
    except ValidationError as e:
        metrics.inc_webhook_request("validation_error")
        request.state.webhook_log_extra = {"result": "validation_error"}
        return JSONResponse(status_code=422, content={"detail": e.errors(include_url=False, include_context=False, include_input=False)})
    except Exception:
        metrics.inc_webhook_request("validation_error")
        request.state.webhook_log_extra = {"result": "validation_error"}
        return JSONResponse(status_code=422, content={"detail": "Invalid JSON"})

    # 4. Idempotency & Persistence
    inserted = insert_message(webhook_req)
    
    if inserted:
        result = "created"
    else:
        result = "duplicate"
        
    metrics.inc_webhook_request(result)
    
    request.state.webhook_log_extra = {
        "message_id": webhook_req.message_id,
        "dup": not inserted,
        "result": result
    }
    
    return {"status": "ok"}

@app.get("/messages")
async def list_messages(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    from_: Optional[str] = Query(None, alias="from"),
    since: Optional[str] = None,
    q: Optional[str] = None
):
    try:
        data, total = db_get_messages(limit, offset, from_, since, q)
        return MessageListResponse(
            data=data,
            total=total,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/stats")
async def get_stats_endpoint():
    try:
        stats = db_get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/health/live")
async def health_live():
    return {"status": "ok"}

@app.get("/health/ready")
async def health_ready():
    # Check DB and Secret
    if not settings.WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Secret not set")
    try:
        # Simple DB check
        db_get_stats()
    except Exception:
        raise HTTPException(status_code=503, detail="Database not ready")
        
    return {"status": "ok"}

@app.get("/metrics")
async def metrics_endpoint():
    return PlainTextResponse(metrics.generate_output())
