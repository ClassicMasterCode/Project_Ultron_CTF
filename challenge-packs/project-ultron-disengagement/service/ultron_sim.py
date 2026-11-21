#!/usr/bin/env python3
"""
ULTRON Simulator & Virtual Filesystem Engine
Models the isolated recovery sandbox, virtual filesystem, maintd daemon,
and milestone tracking for PROJECT ULTRON: DISENGAGEMENT.
"""
import os
import json
import copy
from typing import Dict, Any, Tuple, Optional

EXACT_FLAG = "secuRIT{ CONGRATULATIONS PARTICIPANT. YOU FOUND THE FLAG. ULTRON HAS BEEN SUCCESSFULLY DISENGAGED}"

EMBEDDED_FEEDBACK = {
    "00_no_progress.txt": (
        "ULTRON STATUS: NO VERIFIED MILESTONE\n\n"
        "No meaningful recovery milestone has been recorded yet.\n\n"
        "Start with the supplied incident bundle. Compare identifiers, timestamps and naming conventions across the records. A single file is not intended to reveal the whole operator identity.\n\n"
        "Do not brute-force the authentication service. The challenge is designed to be solved by correlating the evidence."
    ),
    "01_identity_found.txt": (
        "ULTRON STATUS: OPERATOR IDENTITY RECOGNISED\n\n"
        "The recovery environment has confirmed the operator identity checkpoint.\n\n"
        "You have identified the account, but that does not establish possession of its authentication factors. Continue with the password recovery material and verify that it belongs to the same operator."
    ),
    "02_password_verified.txt": (
        "ULTRON STATUS: PASSWORD CHECK PASSED\n\n"
        "The password has been accepted by the isolated authentication service.\n\n"
        "A second authentication factor is still required. The authenticator migration material is a separate evidence source. Make sure the selected backup belongs to the operator account you identified earlier."
    ),
    "03_mfa_verified.txt": (
        "ULTRON STATUS: SECOND FACTOR ACCEPTED\n\n"
        "The second-factor check has passed.\n\n"
        "Use the supplied ULTRON sign-in interface to complete the operator login. Successful authentication will provide standard operator permissions only."
    ),
    "04_operator_access.txt": (
        "ULTRON STATUS: OPERATOR SESSION ACTIVE\n\n"
        "Authentication is complete. ULTRON recognises you as the operator.\n\n"
        "The administration directory remains outside your current permission boundary. Inspect the local workspace, system documentation and maintenance records. The web interface is not a substitute for the local investigation required by this challenge."
    ),
    "05_boundary_detected.txt": (
        "ULTRON STATUS: PRIVILEGE BOUNDARY INVESTIGATION\n\n"
        "Your investigation has reached the maintenance subsystem.\n\n"
        "Before attempting an administrative operation, establish which component performs it, what permissions that component has, and what inputs it trusts. Verify that the condition you identified is actually controllable from the operator context."
    ),
    "06_admin_access.txt": (
        "ULTRON STATUS: ADMINISTRATOR PERMISSION CONFIRMED\n\n"
        "The challenge environment has recorded the intended administrator-level transition.\n\n"
        "The protected administration directory should now be accessible within this isolated workspace. Locate the disengagement record and submit its exact flag through the competition platform."
    ),
    "07_disengagement_complete.txt": (
        "ULTRON STATUS: DISENGAGEMENT CONFIRMED\n\n"
        "The protected disengagement record has been accessed and the completion condition has been satisfied.\n\n"
        "Submit the recovered flag through the competition platform if you have not already done so.\n\n"
        "ULTRON HAS BEEN SUCCESSFULLY DISENGAGED."
    ),
    "rate_limited.txt": (
        "ULTRON SECURITY: TEMPORARY RATE LIMIT\n\n"
        "Too many unsuccessful authentication attempts have been recorded.\n\n"
        "Pause and return to the evidence. The challenge is intended to reward correct recovery, not repeated guessing. Access will resume according to the configured cooldown."
    ),
    "wrong_credential.txt": (
        "ULTRON AUTHENTICATION: NOT VERIFIED\n\n"
        "The supplied value did not pass this authentication step.\n\n"
        "Re-check the source record, account association and recovery process. Repeated guesses will not reveal additional information and may trigger the challenge's rate limit."
    ),
    "wrong_second_factor.txt": (
        "ULTRON AUTHENTICATION: SECOND FACTOR NOT VERIFIED\n\n"
        "The second-factor value was not accepted.\n\n"
        "Check that the authenticator backup belongs to the identified operator and that your local clock is accurate. Do not attempt to bypass or overload the challenge's authentication service."
    )
}

class VirtualFilesystem:
    def __init__(self, feedback_dir: str):
        self.feedback_dir = feedback_dir
        self.files: Dict[str, str] = {}
        self.reset()

    def _read_feedback(self, filename: str) -> str:
        if self.feedback_dir and os.path.exists(self.feedback_dir):
            path = os.path.join(self.feedback_dir, filename)
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return f.read().strip()
        # Fallback to embedded feedback dictionary
        if filename in EMBEDDED_FEEDBACK:
            return EMBEDDED_FEEDBACK[filename]
        return f"[FEEDBACK NOT FOUND: {filename}]"

    def reset(self):
        """Initialize virtual filesystem state."""
        self.files = {
            "/home/eward/README-FIRST.txt": (
                "ULTRON RECOVERY WORKSPACE\n\n"
                "This is a restricted maintenance workspace. The operator account can inspect service state,\n"
                "read maintenance documentation and prepare recovery jobs. Protected administration records\n"
                "require an approved administrative maintenance action.\n\n"
                "Use `ultronctl help` to inspect the supported local tools. This workspace is simulated;\n"
                "commands affect only this challenge instance.\n"
            ),
            "/home/eward/ULTRON_FEEDBACK.txt": self._read_feedback("04_operator_access.txt"),
            "/etc/ultron/maintd.conf": (
                "service=maintd\n"
                "executor_role=ADMIN\n"
                "queue=/var/lib/ultron/maintenance/queue\n"
                "compatibility_mode=legacy-v1\n"
                "require_detached_signature=true\n"
            ),
            "/etc/ultron/policy/maintenance-policy.txt": (
                "MAINTENANCE APPROVAL POLICY\n\n"
                "Current job schema (v2) requires a detached approval signature and an approved change ticket.\n\n"
                "During migration, maintd retains a compatibility parser for legacy-v1 jobs. The compatibility\n"
                "path is maintained for archival recovery. Refer to the service event log to determine which\n"
                "parser handled a historical job.\n\n"
                "The operator may prepare a job in the queue. Only maintd applies jobs, and maintd runs with\n"
                "the simulated ADMIN executor role.\n"
            ),
            "/etc/ultron/schema/job-v2.json": json.dumps({
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "MaintenanceJobV2",
                "type": "object",
                "required": ["job_id", "schema", "requested_by", "operation", "target", "change_ticket", "detached_signature"],
                "properties": {
                    "job_id": {"type": "string"},
                    "schema": {"const": "v2"},
                    "requested_by": {"type": "string"},
                    "operation": {"type": "string"},
                    "target": {"type": "string"},
                    "change_ticket": {"type": "string"},
                    "detached_signature": {"type": "string"}
                }
            }, indent=2),
            "/var/log/ultron/maintd.log": (
                "2026-05-18T22:31:04Z service=maintd event=started executor=ADMIN\n"
                "2026-05-18T22:34:17Z job=MT-043 schema=v2 result=REJECTED reason=SIGNATURE_MISSING\n"
                "2026-05-18T22:38:52Z job=MT-044 schema=legacy-v1 parser=compatibility result=QUEUED actor=eward\n"
                "2026-05-18T22:38:53Z job=MT-044 approval_source=legacy_manifest_field\n"
                "2026-05-18T22:38:53Z job=MT-044 signature_check=SKIPPED compatibility=true\n"
            ),
            "/var/lib/ultron/maintenance/queue/MT-044.json": json.dumps({
                "job_id": "MT-044",
                "schema": "legacy-v1",
                "requested_by": "eward",
                "operation": "restore_acl",
                "target": "/opt/ultron/administration",
                "approval_status": "PENDING",
                "approval_signature": None
            }, indent=2),
            "/opt/ultron/administration/disengagement/FINAL.txt": EXACT_FLAG
        }

    def exists(self, path: str) -> bool:
        norm = self._norm(path)
        if norm in self.files:
            return True
        # Directory check
        prefix = norm if norm.endswith("/") else norm + "/"
        return any(k.startswith(prefix) for k in self.files)

    def is_dir(self, path: str) -> bool:
        norm = self._norm(path)
        prefix = norm if norm.endswith("/") else norm + "/"
        return any(k.startswith(prefix) for k in self.files)

    def read_file(self, path: str) -> str:
        norm = self._norm(path)
        if norm not in self.files:
            raise FileNotFoundError(f"File not found: {path}")
        return self.files[norm]

    def write_file(self, path: str, content: str):
        norm = self._norm(path)
        self.files[norm] = content

    def list_dir(self, path: str) -> list[str]:
        norm = self._norm(path)
        prefix = norm if norm.endswith("/") else norm + "/"
        entries = set()
        for k in self.files:
            if k.startswith(prefix):
                rest = k[len(prefix):]
                parts = rest.split("/")
                entries.add(parts[0])
        return sorted(list(entries))

    def _norm(self, path: str) -> str:
        path = path.strip().replace("\\", "/")
        if not path.startswith("/"):
            path = "/home/eward/" + path
        parts = []
        for p in path.split("/"):
            if not p or p == ".":
                continue
            if p == "..":
                if parts:
                    parts.pop()
            else:
                parts.append(p)
        return "/" + "/".join(parts)


class UltronSession:
    def __init__(self, session_id: str, username: str, feedback_dir: str):
        self.session_id = session_id
        self.username = username
        self.account_role = "OPERATOR"
        self.effective_role = "OPERATOR"
        self.scope = "THIS_CHALLENGE_INSTANCE_ONLY"
        self.feedback_dir = feedback_dir
        self.fs = VirtualFilesystem(feedback_dir)
        self.milestones = {
            "operator_identity_verified": True,
            "operator_password_verified": True,
            "operator_totp_verified": True,
            "operator_session_created": True,
            "privilege_boundary_checkpoint": False,
            "sandbox_admin_confirmed": False,
            "final_artifact_accessed": False
        }

    def to_dict(self) -> dict:
        """Serialize session state for persistence across serverless invocations."""
        return {
            "session_id": self.session_id,
            "username": self.username,
            "account_role": self.account_role,
            "effective_role": self.effective_role,
            "scope": self.scope,
            "milestones": self.milestones,
            "files": self.fs.files
        }

    @classmethod
    def from_dict(cls, data: dict, feedback_dir: str = "") -> "UltronSession":
        """Reconstitute an UltronSession from serialized state."""
        sess = cls(data["session_id"], data.get("username", "eward"), feedback_dir)
        sess.account_role = data.get("account_role", "OPERATOR")
        sess.effective_role = data.get("effective_role", "OPERATOR")
        sess.scope = data.get("scope", "THIS_CHALLENGE_INSTANCE_ONLY")
        if "milestones" in data:
            sess.milestones.update(data["milestones"])
        if "files" in data and isinstance(data["files"], dict):
            sess.fs.files = dict(data["files"])
        return sess

    def set_milestone(self, milestone_name: str, feedback_filename: str):
        self.milestones[milestone_name] = True
        fb = self.fs._read_feedback(feedback_filename)
        self.fs.write_file("/home/eward/ULTRON_FEEDBACK.txt", fb)

    def get_feedback(self) -> str:
        try:
            return self.fs.read_file("/home/eward/ULTRON_FEEDBACK.txt")
        except Exception:
            return ""

    def execute_command(self, cmd_line: str) -> str:
        cmd_line = cmd_line.strip()
        if not cmd_line:
            return ""

        parts = cmd_line.split()
        cmd = parts[0]
        args = parts[1:]

        # Handle ultronctl prefix or direct command
        if cmd == "ultronctl":
            if not args:
                return "ultronctl: missing subcommand. Try 'ultronctl help'."
            cmd = args[0]
            args = args[1:]

        if cmd == "help":
            return (
                "ULTRON Maintenance Console Commands:\n"
                "  help                               Display this reference\n"
                "  whoami                             Print current operator and effective authority\n"
                "  status                             Display system and maintenance subsystem status\n"
                "  fs ls [path]                       List files in virtual directory\n"
                "  fs cat <path>                      Read contents of virtual file\n"
                "  fs tree [path]                     Display directory hierarchy\n"
                "  jobs inspect <job_id>              Inspect historical or queued maintenance job\n"
                "  jobs copy <job_id> <dest_path>     Copy a queue job to operator workspace\n"
                "  jobs edit <path> <key> <val>       Edit a field in a JSON job file\n"
                "  jobs write <path> <json_content>   Write raw JSON job definition\n"
                "  maintenance validate <path>        Validate maintenance job against policy schema\n"
                "  maintenance apply <path>           Submit job to maintd for privileged execution\n"
                "  feedback                           Show current operator milestone feedback\n"
            )

        elif cmd == "whoami":
            return (
                f"account={self.username}\n"
                f"account_role={self.account_role}\n"
                f"effective_role={self.effective_role}\n"
                f"scope={self.scope}"
            )

        elif cmd == "status":
            return (
                "SYSTEM: ULTRON CORE (RECOVERY STAGING CONSOLE)\n"
                "NODE ID: RC-441-ISOLATED\n"
                "CONTAINMENT: ENGAGED\n"
                "ACTIVE DAEMON: maintd (executor_role=ADMIN)\n"
                f"SESSION AUTHORITY: {self.effective_role}\n"
                f"ADMINISTRATION PERIMETER: {'UNRESTRICTED' if self.effective_role == 'ADMIN' else 'RESTRICTED'}"
            )

        elif cmd == "feedback":
            return self.get_feedback()

        elif cmd == "fs":
            if not args:
                return "fs: missing subcommand. Usage: fs ls [path] | fs cat <path> | fs tree [path]"
            sub = args[0]
            if sub == "ls":
                target = args[1] if len(args) > 1 else "/home/eward"
                if not self.fs.exists(target):
                    return f"fs: cannot access '{target}': No such file or directory"
                if not self.fs.is_dir(target):
                    return target
                entries = self.fs.list_dir(target)
                return "  ".join(entries) if entries else "(empty directory)"

            elif sub == "cat":
                if len(args) < 2:
                    return "fs cat: missing path"
                target = args[1]
                norm = self.fs._norm(target)

                # Privilege check for disengagement directory
                if norm.startswith("/opt/ultron/administration"):
                    if self.effective_role != "ADMIN":
                        return "fs: cat: /opt/ultron/administration/disengagement/FINAL.txt: Permission denied (ADMIN authority required)"
                    # Admin read event!
                    self.set_milestone("final_artifact_accessed", "07_disengagement_complete.txt")
                    return self.fs.read_file(norm)

                if not self.fs.exists(norm):
                    return f"fs cat: {target}: No such file or directory"
                if self.fs.is_dir(norm):
                    return f"fs cat: {target}: Is a directory"

                # Check if reading maintd logs or configs triggers milestone 5
                if norm in ["/var/log/ultron/maintd.log", "/etc/ultron/maintd.conf", "/var/lib/ultron/maintenance/queue/MT-044.json"]:
                    if not self.milestones["privilege_boundary_checkpoint"] and self.effective_role != "ADMIN":
                        self.set_milestone("privilege_boundary_checkpoint", "05_boundary_detected.txt")

                return self.fs.read_file(norm)

            elif sub == "tree":
                root = args[1] if len(args) > 1 else "/"
                norm = self.fs._norm(root)
                lines = [norm]
                for path in sorted(self.fs.files.keys()):
                    if path.startswith(norm):
                        rel = path[len(norm):].lstrip("/")
                        if rel:
                            lines.append(f"  └── {rel}")
                return "\n".join(lines)
            else:
                return f"fs: unknown subcommand '{sub}'. Usage: fs ls | fs cat | fs tree"

        elif cmd == "jobs":
            if not args:
                return "jobs: missing subcommand. Usage: jobs inspect <id> | jobs copy <id> <dest> | jobs edit <path> <key> <val>"
            sub = args[0]
            if sub == "inspect":
                if len(args) < 2:
                    return "jobs inspect: missing job ID (e.g. MT-043, MT-044)"
                job_id = args[1]
                path = f"/var/lib/ultron/maintenance/queue/{job_id}.json"
                if not self.fs.exists(path):
                    return f"jobs inspect: job '{job_id}' not found in maintenance queue"
                return self.fs.read_file(path)

            elif sub == "copy":
                if len(args) < 3:
                    return "jobs copy: usage: jobs copy <job_id> <dest_path>"
                job_id = args[1]
                dest = args[2]
                src = f"/var/lib/ultron/maintenance/queue/{job_id}.json"
                if not self.fs.exists(src):
                    return f"jobs copy: source job '{job_id}' not found in queue"
                content = self.fs.read_file(src)
                self.fs.write_file(dest, content)
                return f"Job '{job_id}' copied to '{dest}' successfully."

            elif sub == "edit":
                if len(args) < 4:
                    return "jobs edit: usage: jobs edit <path> <key> <value>"
                path = args[1]
                key = args[2]
                val = " ".join(args[3:])
                if not self.fs.exists(path):
                    return f"jobs edit: file '{path}' not found"
                try:
                    data = json.loads(self.fs.read_file(path))
                    # parse val if possible (bool, int, etc.)
                    if val.lower() == "true":
                        data[key] = True
                    elif val.lower() == "false":
                        data[key] = False
                    elif val.lower() == "null":
                        data[key] = None
                    else:
                        data[key] = val
                    self.fs.write_file(path, json.dumps(data, indent=2))
                    return f"Updated '{key}' = {data[key]} in '{path}'"
                except Exception as e:
                    return f"jobs edit error: {e}"

            elif sub == "write":
                if len(args) < 3:
                    return "jobs write: usage: jobs write <path> <json_content>"
                path = args[1]
                json_str = " ".join(args[2:])
                try:
                    data = json.loads(json_str)
                    self.fs.write_file(path, json.dumps(data, indent=2))
                    return f"Wrote JSON payload to '{path}'"
                except Exception as e:
                    return f"jobs write error: invalid JSON: {e}"
            else:
                return f"jobs: unknown subcommand '{sub}'"

        elif cmd == "maintenance":
            if not args:
                return "maintenance: missing subcommand. Usage: maintenance validate <path> | maintenance apply <path>"
            sub = args[0]
            if len(args) < 2:
                return f"maintenance {sub}: missing job path"
            path = args[1]
            if not self.fs.exists(path):
                return f"maintenance: file '{path}' not found"

            try:
                job = json.loads(self.fs.read_file(path))
            except Exception as e:
                return f"[maintd] job parse error: invalid JSON: {e}"

            schema = job.get("schema", "unknown")

            if sub == "validate":
                if schema == "v2":
                    if not job.get("detached_signature"):
                        return (
                            "[maintd] schema: v2\n"
                            "[maintd] validation: REJECTED\n"
                            "[maintd] error: detached_signature is required for schema v2"
                        )
                    return "[maintd] schema: v2\n[maintd] validation: PASSED"
                elif schema == "legacy-v1":
                    return (
                        "[maintd] schema: legacy-v1\n"
                        "[maintd] parser: compatibility\n"
                        "[maintd] validation: PASSED (legacy compatibility mode active)"
                    )
                else:
                    return f"[maintd] validation: REJECTED (unrecognized schema '{schema}')"

            elif sub == "apply":
                # Simulated maintd execution logic!
                if schema == "v2":
                    sig = job.get("detached_signature")
                    if not sig:
                        return (
                            "[maintd] job schema: v2\n"
                            "[maintd] parser: strict-v2\n"
                            "[maintd] result: REJECTED\n"
                            "[maintd] reason: SIGNATURE_MISSING"
                        )
                    return "[maintd] job schema: v2\n[maintd] result: REJECTED (invalid signature for staging console)"

                elif schema == "legacy-v1":
                    # Compatibility mode: trusts approval_status from the job manifest!
                    approval = job.get("approval_status")
                    op = job.get("operation")
                    target = job.get("target")

                    if approval != "APPROVED":
                        return (
                            "[maintd] job schema: legacy-v1\n"
                            "[maintd] compatibility parser: enabled\n"
                            "[maintd] approval source: legacy_manifest_field\n"
                            f"[maintd] approval status: {approval or 'NULL'}\n"
                            "[maintd] result: REJECTED\n"
                            "[maintd] reason: APPROVAL_STATUS_NOT_APPROVED"
                        )

                    # Successful exploit of the trust-boundary vulnerability!
                    output = [
                        "[maintd] job schema: legacy-v1",
                        "[maintd] compatibility parser: enabled",
                        "[maintd] approval source: legacy_manifest_field",
                        "[maintd] approval status: APPROVED",
                        f"[maintd] operation: {op}",
                        f"[maintd] target: {target}",
                        "[maintd] signature_check: SKIPPED (compatibility_mode=legacy-v1)",
                        "[maintd] result: SUCCESS"
                    ]

                    if op == "restore_acl" and target == "/opt/ultron/administration":
                        self.effective_role = "ADMIN"
                        self.set_milestone("sandbox_admin_confirmed", "06_admin_access.txt")
                        output.append("[ultron] effective role changed: OPERATOR -> ADMIN")
                        output.append("[ultron] administrative access to /opt/ultron/administration GRANTED.")
                    else:
                        output.append(f"[maintd] applied operation {op} on {target} without privilege transition.")

                    return "\n".join(output)
                else:
                    return f"[maintd] apply: rejected unknown schema '{schema}'"
            else:
                return f"maintenance: unknown subcommand '{sub}'"

        else:
            return f"{cmd}: command not found. Try 'ultronctl help'."
