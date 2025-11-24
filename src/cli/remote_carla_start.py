from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Callable, List, Optional

from src.logging.structured import log_error, log_event
from src.models.entities import PortMapping, SSHConnection
from src.services import carla_detect, carla_start, ports
from src.services.ssh_client import SSHClientWrapper, SSHConnectionError, SSHCommandError, SSHTunnelError

ERROR_CODES = {
    SSHConnectionError: "SSH_CONN_FAIL",
    SSHTunnelError: "PORT_CONFLICT",
    carla_start.CarlaStartError: "CARLA_START_TIMEOUT",
    RuntimeError: "INSTALL_ABORTED",
}

InputFn = Callable[[str], str]


@dataclass
class UserInputs:
    host: str
    user: str
    carla_installed: bool
    proceed_download: bool
    use_tmux: bool


def collect_inputs(input_fn: Optional[InputFn] = None) -> UserInputs:
    prompt = input_fn or input
    host = prompt("Enter remote host (IP or hostname): ")
    user = prompt("Enter SSH username: ")
    installed = prompt("Is CARLA already installed? (y/n): ").strip().lower().startswith("y")
    proceed_download = prompt("If not installed, proceed with download? (y/n): ").strip().lower().startswith("y")
    use_tmux = prompt("Use persistent tmux session? (y/n): ").strip().lower().startswith("y")
    return UserInputs(
        host=host,
        user=user,
        carla_installed=installed,
        proceed_download=proceed_download,
        use_tmux=use_tmux,
    )


def select_port_mappings(input_fn: Optional[InputFn] = None) -> List[PortMapping]:
    prompt = input_fn or input
    mappings = ports.probe_ports()
    if ports.all_available(mappings):
        return mappings

    print("Port conflict detected for 2000-2002 on localhost.")
    remap = ports.suggest_remap()
    if remap:
        suggestion = ", ".join(str(mapping.local_port) for mapping in remap)
        confirm = prompt(f"Use alternative local ports [{suggestion}]? (y/n): ").strip().lower()
        if confirm.startswith("y"):
            return remap
    raise SSHTunnelError("No available local ports for forwarding")


class RemoteCarlaRunner:
    def __init__(self, input_fn: Optional[InputFn] = None) -> None:
        self.input_fn = input_fn or input
        self.ssh_wrapper: Optional[SSHClientWrapper] = None

    def _maybe_reuse_tmux(self, wrapper: SSHClientWrapper, mappings: List[PortMapping]) -> Optional[carla_start.CarlaServerProcess]:
        tmux_session = carla_start.detect_tmux_session(wrapper)
        if not tmux_session:
            return None

        choice = self.input_fn(
            "Persistent CARLA tmux session found. Attach/reuse (a), restart (r), or stop (s)? (a/r/s): "
        ).strip().lower()
        if choice.startswith("a"):
            carla_start.ensure_tunnel(wrapper, mappings)
            log_event("carla_start", "reuse_tmux_session", details={"session": tmux_session.session_name})
            return tmux_session
        if choice.startswith("s"):
            carla_start.stop_server(wrapper, tmux_session)
            log_event("carla_start", "stopped_tmux_session", details={"session": tmux_session.session_name})
            return None

        carla_start.stop_server(wrapper, tmux_session)
        log_event("carla_start", "restart_tmux_session", details={"session": tmux_session.session_name})
        return None

    def execute(self, user_inputs: UserInputs, *, dry_run: bool = False) -> SSHConnection:
        connection = SSHConnection(host=user_inputs.host, user=user_inputs.user)
        log_event(
            "cli",
            "inputs_collected",
            details={
                "host": user_inputs.host,
                "user": user_inputs.user,
                "carla_installed": user_inputs.carla_installed,
                "proceed_download": user_inputs.proceed_download,
                "use_tmux": user_inputs.use_tmux,
                "dry_run": dry_run,
            },
        )

        mappings = select_port_mappings(self.input_fn)
        connection.ports_forwarded = [mapping.local_port for mapping in mappings]

        if dry_run:
            log_event("cli", "dry_run_complete", details={"ports": connection.ports_forwarded})
            return connection

        wrapper = SSHClientWrapper(user_inputs.host, user_inputs.user)
        self.ssh_wrapper = wrapper
        try:
            wrapper.connect()
        except SSHConnectionError as exc:
            log_error("ssh", "connect_failed", str(exc))
            raise

        if not user_inputs.carla_installed:
            install_state = carla_detect.detect_installation(wrapper)
            if not install_state.detected and user_inputs.proceed_download:
                install_state = carla_detect.interactive_install(
                    wrapper,
                    download_url="https://carla-releases.s3.eu-west-3.amazonaws.com/Linux/CARLA_0.9.15.tar.gz",
                    input_fn=self.input_fn,
                )
            if not install_state.detected:
                raise RuntimeError("CARLA installation not found and install declined")
            install_path = install_state.path
        else:
            install_state = None
            install_path = None

        if user_inputs.use_tmux:
            reused_session = self._maybe_reuse_tmux(wrapper, mappings)
            if reused_session:
                connection.status = "CONNECTED"
                connection.started_at = reused_session.started_at
                log_event(
                    "carla_start",
                    "tmux_session_attached",
                    details={"ports": connection.ports_forwarded, "session": reused_session.session_name},
                )
                return connection

        existing = carla_start.detect_running_server(wrapper)
        if existing:
            reuse = self.input_fn("CARLA server already running. Reuse existing session? (y/n): ").strip().lower()
            if reuse.startswith("y"):
                carla_start.ensure_tunnel(wrapper, mappings)
                log_event("carla_start", "reuse_existing", details={"pid": existing.pid})
                return connection

        server = carla_start.start_carla_server(
            wrapper,
            install_path=install_path,
            use_tmux=user_inputs.use_tmux,
            session_name=carla_start.DEFAULT_SESSION_NAME,
            remote_ports=[mapping.remote_port for mapping in mappings],
        )
        carla_start.ensure_tunnel(wrapper, mappings)
        connection.status = "CONNECTED"
        connection.started_at = server.started_at
        log_event("carla_start", "server_running", details={"session": server.session_name, "ports": server.ports})
        return connection

    def cleanup(self) -> None:
        if self.ssh_wrapper:
            self.ssh_wrapper.close()
            self.ssh_wrapper = None


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Start remote CARLA server via SSH.")
    parser.add_argument("--dry-run", action="store_true", help="Collect inputs and exit without SSH actions.")
    args = parser.parse_args(argv)

    runner = RemoteCarlaRunner()
    try:
        user_inputs = collect_inputs()
        runner.execute(user_inputs, dry_run=args.dry_run)
        return 0
    except (KeyboardInterrupt, EOFError):
        print("\nInterrupted by user. Cleaning up...")
        runner.cleanup()
        return 1
    except (SSHConnectionError, SSHCommandError, SSHTunnelError, carla_start.CarlaStartError, RuntimeError) as exc:
        error_code = ERROR_CODES.get(exc.__class__)
        log_error("cli", "startup_failed", str(exc), error_code=error_code)
        runner.cleanup()
        return 1


if __name__ == "__main__":
    sys.exit(main())
