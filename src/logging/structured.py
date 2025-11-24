from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional, TextIO

from src.models.entities import ExecutionLogEntry

DEFAULT_LEVELS: Iterable[str] = ("DEBUG", "INFO", "WARN", "ERROR")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_level(level: str) -> str:
    upper = level.upper()
    return upper if upper in DEFAULT_LEVELS else "INFO"


def serialize_entry(entry: ExecutionLogEntry) -> Dict[str, Any]:
    payload = entry.to_dict()
    # Ensure timezone suffix is always Z for UTC
    timestamp = entry.timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    payload["timestamp"] = timestamp
    return payload


def log_event(
    component: str,
    action: str,
    *,
    level: str = "INFO",
    outcome: str = "success",
    details: Optional[Dict[str, Any]] = None,
    stream: TextIO = sys.stdout,
) -> ExecutionLogEntry:
    entry = ExecutionLogEntry(
        timestamp=_utcnow(),
        level=_normalize_level(level),
        component=component,
        action=action,
        outcome=outcome,
        details=details or {},
    )
    payload = serialize_entry(entry)
    stream.write(json.dumps(payload, separators=(",", ":"), default=str) + "\n")
    stream.flush()
    return entry


def log_error(component: str, action: str, message: str, *, stream: TextIO = sys.stdout, **extra: Any) -> ExecutionLogEntry:
    details: Dict[str, Any] = {"message": message}
    details.update(extra)
    return log_event(component, action, level="ERROR", outcome="failure", details=details, stream=stream)
