# carla-remote

Interactive CLI to start a remote CARLA server over SSH with port forwarding, optional installation, and tmux-based persistence.

## Usage
- Collect inputs only: `uv run --extra dev python -m src.cli.remote_carla_start --dry-run`
- Full run: `uv run --extra dev python -m src.cli.remote_carla_start`
- Tests: `uv run --extra dev pytest -q`

## Security Notes
- Prompts for host/user and install choices at runtime; nothing is written to disk.
- SSH key-based auth only; passwords are not stored or accepted.
- Ctrl+C triggers cleanup for tunnels and any session the script started.

## Troubleshooting
- `SSH_CONN_FAIL`: verify key permissions and direct `ssh user@host`.
- `PORT_CONFLICT`: accept remap suggestion or free ports 2000-2002.
- `CARLA_START_TIMEOUT`: check remote GPU/driver and CARLA install integrity.
- `INSTALL_ABORTED`: rerun and opt into download, or install CARLA manually.
