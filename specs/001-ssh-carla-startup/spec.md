# Feature Specification: SSH-Based CARLA Server Remote Startup

**Feature Branch**: `001-ssh-carla-startup`  
**Created**: 2025-11-21  
**Status**: Draft  
**Input**: User description: "add the ability to start the carla server on a remote ubuntu pc through ssh with exposing the correct ports. Check if carla is already installed and whether it can be downloaded. the script should run interactively and never save any secrets or keys. However, it should prompt for user and host ip as well as an interactive startup. Not saving any secrets in a way that they land in git is most important."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Interactive Remote Server Startup (Priority: P1)

A researcher wants to start a CARLA simulation server on their remote Ubuntu machine so they can run reinforcement learning experiments from their local development environment. They provide connection details interactively and the script establishes an SSH connection, starts CARLA, and exposes the necessary ports back to their local machine.

**Why this priority**: This is the core value proposition - without remote server startup, the entire project purpose is blocked. All subsequent features depend on this working.

**Independent Test**: Can be fully tested by running the script, providing SSH credentials interactively, and verifying that CARLA server starts on the remote machine with ports forwarded locally. Success means being able to connect to CARLA from local Python code.

**Acceptance Scenarios**:

1. **Given** user has SSH access to remote Ubuntu machine with CARLA installed, **When** user runs the startup script and provides host IP and username interactively, **Then** script establishes SSH connection, starts CARLA server, forwards ports (2000-2002) to localhost, and confirms server is running
2. **Given** user runs the startup script, **When** prompted for connection details, **Then** user can enter hostname/IP and username without any credentials being saved to disk or configuration files
3. **Given** CARLA server is already running on remote machine, **When** user runs the startup script, **Then** script detects existing server process and asks whether to reuse or restart it
4. **Given** SSH connection succeeds but CARLA fails to start, **When** startup error occurs, **Then** script displays clear error message with troubleshooting guidance and cleans up SSH tunnel

---

### User Story 2 - CARLA Installation Detection and Download (Priority: P2)

A researcher connects to a new remote Ubuntu machine that doesn't have CARLA installed yet. The script detects the missing installation, offers to download and install CARLA, and guides the user through the setup process interactively.

**Why this priority**: This removes a major setup barrier and enables first-time users to get started quickly. However, users can manually install CARLA beforehand, so this is not blocking for MVP.

**Independent Test**: Can be tested independently by connecting to a clean Ubuntu VM, running the script, and verifying it detects missing CARLA, downloads the correct version, extracts it to the appropriate location, and successfully starts the server.

**Acceptance Scenarios**:

1. **Given** remote Ubuntu machine without CARLA installed, **When** script connects and checks for CARLA, **Then** script detects absence of CARLA executable and prompts user to download/install
2. **Given** user confirms CARLA download, **When** script begins installation, **Then** script downloads the appropriate CARLA release for Ubuntu, extracts it to user-specified directory, and verifies installation
3. **Given** CARLA installation fails (network error, insufficient disk space), **When** error occurs, **Then** script provides clear error message, preserves partial downloads if resumable, and allows retry
4. **Given** multiple CARLA versions detected on remote machine, **When** script checks installation, **Then** script lists available versions and prompts user to select which version to use

---

### User Story 3 - Persistent Session Management (Priority: P3)

A researcher wants to keep the CARLA server running even after disconnecting their local SSH session, so they can reconnect later or run long experiments without maintaining an active terminal. The script uses screen/tmux to create a persistent remote session.

**Why this priority**: This is a quality-of-life improvement for long-running experiments. Users can manually manage screen sessions, so it's not critical for initial MVP but greatly improves user experience.

**Independent Test**: Can be tested by starting CARLA via the script, disconnecting the local terminal, reconnecting later, and verifying CARLA is still running and accessible. Success means experiments continue uninterrupted.

**Acceptance Scenarios**:

1. **Given** user starts CARLA server remotely, **When** script launches server, **Then** server runs inside a detached screen or tmux session that persists after local disconnect
2. **Given** user reconnects to remote machine, **When** running the script again, **Then** script detects existing persistent session and offers to attach to it or view logs
3. **Given** user wants to stop the remote CARLA server, **When** requesting shutdown, **Then** script terminates the persistent session cleanly and confirms server stopped
4. **Given** persistent session crashes, **When** script checks server status, **Then** script detects crash, displays relevant logs, and offers to restart

---

### Edge Cases

- **Network interruption during SSH connection**: Script should detect connection loss, attempt reconnection with exponential backoff, and cleanly fail after timeout with clear error message
- **Port already in use locally**: If ports 2000-2002 are already bound on localhost, script should detect conflict and offer alternative port mapping or terminate gracefully
- **Insufficient permissions on remote machine**: If user lacks permissions to run CARLA or bind ports, script should fail early with permission error details
- **CARLA binary incompatible with remote Ubuntu version**: Script should verify Ubuntu version compatibility before downloading/running CARLA
- **Firewall blocking forwarded ports**: Script should test port connectivity after establishing tunnel and warn if ports are unreachable
- **Disk space exhausted during CARLA download**: Script should check available disk space before downloading and abort if insufficient
- **User cancels interactive prompt mid-execution**: Script should handle Ctrl+C gracefully, clean up partial SSH tunnels, and not leave orphaned processes
- **Multiple simultaneous script executions**: Script should detect if another instance is managing the same remote server and prevent conflicts

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Script MUST prompt user interactively for remote host IP/hostname and SSH username at runtime
- **FR-002**: Script MUST establish SSH connection using SSH key-based authentication (no password storage)
- **FR-003**: Script MUST NEVER persist SSH credentials, hostnames, or any secrets to disk, configuration files, or version control
- **FR-004**: Script MUST forward CARLA server ports (2000, 2001, 2002) from remote machine to localhost using SSH tunnel
- **FR-005**: Script MUST check if CARLA server process is already running on remote machine before attempting to start
- **FR-006**: Script MUST verify CARLA installation exists on remote Ubuntu machine (check for CarlaUE4.sh or similar executable)
- **FR-007**: Script MUST offer to download and install CARLA if not detected on remote machine
- **FR-008**: Script MUST display clear error messages with troubleshooting guidance when SSH connection fails
- **FR-009**: Script MUST detect if local ports (2000-2002) are already in use and handle conflict gracefully
- **FR-010**: Script MUST verify CARLA server started successfully by checking process status on remote machine
- **FR-011**: Script MUST provide option to run CARLA server in persistent session (screen or tmux) for long-running experiments
- **FR-012**: Script MUST log all SSH operations and CARLA startup events with timestamps for debugging
- **FR-013**: Script MUST handle Ctrl+C interrupt gracefully and clean up SSH tunnels and remote processes
- **FR-014**: Script MUST test port connectivity after establishing SSH tunnel and warn if ports unreachable
- **FR-015**: Script MUST detect remote Ubuntu version and verify CARLA compatibility before download/startup

### Key Entities *(include if feature involves data)*

- **SSH Connection**: Represents active SSH session to remote Ubuntu machine, includes tunnel state, connection health, and forwarded port mappings
- **CARLA Server Process**: Remote process running CARLA simulator, tracked by PID, status (running/stopped), version, and persistent session identifier (screen/tmux session name)
- **Port Mapping**: Association between remote CARLA ports and local forwarded ports, includes port numbers, protocol, and connectivity status
- **Installation State**: Represents CARLA installation on remote machine, includes installation path, version detected, binary location, and compatibility verification
- **Script Execution Context**: Runtime state of the management script, includes user inputs (hostname, username), session tokens, error states, and cleanup handlers

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: User can establish SSH connection and start remote CARLA server in under 60 seconds for existing installations
- **SC-002**: Zero credentials or secrets are persisted to disk or git repository (verified by automated git pre-commit checks)
- **SC-003**: Script successfully handles SSH connection failures and provides actionable error messages in 100% of failure scenarios
- **SC-004**: Port forwarding establishes correctly and allows local CARLA client to connect within 5 seconds of server startup
- **SC-005**: CARLA installation detection correctly identifies existing installations or absence in 100% of test cases
- **SC-006**: First-time setup (including CARLA download and installation) completes successfully for users with no prior CARLA installation
- **SC-007**: Persistent sessions (screen/tmux) maintain CARLA server running after local disconnect for at least 24 hours
- **SC-008**: Script handles 95% of common failure scenarios (network drops, port conflicts, permission errors) without leaving orphaned processes or tunnels

## Assumptions *(if applicable)*

- User has SSH key-based authentication already configured for the remote Ubuntu machine
- Remote Ubuntu machine has internet access for downloading CARLA if not installed
- User has sufficient permissions on remote machine to run processes and bind ports
- Default CARLA ports (2000-2002) are not firewalled on the remote machine
- User's local machine has available ports 2000-2002 or can accept alternative port mappings
- Remote machine has at least 20GB free disk space for CARLA installation
- Network latency between local and remote machine is reasonable (<500ms RTT) for interactive use

## Out of Scope *(if applicable)*

- Automatic SSH key generation or distribution (user must configure SSH keys manually)
- Multi-user concurrent access control (script assumes single user manages the remote server)
- CARLA configuration or map management (script only handles server startup/shutdown)
- Performance monitoring or resource usage tracking during simulation
- Automatic CARLA version upgrades or migration between versions
- GUI-based interaction (script is CLI-only, fully text-based interactive prompts)
- Windows or macOS remote servers (Ubuntu Linux only)
- Authentication methods other than SSH keys (no password, no tokens, no certificates)
