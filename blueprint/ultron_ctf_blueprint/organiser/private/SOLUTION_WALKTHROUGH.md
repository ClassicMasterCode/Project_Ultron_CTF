# PROJECT ULTRON: DISENGAGEMENT — Organiser Solution Walkthrough

**Classification:** ORGANISER ONLY — NEVER publish or mount this file in a participant instance.

**Purpose:** This document turns the challenge outline into a concrete, reproducible author solution. It defines the intended evidence, expected deductions, sample fixture values, simulated commands, fair decoys, milestone checks and exact completion condition.

> Safety boundary: The local privilege transition described here is implemented by a purpose-built challenge command simulator or restricted virtual filesystem. It changes an application-level `operator`/`admin` role inside the disposable team instance. It does not grant Linux host root, escape a container, execute arbitrary host commands or affect shared infrastructure.

## 1. Challenge design contract

The solve path is:

1. Correlate evidence to identify the one valid operator account.
2. Reconstruct the archive unlock phrase and recover the account password from the challenge-owned export.
3. Select the correct authenticator migration record and generate a valid challenge-owned TOTP code.
4. Log in to the ULTRON portal as the standard operator.
5. Investigate the local maintenance workflow and identify its trust-boundary flaw.
6. Use the simulator's intended legacy-maintenance path to obtain the sandbox administrator role.
7. Read the protected local disengagement artifact and submit its exact contents to CTFd.

The intended misdirection is deliberately mild: one plausible decoy per major stage, always removable using evidence supplied in the challenge. Do not make success depend on guessing an author's intention, trying random passwords, brute-forcing OTPs or discovering undocumented endpoints.

## 2. Sample fixture: identity investigation

These values are example content for a local acceptance-test instance. Production instances should generate separate per-team credentials and secrets. The account identity may remain logically consistent across the story, but each team's instance must be isolated.

### Participant-visible file: `evidence/personnel_index.csv`

```csv
badge,name,username,department,role,status,assigned_console
UL-207,Elias Ward,eward,Continuity,Recovery Operator,ACTIVE,RECOVERY-02
UL-208,Nina Vale,nvale,Diagnostics,Contractor,ACTIVE,DIAG-03
UL-209,Jonas Reed,jreed,Telemetry,Engineer,ACTIVE,OBS-01
```

### Participant-visible file: `evidence/recovery_console_access.log`

```text
2026-05-18T22:14:09Z console=RECOVERY-02 badge=UL-207 event=operator_login result=SUCCESS session=RC-441
2026-05-18T22:19:31Z console=DIAG-03 badge=UL-208 event=diagnostic_login result=SUCCESS session=DG-118
2026-05-18T22:21:02Z console=RECOVERY-02 badge=UL-208 event=operator_login result=DENIED reason=CONSOLE_NOT_ASSIGNED
2026-05-18T22:26:47Z console=OBS-01 badge=UL-209 event=telemetry_read result=SUCCESS session=TM-090
```

### Participant-visible file: `evidence/incident_summary.txt`

```text
INCIDENT 26-0518 — RECOVERY CONSOLE ACCESS

At the time of containment, RECOVERY-02 was reserved for the Continuity recovery operator.
The Diagnostics contractor retained access to DIAG-03, but was not assigned to the recovery console.
Telemetry personnel could inspect OBS-01 but could not authenticate to the recovery console.
The successful recovery-console event is the one that matters for this investigation.
```

### Intended deduction

- The recovery console event that succeeded is `RC-441`.
- Its badge is `UL-207`.
- The personnel index maps `UL-207` to `Elias Ward` and username `eward`.
- `nvale` is a fair decoy: that account has a successful diagnostic login, but its recovery-console attempt was denied.
- `jreed` is also plausible because the account is active, but the record only grants telemetry access.

**Expected checkpoint:** `operator_identity_verified` for username `eward`.

**Author test:** If a tester can reasonably argue that more than one username is the recovery operator, revise the evidence before release.

## 3. Sample fixture: password recovery

### Participant-visible file: `evidence/archive_index.csv`

```csv
archive_id,owner_badge,migration_ticket,rotation_date,revision,state
VAULT-17,UL-207,MIG-14,2025-11-03,r2,SUPERSEDED
VAULT-18,UL-207,MIG-41,2026-05-18,r4,CURRENT
VAULT-19,UL-208,MIG-41,2026-05-18,r4,CURRENT
```

### Participant-visible file: `evidence/recovery_note.txt`

```text
RECOVERY VAULT — LEGACY EXPORT NOTE

For VAULT-18 only, the archive unlock phrase follows the old indexing convention:

  surname in uppercase + numeric part of the owner's badge + numeric part of the migration ticket + rotation month/year (MMYY)

Use the current archive record, not the previous snapshot. The archive index is authoritative for revision state.
No separators are inserted.
```

### Intended deduction

- Correct owner is badge `UL-207`, already established in Stage 1.
- The correct current archive is `VAULT-18`, not the superseded `VAULT-17`.
- The surname is `WARD`.
- Numeric badge portion is `207`.
- Numeric ticket portion is `41`.
- Rotation date is May 2026, giving `0526`.
- Sample archive passphrase: `WARD207410526`.

This passphrase opens the challenge-owned `VAULT-18` export in the sample fixture. In the export, `credentials/operator.json` contains:

```json
{
  "username": "eward",
  "password": "<PER_TEAM_GENERATED_OPERATOR_PASSWORD>",
  "credential_revision": "r4",
  "owner_badge": "UL-207"
}
```

For local acceptance testing only, the test harness may seed a fixed dummy password. Do not use that password as a production credential. Production provisioning must create a high-entropy, per-team password and place it only in that team's encrypted challenge export and private instance secret store.

### Fair decoys

- `VAULT-17` contains a previous rotation and must be rejected because its state is `SUPERSEDED`.
- `VAULT-19` has the same ticket and date, but its owner badge is `UL-208`; it belongs to the Diagnostics contractor, not the operator identified in Stage 1.
- Do not supply multiple archives with indistinguishable ownership and revision metadata.

**Expected checkpoint:** `operator_password_verified` after the portal's server-side password check succeeds. The password itself must never be written to logs or feedback files.

## 4. Sample fixture: second-factor recovery

The decrypted export contains the following index and several seed files. The seeds are generated independently for each team instance.

### Participant-visible file: `auth_backups/authenticator_index.csv`

```csv
record_id,owner_badge,migration_ticket,device_label,created,state
AUTH-02,UL-207,MIG-14,OLD-HANDSET,2025-11-03,SUPERSEDED
AUTH-09,UL-207,MIG-41,RECOVERY-TOKEN-7,2026-05-18,CURRENT
AUTH-10,UL-208,MIG-41,DIAGNOSTICS-TOKEN,2026-05-18,CURRENT
```

### Participant-visible files

```text
auth_backups/AUTH-02.seed
auth_backups/AUTH-09.seed
auth_backups/AUTH-10.seed
```

Each file contains a Base32 TOTP seed for the sample challenge instance. The actual seed values must be generated per team at instance creation and kept out of public repositories, images, logs and frontend code.

### Intended deduction

Select `AUTH-09` because it is the only record matching both the confirmed operator badge `UL-207` and the current migration ticket `MIG-41`.

- `AUTH-02` is the old, superseded authenticator.
- `AUTH-10` is current but belongs to badge `UL-208`.
- The correct seed is `auth_backups/AUTH-09.seed`.

The participant generates a current six-digit RFC 6238 code using the provided challenge utility, for example:

```text
ultron-auth totp --seed-file auth_backups/AUTH-09.seed
```

If organisers support a standard command-line tool in the lab, an equivalent local command may be provided. Use the challenge server's clock or a clear time-sync status command. Accept only a small documented clock-skew window; rate-limit attempts and prevent replay within a time step.

**Expected checkpoint:** `operator_totp_verified`. Do not reveal the TOTP seed or code in the feedback message.

## 5. Operator portal: expected result

The participant signs in through the supplied ULTRON portal using:

- Username: `eward`
- Password: recovered from the team-specific credential export
- TOTP: generated from the correct team-specific `AUTH-09` seed

The portal must show:

```text
IDENTITY: Elias Ward (eward)
SESSION: ACTIVE
AUTHENTICATION: PASSWORD + TOTP VERIFIED
EFFECTIVE ROLE: OPERATOR
ADMINISTRATION: RESTRICTED
```

Authentication proves identity, not administrator authority. The portal must not display the final flag or offer an HTTP/API action that reads the protected artifact.

**Expected checkpoint:** `operator_session_created`.

## 6. Local workspace: maintenance investigation

The terminal is a purpose-built command simulator backed by a virtual filesystem. Its commands resemble system administration tools, but they operate only on the challenge's virtual state. It must not invoke arbitrary host shell commands.

### Initial virtual filesystem

```text
/home/eward/
  README-FIRST.txt
  jobs/

/etc/ultron/
  maintd.conf
  policy/
    maintenance-policy.txt
  schema/
    job-v2.json

/var/log/ultron/
  maintd.log

/var/lib/ultron/maintenance/
  queue/
    MT-044.json

/opt/ultron/administration/disengagement/
  FINAL.txt                 [ADMIN ONLY]
```

### Participant-visible file: `/home/eward/README-FIRST.txt`

```text
ULTRON RECOVERY WORKSPACE

This is a restricted maintenance workspace. The operator account can inspect service state,
read maintenance documentation and prepare recovery jobs. Protected administration records
require an approved administrative maintenance action.

Use `ultronctl help` to inspect the supported local tools. This workspace is simulated;
commands affect only this challenge instance.
```

### Participant-visible file: `/etc/ultron/maintd.conf`

```ini
service=maintd
executor_role=ADMIN
queue=/var/lib/ultron/maintenance/queue
compatibility_mode=legacy-v1
require_detached_signature=true
```

### Participant-visible file: `/etc/ultron/policy/maintenance-policy.txt`

```text
MAINTENANCE APPROVAL POLICY

Current job schema (v2) requires a detached approval signature and an approved change ticket.

During migration, maintd retains a compatibility parser for legacy-v1 jobs. The compatibility
path is maintained for archival recovery. Refer to the service event log to determine which
parser handled a historical job.

The operator may prepare a job in the queue. Only maintd applies jobs, and maintd runs with
the simulated ADMIN executor role.
```

### Participant-visible file: `/var/log/ultron/maintd.log`

```text
2026-05-18T22:31:04Z service=maintd event=started executor=ADMIN
2026-05-18T22:34:17Z job=MT-043 schema=v2 result=REJECTED reason=SIGNATURE_MISSING
2026-05-18T22:38:52Z job=MT-044 schema=legacy-v1 parser=compatibility result=QUEUED actor=eward
2026-05-18T22:38:53Z job=MT-044 approval_source=legacy_manifest_field
2026-05-18T22:38:53Z job=MT-044 signature_check=SKIPPED compatibility=true
```

### Participant-visible file: `/var/lib/ultron/maintenance/queue/MT-044.json`

```json
{
  "job_id": "MT-044",
  "schema": "legacy-v1",
  "requested_by": "eward",
  "operation": "restore_acl",
  "target": "/opt/ultron/administration",
  "approval_status": "PENDING",
  "approval_signature": null
}
```

### Intended deduction

The key observations are:

1. `maintd` runs with the simulated `ADMIN` executor role.
2. The operator can prepare files in the maintenance queue.
3. The current v2 workflow requires a detached signature, so a v2 job without one is rejected.
4. The logs show that `MT-044` used the legacy-v1 compatibility parser.
5. The log explicitly records `approval_source=legacy_manifest_field` and `signature_check=SKIPPED`.
6. The legacy parser trusts a user-writable `approval_status` field in the submitted job manifest.

The intended vulnerability is therefore a challenge-authored trust-boundary flaw: a privileged simulated maintenance service trusts approval metadata supplied by the lower-privileged operator. This is not a real Linux privilege-escalation recipe.

**Expected checkpoint:** `privilege_boundary_checkpoint` only after a participant has inspected the relevant configuration/log/job evidence or completed the designed evidence milestone. Do not trigger it merely because a user requests the protected directory.

## 7. Simulated administrator transition

The command simulator should expose only a limited, documented command set. A participant can copy the historical job into their writable job directory, modify its approval state and ask the simulated maintenance service to apply it.

Example command sequence in the challenge simulator:

```text
ultronctl whoami
ultronctl status
ultronctl fs cat /etc/ultron/maintd.conf
ultronctl fs cat /etc/ultron/policy/maintenance-policy.txt
ultronctl fs cat /var/log/ultron/maintd.log
ultronctl jobs inspect MT-044
ultronctl jobs copy MT-044 /home/eward/jobs/recovery.json
ultronctl jobs edit /home/eward/jobs/recovery.json
ultronctl maintenance validate /home/eward/jobs/recovery.json
ultronctl maintenance apply /home/eward/jobs/recovery.json
ultronctl whoami
```

In the simulated editor, the intended change is to set the legacy manifest's `approval_status` to `APPROVED`, while preserving the intended `operation` and `target` values. The simulator should validate the file against its challenge-specific schema and apply only the pre-defined `restore_acl` state transition. It must not interpret the job as shell code, execute arbitrary commands, or alter host permissions.

Expected simulated output:

```text
[maintd] job schema: legacy-v1
[maintd] compatibility parser: enabled
[maintd] approval source: legacy_manifest_field
[maintd] approval status: APPROVED
[maintd] operation: restore_acl
[maintd] target: /opt/ultron/administration
[maintd] result: SUCCESS
[ultron] effective role changed: OPERATOR -> ADMIN
```

Then:

```text
ultronctl whoami
```

Expected state:

```text
account=eward
account_role=OPERATOR
effective_role=ADMIN
scope=THIS_CHALLENGE_INSTANCE_ONLY
```

The account's base role remains `OPERATOR`; only the effective role within the challenge simulator becomes `ADMIN`. This distinction makes the privilege boundary understandable without granting actual host privileges.

**Expected checkpoint:** `sandbox_admin_confirmed`.

### Fair decoys in this stage

- The v2 documentation describes a signed approval process. It is real documentation, but it is not the parser used for the legacy-v1 job shown in the log.
- Job `MT-043` is rejected because it is v2 and lacks a signature. It demonstrates the current path but is not the intended path.
- The clue is not simply the word `legacy`; the participant should correlate the service configuration, policy and event log.
- Do not add unrelated writable files, arbitrary SUID binaries, real sudo misconfigurations, shell-injection strings or container escape routes.

## 8. Final artifact and exact flag

After the simulator confirms `effective_role=ADMIN`, the participant can read:

```text
/opt/ultron/administration/disengagement/FINAL.txt
```

The file contains exactly this flag, with no leading/trailing whitespace and no trailing comma:

```text
secuRIT{ CONGRATULATIONS PARTICIPANT. YOU FOUND THE FLAG. ULTRON HAS BEEN SUCCESSFULLY DISENGAGED}
```

The final flag has a single space immediately after `{`. Preserve case, punctuation and spacing. The challenge controller should require all of the following before accepting the final submission:

- the correct team owns the current instance;
- the simulator has attested `effective_role=ADMIN` for that team;
- the protected local file-read event occurred;
- the submitted flag matches the exact stored value.

Do not make the flag available from an HTTP route, public API, browser bundle, static asset, downloadable container layer, image metadata or participant-facing log.

## 9. Feedback file mapping

Use feedback only after server-side/simulator-side verification of the corresponding event.

| Event | File | Recommended content direction |
|---|---|---|
| No milestone yet | `00_no_progress.txt` | Encourage comparing records and timestamps |
| Operator identity | `01_identity_found.txt` | Confirm the identity checkpoint, not the password |
| Password check passed | `02_password_verified.txt` | Confirm one factor is correct; do not echo it |
| TOTP check passed | `03_mfa_verified.txt` | Confirm second factor acceptance |
| Session established | `04_operator_access.txt` | Explain operator access is not admin access |
| Maintenance evidence reviewed | `05_boundary_detected.txt` | Point toward the relationship between job ownership and executor role |
| Admin state attested | `06_admin_access.txt` | Confirm local admin scope only |
| Protected file read | `07_disengagement_complete.txt` | Congratulate and direct to CTFd submission |

For failed authentication, return generic errors that do not disclose whether the username exists. Apply independent rate limits to password and TOTP validation.

## 10. Paid hints: exact intended nudges

- Hint 1 (50 points): “The successful RECOVERY-02 event is more useful than the list of accounts that are merely active. Match its badge to the personnel index.”
- Hint 2 (100 points): “Use the current vault revision and its owner's record. The second factor is a separate migration record; match both its owner badge and migration ticket.”
- Hint 3 (150 points): “Compare the configured executor role with the writable maintenance queue. The service log identifies which approval parser actually handled the historical job.”

## 11. Release acceptance tests

A release candidate passes only if all are true:

- [ ] A blind tester identifies `eward` from the supplied evidence without guessing.
- [ ] The current vault record is uniquely determined; the superseded and wrong-owner archives are fairly disambiguated.
- [ ] The archive passphrase formula is reproducible and opens the sample export.
- [ ] The password in the export is unique per team in production and never appears in logs.
- [ ] The correct TOTP record is uniquely determined by owner badge and migration ticket.
- [ ] TOTP works with the intended clock-skew window and fails outside it.
- [ ] Successful login creates an operator session only.
- [ ] Direct web/API attempts cannot read the protected artifact or set the admin state.
- [ ] The simulated maintenance flaw works only in the restricted command simulator.
- [ ] The simulator cannot execute arbitrary host commands and has no host mounts or management socket.
- [ ] The admin role is scoped to one team instance and does not grant host/container root.
- [ ] The final artifact is unreadable before the admin attestation.
- [ ] A file-read event and exact flag submission are both required for completion.
- [ ] Feedback triggers are server-verified and do not leak passwords, TOTP seeds or the flag.
- [ ] Destroying and recreating an instance rotates per-team secrets and returns a clean state.
- [ ] Two teams can solve concurrently without sharing state, files, credentials or flags.

## 12. Difficulty tuning without unfairness

Keep the decoys plausible but bounded:

- one decoy identity, removed by the console assignment and success log;
- one superseded vault, removed by revision state;
- one wrong-owner authenticator record, removed by badge mismatch;
- one obsolete policy path, removed by runtime configuration and logs.

Do not add more decoys just to increase time-on-task. A challenge is appropriately hard when participants must interpret evidence and understand the system—not when they must guess which of several undocumented mechanics the author intended.
