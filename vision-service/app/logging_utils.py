import json
import logging
import time
import uuid
from contextvars import ContextVar
from typing import Optional

from fastapi import Request

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": int(time.time()),
            "level": record.levelname.lower(),
            "service": "vision-service",
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None) or request_id_ctx.get(),
        }
        if hasattr(record, "extra"):
            payload.update(record.extra)
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)


def get_request_id(request: Optional[Request] = None) -> str:
    if request is not None:
        incoming = request.headers.get("x-request-id")
        if incoming:
            return incoming
    return f"req_{uuid.uuid4().hex}"


def log_event(logger: logging.Logger, message: str, **extra) -> None:
    logger.info(message, extra={"extra": extra})
