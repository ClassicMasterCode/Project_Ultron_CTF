#!/usr/bin/env python3
"""
HERCULES Orchestrator — Team Instance Manager
Provisions isolated, reproducible challenge instances with per-team
secrets, randomized credentials, and isolated state.
"""
import os
import sys
import json
import secrets
import base64
import shutil
from typing import Dict, Any

class InstanceManager:
    def __init__(self, data_dir: str = "instances"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.state_file = os.path.join(data_dir, "instances.json")
        self.instances: Dict[str, dict] = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.state_file):
            with open(self.state_file, "r") as f:
                return json.load(f)
        return {}

    def _save(self):
        with open(self.state_file, "w") as f:
            json.dump(self.instances, f, indent=2)

    def provision_instance(self, team_id: str, seed: int = None) -> dict:
        """Create a fresh instance configuration for a team."""
        instance_id = f"inst-{team_id}-{secrets.token_hex(4)}"

        # Generate unique operator password and TOTP secret
        password = f"stark-recov-{secrets.token_hex(6)}"
        totp_secret = base64.b32encode(secrets.token_bytes(10)).decode("ascii")
        flag = f"secuRIT{{ CONGRATULATIONS PARTICIPANT. YOU FOUND THE FLAG. ULTRON HAS BEEN SUCCESSFULLY DISENGAGED}}"

        instance_data = {
            "team_id": team_id,
            "instance_id": instance_id,
            "created_at": os.path.getctime(self.data_dir),
            "operator_username": "eward",
            "operator_password": password,
            "totp_secret": totp_secret,
            "flag": flag,
            "status": "ACTIVE",
            "milestones": {
                "operator_identity_verified": False,
                "operator_password_verified": False,
                "operator_totp_verified": False,
                "operator_session_created": False,
                "privilege_boundary_checkpoint": False,
                "sandbox_admin_confirmed": False,
                "final_artifact_accessed": False
            }
        }
        self.instances[team_id] = instance_data
        self._save()
        return instance_data

    def get_instance(self, team_id: str) -> dict:
        return self.instances.get(team_id)

    def terminate_instance(self, team_id: str):
        if team_id in self.instances:
            del self.instances[team_id]
            self._save()

if __name__ == "__main__":
    im = InstanceManager()
    sample = im.provision_instance("team-alpha")
    print(f"[INSTANCE MANAGER] Provisioned instance for team-alpha: {sample['instance_id']}")
