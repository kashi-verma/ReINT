# REint wind decision API — backend vertical slice

This repository contains a tested FastAPI backend and React/TypeScript frontend
for the 5 January 2026 purchasing decision.

The API selects, for every hourly target on 6 January, the newest WINDFOR record
whose `publishTime` is at or before the configured 09:20 Europe/London cutoff.
It averages the two corresponding half-hour FUELHH WIND observations and defines
signed error as `forecast MW - actual MW`.

## Set up and test

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
```

On a Windows machine whose application-control policy blocks native packages
inside OneDrive, create the environment with `--system-site-packages` to reuse a
trusted system pandas installation.

## Reproduce the raw snapshot

```powershell
.\.venv\Scripts\python.exe scripts\fetch_elexon.py
```

The script saves the unmodified JSON response bodies under `data/raw` and writes
`manifest.json` with source URLs, retrieval time, record counts, byte counts, and
SHA-256 hashes. The WINDFOR request intentionally includes one hour after the
cutoff, making the exclusion of the real 09:30 publication testable. Those later
records remain ineligible in the selection function.

## Run the API

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

Then open:

- `http://127.0.0.1:8000/` (built frontend)
- `http://127.0.0.1:8000/api/v1/decision`
- `http://127.0.0.1:8000/docs`

## Build or develop the frontend

Install and build once:

```powershell
cd frontend
npm.cmd install
npm.cmd run test
npm.cmd run build
cd ..
```

The production build is served by FastAPI at `http://127.0.0.1:8000/`. During
frontend development, keep FastAPI running in one terminal and start Vite in a
second terminal:

```powershell
cd frontend
npm.cmd run dev
```

Then open `http://127.0.0.1:5173/`. Vite proxies `/api` requests to FastAPI on
port 8000.

This slice accepts only `decision_date=2026-01-05`, because that is the only raw
sample checked into the repository. The response explicitly labels the metrics
as retrospective and reports missing forecast or actual coverage without filling
from later publications.
