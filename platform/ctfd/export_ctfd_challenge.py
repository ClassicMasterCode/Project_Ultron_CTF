#!/usr/bin/env python3
"""
CTFd Challenge Exporter
Generates standard CTFd export JSON and ZIP packages for the ULTRON challenge,
including the 3 paid hints (cost: 50, 100, 150 points) and dynamic scoring rules.
"""
import os
import sys
import json
import zipfile

def export_ctfd_package(output_json: str = "platform/ctfd/ctfd_challenge.json", output_zip: str = "platform/ctfd/ultron_ctfd_package.zip"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    challenge_dir = os.path.join(base_dir, "..", "..", "challenge-packs", "project-ultron-disengagement")

    with open(os.path.join(challenge_dir, "public", "challenge-briefing.txt"), "r") as f:
        description = f.read()

    hints = [
        {
            "title": "HINT 1 — Identity",
            "content": "The operator's identity is not established by any single document. Compare the records using their timestamps, identifiers and naming conventions. Look for the identity that appears consistently across the incident and authentication records.",
            "cost": 50
        },
        {
            "title": "HINT 2 — Authentication",
            "content": "There are three separate parts to the login process. The password recovery material and the authenticator migration record serve different purposes. Focus on the recovery note and verify that you have selected the correct account's second-factor backup.",
            "cost": 100
        },
        {
            "title": "HINT 3 — Administrator access",
            "content": "Having a valid operator session does not mean the system trusts every operation you request. Examine the maintenance process, especially the relationship between the component's execution privileges and the configuration it consumes.",
            "cost": 150
        }
    ]

    ctfd_data = {
        "name": "PROJECT ULTRON: Disengagement",
        "category": "Web / Digital Forensics / Systems",
        "description": description,
        "value": 500,
        "type": "standard",
        "state": "visible",
        "max_attempts": 0,
        "flags": [
            {
                "type": "static",
                "content": "secuRIT{ CONGRATULATIONS PARTICIPANT. YOU FOUND THE FLAG. ULTRON HAS BEEN SUCCESSFULLY DISENGAGED}",
                "data": "case_sensitive"
            }
        ],
        "tags": [
            "Forensics",
            "Web",
            "Privilege-Escalation",
            "HERCULES-Level-4",
            "AI-Resilient"
        ],
        "hints": hints
    }

    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w") as f:
        json.dump(ctfd_data, f, indent=2)
    print(f"[CTFd EXPORT] Wrote CTFd challenge schema to {output_json}")

    # Generate complete zip package with public attachments
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(output_json, arcname="challenge.json")
        evidence_dir = os.path.join(challenge_dir, "public", "evidence")
        for root, _, files in os.walk(evidence_dir):
            for file in files:
                full_p = os.path.join(root, file)
                rel_p = os.path.relpath(full_p, challenge_dir)
                z.write(full_p, arcname=rel_p)

    print(f"[CTFd EXPORT] Packaged CTFd distribution zip to {output_zip}")

if __name__ == "__main__":
    export_ctfd_package()
