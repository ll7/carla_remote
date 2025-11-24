from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

import paramiko

from src.models.entities import PortMapping


class SSHConnectionError(Exception):
    """Raised when the SSH connection cannot be established."""


class SSHCommandError(Exception):
    """Raised when a remote command fails."""


class SSHTunnelError(Exception):
    """Raised when the SSH tunnel fails to start or dies unexpectedly."""


@dataclass
class SSHCommandResult:
    exit_code: int
    stdout: str
    stderr: str


class SSHClientWrapper:
    def __init__(
        self,
        host: str,
        user: str,
        *,
        port: int = 22,
        identity_file: Optional[str] = None,
        connect_timeout: int = 15,
    ) -> None:
        self.host = host
        self.user = user
        self.port = port
        self.identity_file = identity_file
        self.connect_timeout = connect_timeout
        self._client: Optional[paramiko.SSHClient] = None
        self._tunnel_proc: Optional[subprocess.Popen[bytes]] = None

    def connect(self) -> paramiko.SSHClient:
        if self._client:
            return self._client
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                hostname=self.host,
                username=self.user,
                port=self.port,
                timeout=self.connect_timeout,
                allow_agent=True,
                look_for_keys=True,
            )
        except Exception as exc:  # noqa: BLE001 - surface full SSH errors
            raise SSHConnectionError(str(exc)) from exc
        self._client = client
        return client

    def run_command(self, command: str, *, timeout: Optional[int] = None) -> SSHCommandResult:
        client = self.connect()
        try:
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        except Exception as exc:  # noqa: BLE001
            raise SSHCommandError(str(exc)) from exc

        exit_code = stdout.channel.recv_exit_status()
        stdout_str = stdout.read().decode()
        stderr_str = stderr.read().decode()
        return SSHCommandResult(exit_code=exit_code, stdout=stdout_str, stderr=stderr_str)

    def start_tunnel(self, mappings: Iterable[PortMapping], remote_host: str = "localhost") -> subprocess.Popen[bytes]:
        if self._tunnel_proc and self._tunnel_proc.poll() is None:
            return self._tunnel_proc

        cmd: List[str] = [
            "ssh",
            "-N",
            "-o",
            "ExitOnForwardFailure=yes",
            "-o",
            "ServerAliveInterval=30",
            "-o",
            "ServerAliveCountMax=3",
            "-p",
            str(self.port),
        ]
        if self.identity_file:
            cmd.extend(["-i", self.identity_file])
        for mapping in mappings:
            cmd.extend(["-L", f"{mapping.local_port}:{remote_host}:{mapping.remote_port}"])
        cmd.append(f"{self.user}@{self.host}")

        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError as exc:
            raise SSHTunnelError("ssh binary not found in PATH") from exc
        except Exception as exc:  # noqa: BLE001
            raise SSHTunnelError(str(exc)) from exc

        if not self._wait_for_tunnel_start(proc):
            stderr_output = ""
            if proc.stderr:
                try:
                    stderr_output = proc.stderr.read().decode()
                except Exception:  # noqa: BLE001
                    stderr_output = ""
            raise SSHTunnelError(stderr_output or "failed to start ssh tunnel")

        self._tunnel_proc = proc
        return proc

    def _wait_for_tunnel_start(self, proc: subprocess.Popen[bytes], timeout: int = 10) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            if proc.poll() is not None:
                return False
            # If process is running and not exiting quickly, assume success
            time.sleep(0.2)
        return proc.poll() is None

    def stop_tunnel(self) -> None:
        if self._tunnel_proc and self._tunnel_proc.poll() is None:
            self._tunnel_proc.terminate()
            try:
                self._tunnel_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._tunnel_proc.kill()
        self._tunnel_proc = None

    def close(self) -> None:
        if self._client:
            self._client.close()
        self.stop_tunnel()
        self._client = None
