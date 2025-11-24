from __future__ import annotations

import socket
from typing import Iterable, List, Sequence

from src.models.entities import PortMapping

DEFAULT_REMOTE_PORTS: Sequence[int] = (2000, 2001, 2002)


def _is_port_free(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def probe_ports(remote_ports: Iterable[int] = DEFAULT_REMOTE_PORTS, host: str = "127.0.0.1") -> List[PortMapping]:
    results: List[PortMapping] = []
    for port in remote_ports:
        if _is_port_free(port, host=host):
            results.append(PortMapping(remote_port=port, local_port=port, status="AVAILABLE"))
        else:
            results.append(
                PortMapping(
                    remote_port=port,
                    local_port=port,
                    status="CONFLICT",
                    conflict_reason="local port unavailable",
                )
            )
    return results


def suggest_remap(
    remote_ports: Sequence[int] = DEFAULT_REMOTE_PORTS,
    *,
    host: str = "127.0.0.1",
    step: int = 10,
    attempts: int = 20,
) -> List[PortMapping]:
    """Find the first contiguous free block for the given remote ports."""
    base = min(remote_ports)
    span = len(remote_ports)
    for attempt in range(attempts):
        start = base + (attempt + 1) * step
        candidate = [start + idx for idx in range(span)]
        if all(_is_port_free(port, host=host) for port in candidate):
            return [
                PortMapping(remote_port=remote_ports[idx], local_port=local_port, status="MAPPED")
                for idx, local_port in enumerate(candidate)
            ]
    return []


def all_available(mappings: Iterable[PortMapping]) -> bool:
    return all(mapping.status == "AVAILABLE" for mapping in mappings)
