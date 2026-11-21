# Organiser execution plan

## 1. Define the scope before implementation

- Treat the ULTRON system as a fictional, isolated lab inspired by a science-fiction scenario. Do not imply an official Marvel/Avengers affiliation or use film stills, logos, soundtrack or dialogue without the necessary rights.
- Put the exact challenge hostname, ports, permitted protocols, time window and prohibited actions in the event rules.
- Use one logical operator account per team instance. Every team's account should be independently generated; do not create real user accounts or reuse any employee credentials.
- The privilege transition must occur inside the challenge sandbox. It must not grant root on the CTF host, Docker host, Kubernetes node, database server or any shared organiser infrastructure.

## 2. Recommended platform topology

1. CTFd: registration, team membership, challenge presentation, hint purchase, flag submission and scoreboard.
2. Reverse proxy: TLS termination and routing. Keep admin routes protected.
3. Challenge controller: issues a team-scoped instance, tracks verified milestones and writes the matching feedback text file into that team's workspace.
4. ULTRON challenge environment: a disposable per-team sandbox or microVM containing the login portal, local terminal/workspace, simulated operator account, maintenance workflow and protected filesystem.
5. Secret store: holds per-team password material, TOTP seed, per-team flag, instance identifiers and attestation values.
6. Logs/metrics: record authentication outcomes, milestone transitions, resource use and instance lifecycle. Never log passwords, TOTP codes, TOTP seeds or flags.

Keep the CTFd application/database and the challenge runtime in separate network segments. The challenge environment must not have a route to the CTFd database, organiser dashboard, host management interfaces or cloud metadata endpoints.

## 3. Build the participant journey in order

### Stage 1 — Identity investigation

Create a small, internally consistent evidence set: personnel index, system access journal, incident report and authentication migration note. Give each record a clear provenance and timestamps. The intended username must be recoverable by correlating at least two independent artefacts. Ensure decoy identities are plausible but eliminable using evidence, not guesswork.

### Stage 2 — Password recovery

Supply a challenge-owned encrypted recovery export plus a developer recovery note and relevant metadata. The intended password recovery process must be reproducible. Avoid real password dumps, real account material, generic dictionary-cracking tasks or instructions that encourage attacks outside the lab. Do not expose the recovered password in browser source, client-side storage or logs.

### Stage 3 — Second factor

Use a challenge-owned RFC 6238 TOTP implementation and a per-team secret. The correct migration record must be distinguishable using evidence. Test time synchronisation and a small, documented clock-skew window. Apply rate limiting and a temporary cooldown. Do not connect to a real authenticator provider or real phone/email identity.

### Stage 4 — Operator login

The single logical account starts with the operator role. Successful login opens the challenge workspace and displays the effective role. The UI must not suggest that authentication equals administrator access.

### Stage 5/6 — Local privilege-boundary task

Provide a terminal or local workspace that is separate from the public challenge API. Populate it with maintenance logs, local documentation, configuration and one deliberately vulnerable, challenge-specific privileged workflow. The weakness should be a controlled trust/permission mistake in the challenge's own userland. A successful solve changes only the sandbox's internal role or access-control state.

For the default deployment, prefer a purpose-built restricted shell or virtual filesystem with an app-level administrator role. If a real OS privilege-escalation exercise is essential, use a dedicated disposable microVM per team with no shared host mounts or management credentials. Do not rely on a kernel/container escape.

### Stage 7 — Protected artifact

Place the exact flag in a local file readable only after the challenge's administrator state is achieved. The challenge controller should validate both the administrator state and an access event for the protected artifact. Do not create an HTTP route, public API, frontend variable, downloadable image layer or static asset that returns the flag.

## 4. Feedback implementation

- Store the text files in a read-only template directory available to the challenge controller, not as a public directory listing.
- Trigger feedback only from server-verified events: identity checkpoint, password success, TOTP success, session creation, privilege-boundary checkpoint, admin state and protected-file access.
- Write the correct template to the team's workspace as `ULTRON_FEEDBACK.txt` or append it to a milestone log.
- For unsuccessful login/OTP attempts, use the generic failure messages and rate-limit notice. Do not reveal whether a username exists.
- Do not trigger the privilege-boundary success message merely because a participant requests a sensitive path or sends a string containing a guessed keyword.

## 5. CTFd configuration

- Create one Hard challenge worth 500 points.
- Configure three paid hints with costs 50, 100 and 150 points.
- CTFd paid hints deduct points from the user's score and require sufficient existing points. For a standalone event, either provide a small introductory scoring task or implement a team-aware hint-credit mechanism. Verify the exact behaviour with team accounts before launch.
- Restrict repeated incorrect submissions and authentication attempts independently. Do not assume CTFd's flag-attempt controls protect the challenge login service.
- Use a server-side flag validator or a custom challenge/flag integration where needed. Never trust a completion claim supplied by the browser.

## 6. Meticulous setup checklist

- Pin all application/container image versions and record build hashes.
- Build the challenge image from reviewed source; scan dependencies and images.
- Generate per-team credentials and flags at instance creation.
- Keep secret material out of Git, CI logs, image layers, frontend bundles and downloadable files.
- Use a separate network for challenge workloads. Deny outbound access by default; allow only explicitly required destinations.
- Do not mount `/var/run/docker.sock`, host root, host home directories or organiser secrets into a participant environment.
- Apply CPU, memory, PID, disk and runtime limits; set an automatic expiry and reset path.
- Run challenge processes as non-root where possible. If the exercise needs elevated privileges, simulate the role transition or confine the real OS exercise to a disposable microVM.
- Apply filesystem isolation, read-only mounts where practical, seccomp/AppArmor/SELinux policy and minimal capabilities.
- Ensure no challenge container can reach the CTFd database, admin panel, cloud metadata service or other teams' instances.
- Synchronise clocks for TOTP. Test clock drift and container restart behaviour.
- Use HTTPS for the public site. Protect organiser/admin accounts with separate MFA and strong credentials.
- Back up CTFd data and challenge authoring assets; test restoration before the event.
- Ensure instance destruction also deletes temporary credentials, workspaces and artifacts.

## 7. Quality assurance and release gates

A challenge is not ready until all of the following are true:

1. Author solve: the author completes every stage from a clean instance and records the intended solution privately.
2. Blind human solve: at least two non-authors solve using only participant-provided evidence. Record median solve time and ambiguous instructions.
3. AI benchmark: test text-only assistance, tool-enabled assistance and an autonomous browser/terminal agent. Record success, time, shortcuts and whether the solution relies on unintended leakage. Do not claim the challenge is AI-proof.
4. Negative testing: wrong username/password/OTP, stale TOTP, replay, expired session, cross-team flag, direct file access as operator, guessed URL, API probing and repeated requests all fail safely.
5. Isolation testing: confirm the participant cannot read another team's instance, host files, organiser secrets, CTFd database or cloud metadata.
6. Reset testing: destroy and recreate the instance; confirm a fresh, reproducible challenge state and new per-team secrets.
7. Flag test: verify exact string matching, including the space after the opening brace. Confirm the submitted flag matches the local file byte-for-byte.
8. Load test: test concurrent login, workspace and instance creation using the expected participant count.

## 8. Suggested release order

- Local development: one CTFd instance and one disposable ULTRON workspace.
- Integration test: several team accounts and separate instances.
- Staging: production-like network separation, TLS, logging and backups.
- Pilot: a small group of blind testers.
- Production: freeze challenge assets, rotate secrets, publish the brief and monitor health.

## 9. Organiser handover

Deliver the website URL, organiser credentials through a secure channel, deployment instructions, challenge reset procedure, challenge authoring manifest, incident contact, backup/restore procedure and an explanation of which components are CTFd versus custom challenge infrastructure.
