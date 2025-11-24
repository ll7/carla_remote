# Research: SSH-Based CARLA Remote Server Startup

## Decisions & Rationale

### 1. SSH Library Selection
- Decision: Use Paramiko for programmatic SSH operations; use native `ssh` subprocess for port forwarding.
- Rationale: Paramiko simplifies command execution and remote probing; native `ssh -L` is more reliable for dynamic port forwarding and user familiarity.
- Alternatives Considered: Fabric (higher-level but adds abstraction overhead); Pure subprocess only (harder to manage interactive error handling).

### 2. Persistent Session Tool
- Decision: Use `tmux` for persistent CARLA server session.
- Rationale: `tmux` provides easier session listing, attach/detach operations, and scripting than `screen`.
- Alternatives: `screen` (less introspection); systemd unit (heavier, not interactive for MVP).

### 3. CARLA Installation Detection
- Decision: Detect installation by checking for `CarlaUE4.sh` executable and validating directory structure (e.g., presence of `Content/` folders).
- Rationale: Direct executable presence is reliable and avoids version misreads from environment variables.
- Alternatives: Checking `which CarlaUE4.sh` (fails if not in PATH); Parsing README or version files (less consistent across installs).

### 4. CARLA Version Handling
- Decision: Accept any installed version; record version by invoking server with `--version` if available, else mark UNKNOWN.
- Rationale: Early feature focuses on startup; strict version management deferred.
- Alternatives: Force specific version (adds friction); Download latest automatically (could break compatibility).

### 5. Download Method for Missing Installation
- Decision: Provide instructions and scripted download using official CARLA releases (wget + extract) only after explicit user confirmation.
- Rationale: Minimizes risk; respects user's environment control.
- Alternatives: Automatic download without prompt (violates security/consent principles); Package manager (may not have desired version).

### 6. Port Conflict Strategy
- Decision: Probe local ports 2000-2002; if occupied, offer remapping to next free range (e.g., 2010-2012) and reflect mapping in output.
- Rationale: Keeps workflow moving without manual troubleshooting; explicit user confirmation avoids accidental remap.
- Alternatives: Abort on conflict (reduces usability); Force kill local processes (dangerous).

### 7. Logging Format
- Decision: JSON structured logs with fields: timestamp, level, component, action, outcome, details.
- Rationale: Constitution requires observability; structured logs parseable for later analysis.
- Alternatives: Plain text (harder to analyze); External logging service (overkill for MVP).

### 8. Credential Handling
- Decision: Reject any attempt to pass passwords; rely solely on user's existing SSH key setup; never write host/user inputs to disk.
- Rationale: Constitution mandates zero credential persistence; simplest secure approach.
- Alternatives: Support passwords (security risk); Store host in config (risk of sensitive environment leaking to VCS).

### 9. Interruption Cleanup
- Decision: Register signal handler for SIGINT to close tunnels (subprocess termination) and terminate any started remote CARLA process if flagged as owned by session.
- Rationale: Prevent orphaned tunnels and dangling server states.
- Alternatives: Rely on OS cleanup (unreliable for remote process termination).

### 10. Testing Strategy
- Decision: Unit tests mock Paramiko for command execution; integration test uses localhost as pseudo remote (start dummy process to simulate CARLA); contract test asserts CLI prompts sequence.
- Rationale: Enables deterministic CI without real remote host dependency.
- Alternatives: Spin up remote VM in tests (costly, slower); Skip integration tests (reduces confidence).

## Resolved Clarifications
- Dependency choices finalized: Paramiko + native ssh, tmux for sessions.
- No persistent storage: confirmed all artifacts ephemeral.
- Version management deferred: acceptable for MVP scope.
- Port remapping approach defined.

## Remaining Open Items
- NONE (all NEEDS CLARIFICATION items resolved).

## Risk Assessment
- Remote environment variability: Mitigated via detection scripts instead of assumptions.
- Download failures: User-facing retry + partial file cleanup strategy.
- Port forwarding instability: Native ssh tunneling fallback ensures robustness.

## Summary
Research confirms lightweight, secure, testable approach consistent with constitution principles. Ready to proceed to design artifacts.
