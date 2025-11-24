import pytest

from src.services import carla_detect
from src.services.ssh_client import SSHCommandError, SSHCommandResult


class FakeSSH:
    def __init__(self, stdout: str = "", exit_code: int = 0, raise_exc: Exception | None = None):
        self.stdout = stdout
        self.exit_code = exit_code
        self.raise_exc = raise_exc
        self.commands: list[str] = []

    def run_command(self, command: str, timeout: int | None = None) -> SSHCommandResult:
        self.commands.append(command)
        if self.raise_exc:
            raise self.raise_exc
        return SSHCommandResult(exit_code=self.exit_code, stdout=self.stdout, stderr="")


def test_detect_installation_detects_primary_path():
    fake = FakeSSH(stdout="/opt/carla/CarlaUE4.sh\n")
    state = carla_detect.detect_installation(fake, search_paths=["/opt"])
    assert state.detected
    assert state.path == "/opt/carla/CarlaUE4.sh"


def test_detect_installation_handles_errors():
    fake = FakeSSH(raise_exc=SSHCommandError("unreachable"))
    state = carla_detect.detect_installation(fake, search_paths=["/opt"])
    assert not state.detected


def test_download_and_install_checks_disk_space(monkeypatch):
    fake = FakeSSH(stdout="", exit_code=0)
    monkeypatch.setattr(carla_detect, "check_disk_space", lambda ssh, required_gb=20: False)
    state = carla_detect.download_and_install(fake, download_url="http://example.com/carla.tar.gz")
    assert not state.detected


def test_interactive_install_respects_user_decline(monkeypatch):
    fake = FakeSSH(stdout="", exit_code=0)
    monkeypatch.setattr(carla_detect, "check_disk_space", lambda ssh, required_gb=20: False)
    called = {"download": False}

    def fake_download(*args, **kwargs):
        called["download"] = True
        return carla_detect.CarlaInstallState(detected=True, path="/opt/carla", version="UNKNOWN")

    monkeypatch.setattr(carla_detect, "download_and_install", fake_download)
    state = carla_detect.interactive_install(fake, download_url="http://example.com", input_fn=lambda prompt="": "n")

    assert not state.detected
    assert called["download"] is False
