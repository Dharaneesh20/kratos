import logging
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.config import settings
from app.logging_utils import configure_logging, get_request_id, log_event, request_id_ctx
from app.routers.dataset import router as dataset_router
from app.routers.vision import router as vision_router
from app.schemas import HealthResponse

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.SERVICE_NAME)

app.include_router(dataset_router)
app.include_router(vision_router)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = get_request_id(request)
    token = request_id_ctx.set(request_id)
    started = time.perf_counter()
    try:
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        log_event(
            logger,
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round((time.perf_counter() - started) * 1000, 2),
        )
        return response
    finally:
        request_id_ctx.reset(token)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and detail.get("status") == "error":
        return JSONResponse(status_code=exc.status_code, content=detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "agent": "vision",
            "message": str(detail),
            "code": "VISION_HTTP_ERROR",
        },
    )


def _sanitize_error_obj(obj):
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    elif isinstance(obj, dict):
        return {k: _sanitize_error_obj(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_error_obj(v) for v in obj]
    return obj


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    sanitized_errors = _sanitize_error_obj(exc.errors())
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "agent": "vision",
            "message": "request validation failed",
            "code": "VISION_VALIDATION_ERROR",
            "errors": jsonable_encoder(sanitized_errors),
        },
    )


@app.get("/health", response_model=HealthResponse)
def health():
    return {
        "status": "ok",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
    }
