from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, List, Optional, Sequence

from src.logging.structured import log_error, log_event
from src.models.entities import CarlaServerProcess, PortMapping
from src.services.ports import DEFAULT_REMOTE_PORTS
from src.services.ssh_client import SSHClientWrapper, SSHCommandError, SSHConnectionError

DEFAULT_SESSION_NAME = "carla-server"


class CarlaStartError(Exception):
    """Raised when CARLA fails to start or verify."""


def detect_running_server(ssh: SSHClientWrapper) -> Optional[CarlaServerProcess]:
    """Return an existing CARLA process if found."""
    try:
        result = ssh.run_command("pgrep -f CarlaUE4.sh")
    except (SSHConnectionError, SSHCommandError):
        return None

    if result.exit_code == 0 and result.stdout.strip():
        try:
            pid = int(result.stdout.splitlines()[0])
        except ValueError:
            pid = None
        return CarlaServerProcess(
            pid=pid,
            session_type="none",
            session_name=None,
            state="RUNNING",
            started_at=datetime.now(timezone.utc),
            ports=list(DEFAULT_REMOTE_PORTS),
        )
    return None


def _build_start_command(install_path: Optional[str], remote_ports: Sequence[int]) -> str:
    path = install_path or "$HOME"
    port_flags = f"-carla-rpc-port {remote_ports[0]}" if remote_ports else ""
    return f"cd {path} && ./CarlaUE4.sh -RenderOffScreen {port_flags}"


def start_carla_server(
    ssh: SSHClientWrapper,
    *,
    install_path: Optional[str],
    use_tmux: bool,
    session_name: str = DEFAULT_SESSION_NAME,
    remote_ports: Sequence[int] = DEFAULT_REMOTE_PORTS,
) -> CarlaServerProcess:
    start_cmd = _build_start_command(install_path, remote_ports)
    if use_tmux:
        command = f"tmux new -d -s {session_name} \"{start_cmd}\""
    else:
        command = f"bash -lc '{start_cmd} >/tmp/carla_server.log 2>&1 & echo $!'"

    log_event("carla_start", "start_attempt", details={"use_tmux": use_tmux, "session": session_name})
    result = ssh.run_command(command, timeout=120)
    if result.exit_code != 0:
        log_error("carla_start", "start_failed", result.stderr)
        raise CarlaStartError(result.stderr or "CARLA start failed")

    pid: Optional[int] = None
    if not use_tmux and result.stdout.strip():
        try:
            pid = int(result.stdout.strip().splitlines()[-1])
        except ValueError:
            pid = None

    server = CarlaServerProcess(
        pid=pid,
        session_type="tmux" if use_tmux else "none",
        session_name=session_name if use_tmux else None,
        state="STARTING",
        started_at=datetime.now(timezone.utc),
        ports=list(remote_ports),
    )
    if not verify_ports(ssh, remote_ports):
        server.state = "ERROR"
        raise CarlaStartError("CARLA ports not listening after start")
    server.state = "RUNNING"
    return server


def detect_tmux_session(
    ssh: SSHClientWrapper,
    session_name: str = DEFAULT_SESSION_NAME,
    remote_ports: Sequence[int] = DEFAULT_REMOTE_PORTS,
) -> Optional[CarlaServerProcess]:
    try:
        result = ssh.run_command(f"tmux has-session -t {session_name}")
    except (SSHConnectionError, SSHCommandError):
        return None

    if result.exit_code == 0:
        return CarlaServerProcess(
            pid=None,
            session_type="tmux",
            session_name=session_name,
            state="RUNNING",
            started_at=datetime.now(timezone.utc),
            ports=list(remote_ports),
        )
    return None


def verify_ports(ssh: SSHClientWrapper, remote_ports: Iterable[int]) -> bool:
    """Check remote ports are listening."""
    for port in remote_ports:
        cmd = f"ss -ltn sport = :{port}"
        try:
            result = ssh.run_command(cmd, timeout=10)
        except (SSHConnectionError, SSHCommandError):
            return False
        if result.exit_code != 0 or not result.stdout.strip():
            return False
    return True


def stop_server(ssh: SSHClientWrapper, server: CarlaServerProcess) -> None:
    """Attempt to stop a running CARLA process or tmux session."""
    if server.session_type == "tmux" and server.session_name:
        ssh.run_command(f"tmux kill-session -t {server.session_name}")
    elif server.pid:
        ssh.run_command(f"kill {server.pid}")


def ensure_tunnel(ssh: SSHClientWrapper, mappings: List[PortMapping]) -> None:
    """Create the local tunnel for CARLA ports."""
    ssh.start_tunnel(mappings)
