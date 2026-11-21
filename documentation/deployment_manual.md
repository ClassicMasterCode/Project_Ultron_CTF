# HERCULES CTF — Deployment & Operations Manual

## 1. Architecture Overview
The platform deployment consists of:
- **CTFd Engine**: Registration, challenge listing, hint purchasing (with automatic deductions), and scoreboard.
- **Reverse Proxy (Nginx/Traefik)**: TLS termination and traffic routing.
- **Challenge Runner / Orchestrator**: Manages disposable team instances and flag validation.
- **ULTRON Challenge Sandbox**: Isolated container running the recovery portal and virtual simulator.

## 2. Running the ULTRON Challenge Locally
To run the challenge service locally:
```powershell
# Activate Python virtual environment
.\venv\Scripts\Activate.ps1

# Start the portal service (default port 8080)
python challenge-packs/project-ultron-disengagement/service/server.py 8080
```
Open a browser and navigate to `http://localhost:8080`.

## 3. Running Automated Acceptance Tests
```powershell
# Run the healthcheck
python challenge-packs/project-ultron-disengagement/tests/healthcheck.py http://localhost:8080

# Run the complete end-to-end author solve
python challenge-packs/project-ultron-disengagement/tests/solve.py http://localhost:8080
```

## 4. CTFd Integration
To export the challenge definition for import into CTFd:
```powershell
python platform/ctfd/export_ctfd_challenge.py
```
This produces `platform/ctfd/ctfd_challenge.json` and `platform/ctfd/ultron_ctfd_package.zip`.
In CTFd Admin panel:
1. Navigate to Challenges -> Import.
2. Upload the exported package.
3. Verify that the 3 paid hints (cost: 50, 100, 150 points) are properly linked.
