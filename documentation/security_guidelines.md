# HERCULES CTF — Security & Isolation Guidelines

## 1. Threat Model & Sandbox Boundaries
The challenge environment intentionally exposes a local privilege escalation flaw.
To ensure the competition host and other teams remain completely secure:

1. **Simulated Application Privilege vs. Host Root**:
   - The privilege escalation from `OPERATOR` to `ADMIN` takes place entirely inside the challenge's userland virtual filesystem engine (`ultron_sim.py`).
   - It grants administrative authority within the simulation only.
   - It DOES NOT execute arbitrary shell commands on the host operating system.
   - It DOES NOT grant host root or container root.

2. **Container Hardening (When Deployed via Docker)**:
   - Run as non-root user (`USER ultron:1337`).
   - Drop all Linux capabilities: `--cap-drop=ALL`.
   - Read-only root filesystem: `--read-only` with ephemeral `/tmp` tmpfs.
   - Resource quotas: `--cpus="0.5" --memory="256m" --pids-limit=64`.
   - Network segmentation: Challenge containers cannot reach the CTFd database, Docker socket, or cloud metadata endpoints (`169.254.169.254`).

3. **Rate Limiting & Anti-Brute-Force**:
   - Authentication endpoints enforce a maximum of 6 attempts per 60 seconds per IP.
   - Lockout triggers a temporary cooldown period with `rate_limited.txt` feedback.
   - Failure responses never disclose account existence.
