# Vercel Deployment Manual — PROJECT ULTRON CTF Platform

This guide provides instructions for deploying the **HERCULES CTF: PROJECT ULTRON** web application to **Vercel** serverless infrastructure without configuration errors, session loss, or bundling failures.

---

## 1. Architectural Highlights on Vercel

```text
[ Participant Browser ]
        │
        ├───► GET / , /style.css , /app.js ──► [ Vercel Edge CDN ] ────► /public (Instant 0ms)
        │
        └───► /api/* (login, terminal, flag) ─► [ Vercel Rewrites ] ───► /api/index.py (Serverless Python)
                                                                                  │
                                                                           ┌──────┴──────────────┐
                                                                           ▼                     ▼
                                                                  [In-Memory Cache]    [/tmp Disk Persistence]
```

### Prevention of Common Vercel Deployment Errors:
1. **No Output Directory / Framework Detection Failure**:
   - Resolved with root-level `vercel.json` routing configuration and `public/` directory for static HUD frontend assets.
2. **Missing Module / Bundling Errors in Serverless Lambdas**:
   - `api/index.py` and `api/ultron_sim.py` are co-located in `api/` to ensure self-contained bundling without external relative path errors.
   - All 11 milestone telemetry feedback logs are embedded directly in code as fallback constants to prevent missing file crashes in ephemeral Lambda containers.
3. **Session Eviction Across Ephemeral Serverless Containers**:
   - Serverless instances are stateless and subject to cold starts.
   - `UltronSession` features full `to_dict()` and `from_dict()` serialization.
   - Sessions are cached in memory and automatically backed by the container's `/tmp/ultron_sessions` store, preserving progress, virtual file changes, and administrator privileges across requests.
4. **Proxy IP Rate-Limiting Collisions**:
   - `extract_client_ip` inspects `X-Forwarded-For` and `X-Real-IP` before falling back to local address, preventing shared proxy IP collisions.
5. **CORS & Preflight Blocks**:
   - `do_OPTIONS` explicitly responds with `204 No Content` and CORS headers (`Access-Control-Allow-Origin: *`, `Access-Control-Allow-Headers: Content-Type, X-Session-ID, Authorization`).

---

## 2. Repository Structure for Vercel

```text
C:/Users/hp/ctf/
├── vercel.json                        # Vercel routing, rewrite rules, and security headers
├── requirements.txt                  # Python build specifications
│
├── api/                              # Vercel Serverless Functions
│   ├── index.py                      # Main Python API gateway (BaseHTTPRequestHandler)
│   └── ultron_sim.py                 # Virtual filesystem and simulation engine
│
├── public/                           # Static assets served directly by Vercel CDN
│   ├── index.html                    # Stark Systems HUD interface
│   ├── style.css                     # Neon retro terminal stylesheet
│   └── app.js                        # Client API communicator & state synchronizer
│
├── challenge-packs/                  # Master HERCULES challenge files
├── orchestrator/                     # Platform orchestration tools
└── platform/                         # CTFd export and integration scripts
```

---

## 3. How to Deploy

### Option A: Deploy via Vercel Dashboard (GitHub / GitLab / Bitbucket)
1. Push this repository to your Git provider (e.g. GitHub).
2. Log in to [vercel.com](https://vercel.com) and click **"Add New Project"**.
3. Select your repository and click **Import**.
4. In the configuration window:
   - **Framework Preset**: Leave as `Other` (detected via `vercel.json`).
   - **Root Directory**: `.` (leave as root).
   - **Build Command**: None (automatic).
   - **Output Directory**: None (automatically uses `public`).
5. (Optional) Set Environment Variables:
   - `ULTRON_OPERATOR_USER`: Operator username (default: `eward`)
   - `ULTRON_OPERATOR_PASS`: Operator password (default: `stark-disengage-recovery-441-alpha`)
   - `ULTRON_TOTP_SECRET`: TOTP base32 secret (default: `JBSWY3DPEHPK3PXP`)
6. Click **Deploy**.

---

### Option B: Deploy via Vercel CLI
```bash
# 1. Install Vercel CLI (if not installed)
npm install -g vercel

# 2. Authenticate and deploy to preview
vercel

# 3. Deploy to production
vercel --prod
```

---

## 4. Verification & Testing

### 1. Test Locally Prior to Deployment
Run the Vercel-compatible server locally:
```powershell
python api/index.py 8080
```
Open `http://localhost:8080` in your browser.

### 2. Verify Healthcheck Against Deployed Site
```powershell
python challenge-packs/project-ultron-disengagement/tests/healthcheck.py https://your-project.vercel.app
```

### 3. Verify End-to-End Solve Harness
```powershell
python challenge-packs/project-ultron-disengagement/tests/solve.py https://your-project.vercel.app
```
When all 7 stages complete with `🏆 ALL 7 HERCULES CHALLENGE STAGES COMPLETED & VERIFIED SUCCESSFULLY!`, your deployment is completely validated.
