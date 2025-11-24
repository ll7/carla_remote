from datetime import datetime, timezone

from src.services import carla_start
from src.services.ssh_client import SSHCommandResult


class FakeSSH:
    def __init__(self, exit_code: int = 0, stdout: str = ""):
        self.exit_code = exit_code
        self.stdout = stdout
        self.commands: list[str] = []

    def run_command(self, command: str, timeout: int | None = None) -> SSHCommandResult:
        self.commands.append(command)
        return SSHCommandResult(exit_code=self.exit_code, stdout=self.stdout, stderr="")


def test_detect_tmux_session_returns_process():
    ssh = FakeSSH(exit_code=0, stdout="")
    session = carla_start.detect_tmux_session(ssh, session_name="carla-server")
    assert session is not None
    assert session.session_type == "tmux"
    assert session.state == "RUNNING"


def test_start_carla_server_tmux_sets_session(monkeypatch):
    ssh = FakeSSH(exit_code=0, stdout="")
    monkeypatch.setattr(carla_start, "verify_ports", lambda ssh, remote_ports: True)
    server = carla_start.start_carla_server(
        ssh,
        install_path="/opt/carla",
        use_tmux=True,
        session_name="carla-server",
        remote_ports=[2000, 2001, 2002],
    )
    assert server.session_type == "tmux"
    assert server.state == "RUNNING"
    assert any("tmux new" in cmd for cmd in ssh.commands)


def test_stop_server_kills_tmux_session():
    ssh = FakeSSH(exit_code=0, stdout="")
    server = carla_start.CarlaServerProcess(
        pid=None,
        session_type="tmux",
        session_name="carla-session",
        state="RUNNING",
        started_at=datetime.now(timezone.utc),
        ports=[2000, 2001, 2002],
    )
    carla_start.stop_server(ssh, server)
    assert any("tmux kill-session -t carla-session" in cmd for cmd in ssh.commands)
