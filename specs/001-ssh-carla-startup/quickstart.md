# Quickstart: Remote CARLA Server Startup

## Prerequisites
- Local machine: Python 3.13+, SSH client available (`ssh` in PATH)
- Remote machine: Ubuntu 22.04+ with SSH access and user having execution permissions
- SSH keys configured (no passwords; agent forwarding optional)
- Sufficient remote disk space (~20GB if installing CARLA)

## Install Dependencies (Local)

```bash
pip install paramiko pytest
```

(Additional dependencies added later via pyproject when implementing.)

## First Use

```bash
python -m src.cli.remote_carla_start
```

### Interactive Prompts
1. Remote host/IP
2. SSH username
3. Whether CARLA is already installed
4. If absent, confirmation to download
5. Use persistent tmux session?

## Successful Outcome
- SSH tunnel established mapping remote 2000-2002 → local ports
- CARLA server process running (tmux session if selected)
- Structured JSON logs printed to stdout

## Verifying Server
In separate terminal:
```bash
lsof -iTCP:2000 -sTCP:LISTEN
```
Or connect via CARLA Python client in another script.

## Stopping Server
Re-run script; it will detect existing session and offer shutdown.
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

## Next Steps
- Implement CLI script per contracts/cli-contract.json
- Add unit & integration tests before first implementation commit
