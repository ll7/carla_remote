import io
from typing import Any

import pytest

from src.services import ssh_client
from src.services.ssh_client import (
    SSHClientWrapper,
    SSHCommandError,
    SSHCommandResult,
    SSHConnectionError,
    SSHTunnelError,
)


class DummyChannel:
    def __init__(self, exit_code: int) -> None:
        self._exit_code = exit_code

    def recv_exit_status(self) -> int:
        return self._exit_code


class DummyStream(io.BytesIO):
    def __init__(self, data: bytes, exit_code: int = 0) -> None:
        super().__init__(data)
        self.channel = DummyChannel(exit_code)


class DummySSH:
    def __init__(self) -> None:
        self.connected = False
        self.commands: list[str] = []

    def load_system_host_keys(self) -> None:  # pragma: no cover - no-op for stub
        return None

    def set_missing_host_key_policy(self, policy: Any) -> None:  # pragma: no cover - no-op for stub
        return None

    def connect(self, **_: Any) -> None:
        self.connected = True

    def exec_command(self, command: str, timeout: int | None = None):  # type: ignore[override]
        self.commands.append(command)
        return None, DummyStream(b"ok"), DummyStream(b"", 0)

    def close(self) -> None:  # pragma: no cover - no-op for stub
        self.connected = False


def test_run_command_returns_output(monkeypatch):
    monkeypatch.setattr(ssh_client.paramiko, "SSHClient", lambda: DummySSH())
    wrapper = SSHClientWrapper("example.com", "ubuntu", connect_timeout=1)
    result: SSHCommandResult = wrapper.run_command("echo hello")
    assert result.exit_code == 0
    assert "ok" in result.stdout
    assert result.stderr == ""


def test_connect_failure_raises(monkeypatch):
    class FailingSSH(DummySSH):
        def connect(self, **_: Any) -> None:
            raise RuntimeError("unreachable")

    monkeypatch.setattr(ssh_client.paramiko, "SSHClient", lambda: FailingSSH())
    wrapper = SSHClientWrapper("badhost", "ubuntu", connect_timeout=1)
    with pytest.raises(SSHConnectionError):
        wrapper.connect()


def test_start_tunnel_builds_command(monkeypatch):
    monkeypatch.setattr(ssh_client.paramiko, "SSHClient", lambda: DummySSH())
    captured_args: list[str] = []

    class DummyProc:
        def __init__(self, args: list[str]) -> None:
            self.args = args
            self.stderr = None

        def poll(self) -> int | None:
            return None

        def wait(self, timeout: int | None = None) -> int:
            return 0

    def fake_popen(args, stdout=None, stderr=None):  # type: ignore[override]
        captured_args.extend(args)
        return DummyProc(args)

    monkeypatch.setattr(ssh_client.subprocess, "Popen", fake_popen)
    wrapper = SSHClientWrapper("example.com", "ubuntu")
    monkeypatch.setattr(wrapper, "_wait_for_tunnel_start", lambda proc, timeout=10: True)

    mappings = [
        ssh_client.PortMapping(remote_port=2000, local_port=2000, status="AVAILABLE"),
        ssh_client.PortMapping(remote_port=2001, local_port=2001, status="AVAILABLE"),
    ]
    proc = wrapper.start_tunnel(mappings)
    assert isinstance(proc, DummyProc)
    assert "-L" in captured_args
    assert any("2000:localhost:2000" in arg for arg in captured_args)


def test_start_tunnel_missing_binary_raises(monkeypatch):
    monkeypatch.setattr(ssh_client.paramiko, "SSHClient", lambda: DummySSH())

    def failing_popen(*args, **kwargs):  # type: ignore[override]
        raise FileNotFoundError("ssh missing")

    monkeypatch.setattr(ssh_client.subprocess, "Popen", failing_popen)
    wrapper = SSHClientWrapper("example.com", "ubuntu")
    with pytest.raises(SSHTunnelError):
        wrapper.start_tunnel(
            [ssh_client.PortMapping(remote_port=2000, local_port=2000, status="AVAILABLE")]
        )
