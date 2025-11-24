---
description: "Task list for SSH-Based CARLA Remote Server Startup"
---

# Tasks: SSH-Based CARLA Remote Server Startup

**Input**: specs/001-ssh-carla-startup design artifacts  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md  
**Tests**: Required per plan (pytest: unit, contract, integration)  
**Organization**: Tasks grouped by user story to keep each story independently testable.

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 Create project structure for src/cli, src/services, src/models, src/logging, tests/unit, tests/integration, tests/contract directories.
- [ ] T002 Add runtime and test dependencies (paramiko, pytest, typing extensions) in pyproject.toml and refresh uv.lock.
- [ ] T003 Update .gitignore to cover Python artifacts (.venv/, __pycache__/, *.pyc, dist/) in .gitignore.

---

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T004 Implement structured JSON logging helpers with timestamp/level/component fields in src/logging/structured.py.
- [ ] T005 Define dataclasses for SSHConnection, CarlaInstallState, CarlaServerProcess, PortMapping, ExecutionLogEntry in src/models/entities.py.
- [ ] T006 Implement local port probing and remap suggestion utilities for CARLA ports 2000-2002 in src/services/ports.py.
- [ ] T007 Implement SSH client abstraction using Paramiko for commands and subprocess ssh for tunnels with cleanup handling in src/services/ssh_client.py.

---

## Phase 3: User Story 1 - Interactive Remote Startup (Priority: P1) 🎯 MVP

Goal: Let a user start CARLA on a remote host with interactive prompts, port forwarding, detection of existing server, and clean logging without persisting secrets.  
Independent Test: Run CLI against localhost loopback; verify prompts, port forwarding 2000-2002 (or remap), CARLA process start/detect, structured logs, and cleanup on Ctrl+C.

### Tests for User Story 1

- [ ] T008 [P] [US1] Write contract test for CLI prompt sequence and responses per contracts/cli-contract.json in tests/contract/test_cli_contract.py.
- [ ] T009 [P] [US1] Write unit tests for port probing/remap decision logic in tests/unit/test_ports.py.
- [ ] T010 [P] [US1] Write unit tests for SSH client connect/command/tunnel error handling in tests/unit/test_ssh_client.py.

### Implementation for User Story 1

- [ ] T011 [US1] Implement interactive CLI flow (host/user prompts, no persistence, Ctrl+C cleanup) in src/cli/remote_carla_start.py.
- [ ] T012 [US1] Integrate port conflict detection and remap prompts using ports service in src/cli/remote_carla_start.py.
- [ ] T013 [US1] Implement CARLA process detection/startup with tunnel creation and remote health verification in src/services/carla_start.py.
- [ ] T014 [US1] Add structured logging and error code mapping for SSH/connect/start outcomes in src/cli/remote_carla_start.py.
- [ ] T015 [US1] Add integration test simulating remote startup via localhost and verifying forwarded ports in tests/integration/test_end_to_end_local_loopback.py.

Checkpoint: User Story 1 independently delivers remote startup with port forwarding and logging.

---

## Phase 4: User Story 2 - Installation Detection & Download (Priority: P2)

Goal: Detect existing CARLA installations, list versions, and optionally download/install when missing.  
Independent Test: Point CLI at a host without CARLA (simulated via mocks) and verify detection, user prompt, download/install flow, and post-install verification before startup.

### Tests for User Story 2

- [ ] T016 [P] [US2] Write unit tests for installation detection/version selection and path validation in tests/unit/test_carla_detect.py.

### Implementation for User Story 2

- [ ] T017 [US2] Implement CARLA installation detection with multiple-version handling and UNKNOWN fallback in src/services/carla_detect.py.
- [ ] T018 [US2] Add interactive download/install flow with disk space check and retry guidance in src/services/carla_detect.py.
- [ ] T019 [US2] Wire CLI to carla_detect results (prompt install, pass install path into startup) in src/cli/remote_carla_start.py.

Checkpoint: User Story 2 independently enables first-time setup with guided install.

---

## Phase 5: User Story 3 - Persistent Session Management (Priority: P3)

Goal: Keep CARLA running in a detached tmux session, allow reattach, and support graceful shutdown.  
Independent Test: Start CARLA in tmux, detach, reconnect, attach or stop; verify session detection and cleanup.

### Tests for User Story 3

- [ ] T020 [P] [US3] Extend unit tests for tmux session lifecycle (start/detect/attach/stop) in tests/unit/test_carla_start.py.

### Implementation for User Story 3

- [ ] T021 [US3] Implement tmux-based persistent session management with status checks in src/services/carla_start.py.
- [ ] T022 [US3] Update CLI to reuse/attach/restart or stop persistent sessions with clear prompts in src/cli/remote_carla_start.py.

Checkpoint: User Story 3 independently delivers persistent session controls.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T023 Add updated quickstart instructions covering install flow, tmux usage, and test commands in specs/001-ssh-carla-startup/quickstart.md.
- [ ] T024 Add troubleshooting and security notes (no credential persistence, port conflict guidance) to README.md.

---

## Dependencies & Execution Order

- Phase dependencies: Setup → Foundational → US1 → US2 → US3 → Polish.
- User stories are independent after Foundational; US1 is MVP and should land before P2/P3.
- Within each story: tests precede implementation; models/services before CLI wiring.

## Parallel Execution Examples

- Foundational: Ports service (T006) and SSH client (T007) can be built in parallel once logging/entities exist.
- User Story 1 tests (T008-T010) can run in parallel; T012 can proceed while T013 is in progress if interfaces agreed.
- User Story 2 detection (T017) and download flow (T018) can iterate together once test scaffolding (T016) is ready.
- User Story 3 tmux handling (T021) and CLI wiring (T022) can be parallelized after T020 test scaffolding.

## Implementation Strategy

1) Deliver MVP by completing Setup → Foundational → User Story 1 and running tests.  
2) Add installation flow (User Story 2) and validate independently.  
3) Layer persistent sessions (User Story 3) and finalize documentation/polish.
