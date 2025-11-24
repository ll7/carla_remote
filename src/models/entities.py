from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class SSHConnection:
    host: str
    user: str
    ports_forwarded: List[int] = field(default_factory=list)
    tunnel_pid: Optional[int] = None
    status: str = "INIT"  # INIT | CONNECTED | FAILED | CLOSED
    started_at: Optional[datetime] = None
    last_check: Optional[datetime] = None


@dataclass
class CarlaInstallState:
    detected: bool
    path: Optional[str] = None
    version: str = "UNKNOWN"
    multiple_versions: bool = False
    selectable_versions: List[str] = field(default_factory=list)


@dataclass
class CarlaServerProcess:
    pid: Optional[int] = None
    session_type: str = "none"  # tmux | none
    session_name: Optional[str] = None
    state: str = "STARTING"  # STARTING | RUNNING | STOPPED | ERROR
    started_at: Optional[datetime] = None
    ports: List[int] = field(default_factory=list)


@dataclass
class PortMapping:
    remote_port: int
    local_port: int
    status: str = "AVAILABLE"  # AVAILABLE | CONFLICT | MAPPED
    conflict_reason: Optional[str] = None


@dataclass
class ExecutionLogEntry:
    timestamp: datetime
    level: str
    component: str
    action: str
    outcome: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["timestamp"] = self.timestamp.isoformat()
        return payload
