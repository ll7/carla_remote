# Data Model: SSH-Based CARLA Remote Server Startup

## Entities

### SSHConnection
| Field | Type | Description |
|-------|------|-------------|
| host | str | Remote Ubuntu host/IP provided interactively |
| user | str | SSH username provided interactively |
| ports_forwarded | list[int] | Local ports mapped to remote CARLA ports |
| tunnel_pid | int | PID of local ssh tunnel process (if using subprocess) |
| status | str | one of: INIT, CONNECTED, FAILED, CLOSED |
| started_at | datetime | Timestamp when connection established |
| last_check | datetime | Last health check timestamp |

### CarlaInstallState
| Field | Type | Description |
| detected | bool | True if installation found |
| path | str | Root path of CARLA installation |
| version | str | Version string or "UNKNOWN" |
| multiple_versions | bool | True if more than one install detected |
| selectable_versions | list[str] | Versions user may choose from |

### CarlaServerProcess
| Field | Type | Description |
| pid | int | Remote process PID (if discoverable) |
| session_type | str | tmux | none |
| session_name | str | Name of tmux session if used |
| state | str | one of: STARTING, RUNNING, STOPPED, ERROR |
| started_at | datetime | Start timestamp |
| ports | list[int] | Remote ports in use (expected: 2000-2002) |

### PortMapping
| Field | Type | Description |
| remote_port | int | Target port on remote host |
| local_port | int | Mapped port on localhost |
| status | str | AVAILABLE | CONFLICT | MAPPED |
| conflict_reason | str | If conflict detected (process, permission) |

### ExecutionLogEntry
| Field | Type | Description |
| timestamp | datetime | Event time |
| level | str | INFO | WARN | ERROR |
| component | str | ssh | carla | ports | session |
| action | str | Operation performed (connect, forward, detect, start, cleanup) |
| outcome | str | success | failure |
| details | dict | Additional structured info (e.g., ports used) |

## Relationships
- SSHConnection 1--* PortMapping
- CarlaServerProcess 1--* PortMapping (expected three ports for 2000-2002 unless remapped)
- CarlaInstallState informs CarlaServerProcess startup flow
- ExecutionLogEntry aggregates across all entities (no direct containment)

## Validation Rules
- host MUST be non-empty and resolvable (basic IPv4/hostname regex before attempt)
- user MUST be non-empty
- ports_forwarded MUST map 1:1 with remote ports selected
- CarlaInstallState.detected FALSE ⇒ version == "UNKNOWN"
- CarlaServerProcess.state STARTING must transition to RUNNING, STOPPED, or ERROR within timeout (60s)
- PortMapping.status CONFLICT requires conflict_reason not empty

## State Transitions

CarlaServerProcess:
STARTING → RUNNING (successful launch)
STARTING → ERROR (launch failure)
RUNNING → STOPPED (user shutdown)
RUNNING → ERROR (unexpected termination)
ERROR → STARTING (retry scenario)

SSHConnection:
INIT → CONNECTED (successful handshake)
INIT → FAILED (authentication/network error)
CONNECTED → CLOSED (user exit / cleanup)
CONNECTED → FAILED (unexpected tunnel death)
FAILED → INIT (retry attempt)

## Notes
- No persistent storage layer; entities exist in-memory during script execution.
- Logging ensures reproducibility for RL session attribution even though experiment logic not yet in scope.
