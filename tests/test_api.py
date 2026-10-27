from fastapi.testclient import TestClient
import pandas as pd

from backend.app.main import app
from backend.app.repository import load_sample_frames


client = TestClient(app)


def test_decision_endpoint_returns_saved_sample() -> None:
    response = client.get(
        "/api/v1/decision",
        params={"decision_date": "2026-01-05", "cutoff": "09:20"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["decisionDate"] == "2026-01-05"
    assert body["deliveryDate"] == "2026-01-06"
    assert body["cutoffUtc"] == "2026-01-05T09:20:00Z"
    assert body["errorDefinition"] == "forecast minus actual"
    assert body["retrospective"] is True
    assert body["metrics"]["expectedPeriods"] == 24
    assert body["metrics"]["forecastPeriods"] == 24
    assert body["metrics"]["matchedPeriods"] == 24
    assert len(body["points"]) == 24
    assert body["points"][0]["forecastPublishTime"] == "2026-01-05T07:30:00Z"


def test_saved_sample_contains_real_0930_publication_but_api_excludes_it() -> None:
    forecasts, _ = load_sample_frames()
    target = forecasts.loc[
        forecasts["startTime"].eq("2026-01-06T00:00:00Z")
        & forecasts["publishTime"].eq("2026-01-05T09:30:00Z")
    ]
    assert not target.empty

    response = client.get("/api/v1/decision")
    first_point = response.json()["points"][0]
    assert pd.Timestamp(first_point["forecastPublishTime"]) < pd.Timestamp(
        "2026-01-05T09:20:00Z"
    )


def test_decision_endpoint_rejects_dates_not_in_snapshot() -> None:
    response = client.get(
        "/api/v1/decision", params={"decision_date": "2026-01-06"}
    )

    assert response.status_code == 422
    assert "only for the 2026-01-05 decision" in response.json()["detail"]

