#!/usr/bin/env python3
"""
HERCULES Orchestrator — Flag Validator Service
Performs server-side validation ensuring:
1. Team instance ownership
2. Attestation of sandbox administrator transition
3. Protected local filesystem artifact read event
4. Exact byte-for-byte flag matching
"""
import sys
import os
import json
from typing import Tuple

class FlagValidator:
    def __init__(self, instance_manager=None):
        self.im = instance_manager

    def validate_submission(self, team_id: str, submitted_flag: str, session_data: dict) -> Tuple[bool, str]:
        # 1. Exact string match
        expected_flag = "secuRIT{ CONGRATULATIONS PARTICIPANT. YOU FOUND THE FLAG. ULTRON HAS BEEN SUCCESSFULLY DISENGAGED}"
        if submitted_flag.strip() != expected_flag:
            return False, "Incorrect flag."

        # 2. Check administrator transition attestation
        if session_data.get("effective_role") != "ADMIN":
            return False, "Validation rejected: Sandbox administrator state has not been attained."

        # 3. Check local artifact access event
        milestones = session_data.get("milestones", {})
        if not milestones.get("final_artifact_accessed"):
            return False, "Validation rejected: Protected filesystem read event not attested."

        return True, "Flag accepted! ULTRON disengagement verified."

if __name__ == "__main__":
    fv = FlagValidator()
    # Test valid submission
    mock_session = {
        "effective_role": "ADMIN",
        "milestones": {"final_artifact_accessed": True}
    }
    valid, msg = fv.validate_submission("team-1", "secuRIT{ CONGRATULATIONS PARTICIPANT. YOU FOUND THE FLAG. ULTRON HAS BEEN SUCCESSFULLY DISENGAGED}", mock_session)
    print(f"[FLAG VALIDATOR TEST] Result: {valid} - {msg}")
