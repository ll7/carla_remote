# Quickstart: Remote CARLA Server Startup

## Prerequisites
- Local machine: Python 3.13+, SSH client available (`ssh` in PATH)
- Remote machine: Ubuntu 22.04+ with SSH access and user having execution permissions
- SSH keys configured (no passwords; agent forwarding optional)
- Sufficient remote disk space (~20GB if installing CARLA)

## Install Dependencies (Local)

```bash
uv sync --extra dev
```

## First Use

```bash
python -m src.cli.remote_carla_start
# or dry run (collect prompts only)
python -m src.cli.remote_carla_start --dry-run
```

### Interactive Prompts
1. Remote host/IP
2. SSH username
3. Whether CARLA is already installed
4. If absent, confirmation to download
5. Use persistent tmux session?
6. If tmux session already exists: attach/reuse, restart, or stop

## Successful Outcome
- SSH tunnel established mapping remote 2000-2002 → local ports
- CARLA server process running (tmux session if selected)
- Structured JSON logs printed to stdout

## Installation Flow (when CARLA is missing)
- Script searches common paths for `CarlaUE4.sh`
- If not found and you opt in, it checks disk space (~20GB) then downloads and extracts CARLA to `$HOME/carla`
- You can decline install at any prompt; nothing is persisted locally

## Persistent Sessions (tmux)
- Choose tmux when prompted to keep the server alive after disconnect
- On rerun, the script detects the tmux session and offers to attach/reuse, restart, or stop it
- Manual attach: `ssh user@host "tmux attach -t carla-server"`

## Verifying Server
In separate terminal:
```bash
lsof -iTCP:2000 -sTCP:LISTEN
```
Or connect via CARLA Python client in another script.

## Stopping Server
Re-run script; it will detect existing session and offer shutdown/restart/attach.
If tmux used:
```bash
tmux ls
tmux kill-session -t carla-server
```

## Safety & Security
- No credentials written to disk
- Host/user inputs remain memory-only
- Abort anytime with Ctrl+C (cleanup routine closes tunnel & session if owned)

## Troubleshooting
| Issue | Cause | Resolution |
|-------|-------|------------|
| SSH_CONN_FAIL | Network or auth | Check key permissions; run `ssh user@host` manually |
| PORT_CONFLICT | Local ports occupied | Choose remap offered by script |
| CARLA_START_TIMEOUT | Heavy startup or missing deps | Check remote GPU/driver; review logs |
| INSTALL_ABORTED | User declined install | Manually install CARLA and retry |

## Tests
- Run full suite: `uv run --extra dev pytest -q`
- Key files: `tests/contract/test_cli_contract.py`, `tests/unit/test_ports.py`, `tests/unit/test_ssh_client.py`, `tests/unit/test_carla_detect.py`, `tests/unit/test_carla_start.py`, `tests/integration/test_end_to_end_local_loopback.py`

## Next Steps
- Implement CLI script per contracts/cli-contract.json
- Add unit & integration tests before first implementation commit
