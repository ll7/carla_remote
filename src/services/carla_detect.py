from __future__ import annotations

from typing import Callable, Iterable, Optional, Sequence

from src.logging.structured import log_event
from src.models.entities import CarlaInstallState
from src.services.ssh_client import SSHClientWrapper, SSHCommandError, SSHConnectionError

DEFAULT_SEARCH_PATHS: Sequence[str] = ("/opt", "$HOME")
DEFAULT_REQUIRED_DISK_GB = 20


def detect_installation(
    ssh: SSHClientWrapper,
    search_paths: Iterable[str] = DEFAULT_SEARCH_PATHS,
) -> CarlaInstallState:
    """Locate CarlaUE4.sh on the remote host."""
    paths = " ".join(search_paths)
    find_cmd = f"set -e; find {paths} -maxdepth 4 -name CarlaUE4.sh -type f 2>/dev/null"
    try:
        result = ssh.run_command(find_cmd, timeout=15)
    except (SSHConnectionError, SSHCommandError):
        return CarlaInstallState(detected=False, version="UNKNOWN")

    installs = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not installs:
        return CarlaInstallState(detected=False, version="UNKNOWN")

    primary = installs[0]
    multiple = len(installs) > 1
    return CarlaInstallState(
        detected=True,
        path=primary,
        version="UNKNOWN",
        multiple_versions=multiple,
        selectable_versions=installs if multiple else [primary],
    )


def check_disk_space(ssh: SSHClientWrapper, *, required_gb: int = DEFAULT_REQUIRED_DISK_GB) -> bool:
    """Return True if remote host has at least required_gb available."""
    cmd = "df -BG --output=avail . | tail -1 | tr -dc '0-9'"
    try:
        result = ssh.run_command(cmd, timeout=10)
    except (SSHConnectionError, SSHCommandError):
        return False
    try:
        available_gb = int(result.stdout.strip() or 0)
    except ValueError:
        return False
    return available_gb >= required_gb


def download_and_install(
    ssh: SSHClientWrapper,
    *,
    download_url: str,
    target_dir: str = "$HOME/carla",
    require_disk_space: bool = True,
    logger=log_event,
) -> CarlaInstallState:
    """
    Download and extract CARLA on the remote host.
    Command is intentionally explicit and avoids persistence of secrets.
    """
    if require_disk_space and not check_disk_space(ssh):
        logger(
            "carla_install",
            "insufficient_disk_space",
            level="ERROR",
            outcome="failure",
            details={"required_gb": DEFAULT_REQUIRED_DISK_GB},
        )
        return CarlaInstallState(detected=False, version="UNKNOWN")

    install_cmd = (
        f"set -e; mkdir -p {target_dir}; "
        f"cd {target_dir}; "
        f"wget -q {download_url} -O carla.tar.gz; "
        f"tar -xzf carla.tar.gz; "
        f"rm -f carla.tar.gz"
    )
    logger("carla_install", "download_start", details={"target_dir": target_dir, "url": download_url})
    try:
        result = ssh.run_command(install_cmd, timeout=600)
    except (SSHConnectionError, SSHCommandError) as exc:
        logger("carla_install", "download_failed", level="ERROR", outcome="failure", details={"error": str(exc)})
        return CarlaInstallState(detected=False, version="UNKNOWN")

    if result.exit_code != 0:
        logger(
            "carla_install",
            "download_failed",
            level="ERROR",
            outcome="failure",
            details={"stderr": result.stderr},
        )
        return CarlaInstallState(detected=False, version="UNKNOWN")

    state = detect_installation(ssh, search_paths=[target_dir])
    logger("carla_install", "download_complete", details={"detected": state.detected, "path": state.path})
    return state


def interactive_install(
    ssh: SSHClientWrapper,
    *,
    download_url: str,
    target_dir: str = "$HOME/carla",
    input_fn: Optional[Callable[[str], str]] = None,
    logger=log_event,
) -> CarlaInstallState:
    prompt = input_fn or input
    if not check_disk_space(ssh):
        proceed = prompt(
            f"Remote host reports less than {DEFAULT_REQUIRED_DISK_GB}GB free. Attempt download anyway? (y/n): "
        ).strip().lower()
        if not proceed.startswith("y"):
            return CarlaInstallState(detected=False, version="UNKNOWN")

    confirm = prompt(f"Download CARLA to {target_dir}? (y/n): ").strip().lower()
    if not confirm.startswith("y"):
        return CarlaInstallState(detected=False, version="UNKNOWN")

    return download_and_install(
        ssh,
        download_url=download_url,
        target_dir=target_dir,
        require_disk_space=False,
        logger=logger,
    )
