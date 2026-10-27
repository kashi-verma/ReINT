from datetime import date, time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.models import DecisionResponse
from backend.app.repository import load_sample_frames
from backend.app.services.decision import build_decision_analysis


app = FastAPI(
    title="REint Wind Decision API",
    version="0.1.0",
    description="Point-in-time replay of Elexon wind forecasts and FUELHH actuals.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/decision", response_model=DecisionResponse)
def get_decision(
    decision_date: date = Query(default=date(2026, 1, 5)),
    cutoff: time = Query(default=time(9, 20)),
    timezone: str = Query(default="Europe/London"),
) -> dict:
    if decision_date != date(2026, 1, 5):
        raise HTTPException(
            status_code=422,
            detail="This vertical slice contains data only for the 2026-01-05 decision.",
        )
    try:
        forecasts, actuals = load_sample_frames()
        return build_decision_analysis(
            forecasts,
            actuals,
            decision_date=decision_date,
            cutoff=cutoff,
            timezone_name=timezone,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

