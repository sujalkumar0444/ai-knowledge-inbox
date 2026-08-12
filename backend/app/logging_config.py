"""
Structured logging setup.

Emits single-line JSON logs to stdout so they're easy to grep or pipe into
a log aggregator. Every request gets a request_id (see the middleware in
main.py) attached via the `extra={"request_id": ...}` kwarg on each log
call, so a single request's start/end can be correlated by grepping that id.

Deliberately not using a ContextVar to propagate request_id automatically
into every log line in the call stack (including deep in the service
layer): that's a real option, but it adds implicit global state for a
debuggability need this app-sized project doesn't have -- routers already
log the request lifecycle, and services log their own domain events with
enough context (item_id, question, etc.) to be greppable on their own.
Worth revisiting if the service layer grows deep enough that cross-request
log correlation becomes hard without it.
"""
import json
import logging
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            payload["request_id"] = record.request_id
        if hasattr(record, "extra_fields"):
            payload.update(record.extra_fields)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
