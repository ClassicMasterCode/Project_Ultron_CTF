#!/usr/bin/env python3
"""
HERCULES Challenge Manifest Validator & Secret Hygiene Linter
Enforces authoring standards, file consistency, and secret isolation.
"""
import os
import sys
import yaml
import re

def validate_manifest(manifest_path: str) -> bool:
    print(f"[VALIDATOR] Checking manifest: {manifest_path}")
    if not os.path.exists(manifest_path):
        print(f"[-] Error: Manifest not found: {manifest_path}")
        return False

    with open(manifest_path, "r") as f:
        data = yaml.safe_load(f)

    # 1. Required core attributes
    required_fields = ["id", "title", "category", "difficulty", "points", "stages", "hints"]
    for field in required_fields:
        if field not in data:
            print(f"[-] Missing required field: {field}")
            return False
    print("[+] Core manifest fields: OK")

    # 2. Check points and difficulty
    if data["points"] != 500 or data["difficulty"].lower() != "hard":
        print(f"[-] Unexpected points/difficulty: {data.get('points')}, {data.get('difficulty')}")
        return False
    print(f"[+] Points & Difficulty: {data['points']} pts, {data['difficulty']} - OK")

    # 3. Check 7 stages
    stages = data["stages"]
    if len(stages) != 7:
        print(f"[-] Expected 7 stages, found {len(stages)}")
        return False
    print(f"[+] 7 Stages defined: OK")

    # 4. Check hints
    hints = data["hints"]
    expected_costs = [50, 100, 150]
    actual_costs = [h.get("cost") for h in hints]
    if actual_costs != expected_costs:
        print(f"[-] Hint costs mismatch! Expected {expected_costs}, got {actual_costs}")
        return False
    print(f"[+] Hint costs verified: {actual_costs} pts - OK")

    # 5. Secret Hygiene Audit on Public Directory
    base_dir = os.path.dirname(manifest_path)
    public_dir = os.path.join(base_dir, "public")
    leaked_secrets = []
    forbidden_patterns = [
        re.compile(r"secuRIT\{"),
        re.compile(r"stark-disengage-recovery-441-alpha"),
        re.compile(r"JBSWY3DPEHPK3PXP")
    ]

    # Note: AUTH-09.seed intentionally holds the challenge TOTP seed for participants,
    # but the flag and cleartext password must NEVER appear in public assets.
    critical_forbidden = [
        re.compile(r"secuRIT\{"),
        re.compile(r"stark-disengage-recovery-441-alpha")
    ]

    for root, _, files in os.walk(public_dir):
        for f in files:
            p = os.path.join(root, f)
            if f.endswith((".csv", ".txt", ".md", ".json", ".log", ".py")):
                with open(p, "r", encoding="utf-8", errors="ignore") as content_f:
                    text = content_f.read()
                    for pat in critical_forbidden:
                        if pat.search(text):
                            leaked_secrets.append((p, pat.pattern))

    if leaked_secrets:
        print(f"[-] CRITICAL SECURITY LEAK DETECTED IN PUBLIC ASSETS:")
        for path, pat in leaked_secrets:
            print(f"    - File: {path} matched secret pattern: {pat}")
        return False
    print("[+] Public secret hygiene audit: PASSED (No cleartext flags or passwords found)")

    print("\n[✓] ALL HERCULES RELEASE GATES PASSED SUCCESSFULLY!")
    return True

if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else "challenge-packs/project-ultron-disengagement/challenge.yaml"
    if not validate_manifest(p):
        sys.exit(1)
    sys.exit(0)
