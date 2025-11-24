from datetime import datetime, timezone

from src.cli import remote_carla_start
from src.models.entities import CarlaServerProcess, PortMapping
from src.services.ssh_client import SSHCommandResult


def test_end_to_end_local_loopback(monkeypatch):
    # Always report ports available to skip remap prompts
    monkeypatch.setattr(
        remote_carla_start.ports,
        "probe_ports",
        lambda: [
            PortMapping(remote_port=2000, local_port=2000, status="AVAILABLE"),
            PortMapping(remote_port=2001, local_port=2001, status="AVAILABLE"),
            PortMapping(remote_port=2002, local_port=2002, status="AVAILABLE"),
        ],
    )
    monkeypatch.setattr(remote_carla_start.ports, "all_available", lambda mappings: True)

    recorded_tunnels: list[PortMapping] = []

    def fake_ensure_tunnel(wrapper, mappings):
        recorded_tunnels.extend(mappings)

    monkeypatch.setattr(remote_carla_start.carla_start, "ensure_tunnel", fake_ensure_tunnel)
    monkeypatch.setattr(remote_carla_start.carla_start, "detect_running_server", lambda wrapper: None)

    fake_server = CarlaServerProcess(
        pid=4321,
        session_type="none",
        session_name=None,
        state="RUNNING",
        started_at=datetime.now(timezone.utc),
        ports=[2000, 2001, 2002],
    )
    monkeypatch.setattr(
        remote_carla_start.carla_start,
        "start_carla_server",
        lambda wrapper, install_path, use_tmux, session_name, remote_ports: fake_server,
    )

    class FakeSSH(remote_carla_start.SSHClientWrapper):
        def __init__(self, host, user, *args, **kwargs):
            self.host = host
            self.user = user
            self.connected = False
            self.closed = False

        def connect(self):
            self.connected = True
            return None

        def run_command(self, command, timeout=None):
            return SSHCommandResult(exit_code=0, stdout="", stderr="")

        def start_tunnel(self, mappings, remote_host="localhost"):
            return None

        def close(self):
            self.closed = True

    monkeypatch.setattr(remote_carla_start, "SSHClientWrapper", FakeSSH)

    runner = remote_carla_start.RemoteCarlaRunner()
    inputs = remote_carla_start.UserInputs(
        host="127.0.0.1",
        user="local",
        carla_installed=True,
        proceed_download=False,
        use_tmux=False,
    )

    connection = runner.execute(inputs, dry_run=False)

    assert connection.status == "CONNECTED"
    assert recorded_tunnels  # ensure tunnel setup attempted
