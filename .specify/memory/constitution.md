<!--
SYNC IMPACT REPORT
==================
Version Change: N/A → 1.0.0 (Initial Constitution)
Constitution Type: MINOR (Initial establishment of governance framework)

Modified Principles: N/A (new constitution)
Added Sections:
  - Core Principles (5 principles)
  - Technical Constraints
  - Development Workflow
  - Governance

Removed Sections: N/A

Templates Status:
  ✅ plan-template.md - Reviewed, compatible with constitution gates
  ✅ spec-template.md - Reviewed, aligns with user story prioritization
  ✅ tasks-template.md - Reviewed, supports test-first development workflow
  ⚠ No command-specific .md files found in .specify/templates/commands/

Follow-up TODOs:
  - Update README.md with project description and quick start guide
  - Create initial SSH connection management scripts
  - Document CARLA server setup process
-->

# carla-remote Constitution

## Core Principles

### I. Remote-First Architecture

All components MUST support operation with CARLA simulator running on a remote machine.
This principle ensures the project fulfills its core purpose of enabling distributed RL
training where compute-intensive simulation happens remotely while development and
experimentation happen locally.

**Non-negotiable rules:**
- No hardcoded localhost assumptions; all connections MUST be configurable
- Network failures MUST be handled gracefully with retries and timeouts
- Remote server state MUST be verifiable before starting experiments
- Port forwarding and SSH tunnel management MUST be automated

**Rationale:** CARLA simulator is resource-intensive. Remote execution is not optional—it
is the primary use case. Local-only implementations violate the project's purpose.

### II. SSH Infrastructure Management

The project MUST provide scripts to start, stop, and monitor CARLA servers on remote
machines via SSH, including automated port forwarding and connection management.

**Non-negotiable rules:**
- SSH connection scripts MUST support key-based authentication
- Port forwarding configuration MUST be explicit and documented
- Server startup scripts MUST verify CARLA is running before returning
- Connection health checks MUST be implemented
- All SSH operations MUST log to structured output for debugging

**Rationale:** Manual SSH tunnel management is error-prone and breaks experimental
workflows. Automation ensures reproducibility and reduces cognitive overhead.

### III. Test-First Development (NON-NEGOTIABLE)

Test-Driven Development is mandatory: Tests written → User approved → Tests fail → Then
implement. This applies to RL environments, SSH connection logic, and all infrastructure
code.

**Non-negotiable rules:**
- Red-Green-Refactor cycle strictly enforced
- No implementation without failing tests first
- Integration tests required for SSH/network components
- RL environment tests MUST verify state transitions and rewards
- Mock remote servers for unit testing

**Rationale:** Distributed systems and RL code are notoriously difficult to debug.
TDD catches integration issues early and ensures components work in isolation.

### IV. Experiment Reproducibility

All RL experiments MUST be reproducible through version-controlled configuration,
deterministic random seeds, and environment state snapshots.

**Non-negotiable rules:**
- Every experiment run MUST log: random seeds, hyperparameters, CARLA version,
  environment configuration
- Configuration files MUST be versioned alongside code
- Experiment results MUST include timestamp, commit hash, and environment fingerprint
- CARLA server version MUST be documented and pinned per experiment

**Rationale:** Reinforcement learning research requires reproducibility to validate
results, debug failures, and compare approaches. Non-reproducible experiments waste
compute resources and research time.

### V. Observability & Structured Logging

All components MUST use structured logging with clear severity levels. Distributed
system interactions (SSH, port forwarding, CARLA API calls) MUST be observable through
logs.

**Non-negotiable rules:**
- Use Python logging with JSON-structured output for machine parsing
- Log all SSH connection attempts, successes, and failures with timestamps
- Log CARLA server health checks and API responses
- RL training loops MUST log episode metrics (reward, steps, termination reason)
- ERROR logs MUST include context for debugging (host, port, operation)

**Rationale:** Debugging distributed RL systems requires visibility into both local and
remote state. Structured logs enable automated analysis and alerting.

## Technical Constraints

**Language & Version**: Python 3.13+ (as specified in pyproject.toml)

**Core Dependencies**:
- SSH client library (paramiko or fabric) for remote server management
- CARLA Python API (version must match remote server)
- RL framework (gymnasium/gym for environment interface)
- pytest for testing infrastructure

**Network Requirements**:
- SSH access to remote CARLA server
- Port forwarding for CARLA client API (typically port 2000-2002)
- Configurable timeout and retry policies

**Testing Standards**:
- pytest for all test execution
- Mock SSH servers for unit testing connection logic
- Integration tests against actual CARLA instances (can be local for CI)
- Snapshot-based testing for environment reproducibility

**Documentation Requirements**:
- README MUST include remote server setup instructions
- SSH configuration examples MUST be provided
- Troubleshooting guide for common connection failures
- Environment configuration schema documentation

## Development Workflow

**Constitution Compliance Gate**: All PRs MUST verify that:
- Remote-first architecture is preserved (no localhost hardcoding)
- SSH scripts are tested and handle errors
- Tests are written before implementation
- Experiment configurations are versioned
- Structured logging is used

**Code Review Requirements**:
- Network/SSH code requires manual testing notes in PR description
- RL environment changes require reproducibility verification
- Breaking changes to experiment configuration MUST be documented

**Quality Gates**:
- All tests MUST pass before merge
- SSH connection tests MUST succeed against mock server
- No print statements in production code (use logging)
- Type hints required for all public interfaces

**Versioning Policy**:
- Semantic versioning (MAJOR.MINOR.PATCH)
- MAJOR: Breaking changes to SSH API, experiment configuration format, or RL interface
- MINOR: New features (new RL environments, additional SSH utilities)
- PATCH: Bug fixes, documentation, logging improvements

## Governance

**Authority**: This constitution supersedes all other development practices and coding
conventions. When in conflict, constitution principles take precedence.

**Amendment Process**:
- Amendments require documented justification and impact analysis
- Version bump according to semantic versioning rules
- Migration plan required for breaking governance changes
- Update all dependent templates and documentation

**Compliance Enforcement**:
- All PRs and code reviews MUST verify compliance with core principles
- Violations MUST be justified with documented trade-offs
- Technical debt that violates principles MUST have remediation plan

**Complexity Justification**:
- Any deviation from principles MUST be documented in implementation plan
- Complexity introduced for performance, security, or external constraints requires
  explicit approval

**Version**: 1.0.0 | **Ratified**: 2025-11-21 | **Last Amended**: 2025-11-21
