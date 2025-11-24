# Implementation Plan: SSH-Based CARLA Remote Server Startup

**Branch**: `001-ssh-carla-startup` | **Date**: 2025-11-21 | **Spec**: `specs/001-ssh-carla-startup/spec.md`
**Input**: Feature specification from `specs/001-ssh-carla-startup/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Enable researchers to start, detect, and (if missing) install a CARLA simulation server on a remote Ubuntu host via an interactive, security-safe SSH script that forwards required ports (2000-2002), never persists credentials, and optionally runs the server in a persistent session (screen/tmux). Technical approach (post research): use Paramiko for SSH, fallback to native `ssh` subprocess for tunneling reliability, CARLA version detection via filesystem probe (`CarlaUE4.sh` / `CarlaUE4.exe` not used on Ubuntu), persistent session with `tmux` (preferred over `screen` for session introspection), port availability checks performed locally before establishing tunnel.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.13+
**Primary Dependencies**: NEEDS CLARIFICATION (Paramiko vs native `ssh`; tmux vs screen) → resolved in research
**Storage**: N/A (no persistence; ephemeral runtime only)
**Testing**: pytest (unit with mocks for SSH, integration using localhost loopback or containerized Ubuntu)
**Target Platform**: Local macOS client; Remote Ubuntu 22.04+ server running CARLA
**Project Type**: single (scripts + src modules + tests)
**Performance Goals**: Remote startup < 60s when CARLA already installed; tunnel establishment < 5s
**Constraints**: ZERO credential persistence; robust interruption cleanup; minimal external dependencies
**Scale/Scope**: Single-user tooling; limited code footprint (<2k LOC initial feature)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status (Pre-Research) | Status (Post-Design) | Notes |
|-----------|------|-----------------------|----------------------|-------|
| Remote-First Architecture | Remote host configurable | PASS | PASS | Design enforces host as input |
| SSH Infrastructure Management | Interactive script + port forwarding plan | PASS | PASS | Contract JSON defined |
| Test-First Development | Tests before implementation | PASS | PASS | Test file list defined in structure |
| Experiment Reproducibility | Log startup metadata | PASS | PASS | Data model includes log entity |
| Observability & Structured Logging | Structured JSON logs planned | PASS | PASS | logging/structured.py placeholder included |

No violations; complexity tracking section not required at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── cli/
│   └── remote_carla_start.py        # Entry script (interactive)
├── services/
│   ├── ssh_client.py               # Abstraction over Paramiko / subprocess
│   ├── carla_detect.py             # Installation/version detection
│   ├── carla_start.py              # Startup & persistent session logic
│   └── ports.py                    # Port probing & tunnel setup
├── models/
│   └── entities.py                 # Dataclasses for Connection, Session, InstallState
└── logging/
    └── structured.py               # JSON logging helpers

tests/
├── unit/
│   ├── test_ports.py
│   ├── test_carla_detect.py
│   ├── test_ssh_client.py
│   └── test_carla_start.py
├── integration/
│   └── test_end_to_end_local_loopback.py  # Uses localhost to simulate remote
└── contract/
    └── test_cli_contract.py
```

**Structure Decision**: Single-project layout with focused service modules; separation keeps remote orchestration concerns testable and aligns with constitution (independent, observable components).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | All gates pass | N/A |
