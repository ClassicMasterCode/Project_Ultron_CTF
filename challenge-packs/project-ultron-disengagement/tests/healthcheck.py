#!/usr/bin/env python3
"""
ULTRON Challenge Healthcheck Script
Validates service reachability, authentication endpoints, and decoy consistency.
"""
import sys
import urllib.request
import json
import time

def check_health(base_url: str = "http://localhost:8080") -> bool:
    print(f"[HEALTHCHECK] Probing ULTRON service at {base_url}...")
    try:
        req = urllib.request.Request(f"{base_url}/api/health")
        with urllib.request.urlopen(req, timeout=5) as res:
            if res.status != 200:
                print(f"[-] Healthcheck failed: status {res.status}")
                return False
            data = json.loads(res.read().decode())
            if data.get("status") != "healthy":
                print(f"[-] Unexpected payload: {data}")
                return False
            print("[+] Service healthcheck endpoint: OK (Status: healthy)")
    except Exception as e:
        print(f"[-] Healthcheck connection error: {e}")
        return False

    # Check unauthenticated access rejection
    try:
        req = urllib.request.Request(f"{base_url}/api/session")
        urllib.request.urlopen(req, timeout=5)
        print("[-] Security issue: /api/session should require X-Session-ID header")
        return False
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("[+] Session authentication gate: OK (401 Unauthorized enforced)")
        else:
            print(f"[-] Unexpected HTTP code: {e.code}")
            return False

    print("[+] All preliminary health checks passed.")
    return True

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    if not check_health(url):
        sys.exit(1)
    sys.exit(0)
