from datetime import date, time

import pandas as pd
import pytest

from backend.app.services.decision import build_decision_analysis


def forecast(start: str, published: str, generation: float) -> dict:
    return {
        "startTime": start,
        "publishTime": published,
        "generation": generation,
    }


def actual(start: str, generation: float, published: str | None = None) -> dict:
    timestamp = pd.Timestamp(start)
    return {
        "startTime": start,
        "publishTime": published or (timestamp + pd.Timedelta(minutes=30)).isoformat(),
        "fuelType": "WIND",
        "generation": generation,
    }


def analyze(forecasts: list[dict], actuals: list[dict]) -> dict:
    return build_decision_analysis(
        pd.DataFrame(forecasts),
        pd.DataFrame(actuals),
        decision_date=date(2026, 1, 5),
        cutoff=time(9, 20),
    )


def test_forecast_published_at_0930_is_excluded_at_0920_cutoff() -> None:
    result = analyze(
        [
            forecast("2026-01-06T00:00:00Z", "2026-01-05T07:30:00Z", 100),
            forecast("2026-01-06T00:00:00Z", "2026-01-05T09:30:00Z", 999),
        ],
        [
            actual("2026-01-06T00:00:00Z", 80),
            actual("2026-01-06T00:30:00Z", 100),
        ],
    )

    point = result["points"][0]
    assert point["forecastMw"] == 100
    assert point["forecastPublishTime"].isoformat() == "2026-01-05T07:30:00+00:00"


def test_missing_forecast_remains_missing_instead_of_using_later_publication() -> None:
    result = analyze(
        [forecast("2026-01-06T01:00:00Z", "2026-01-05T09:30:00Z", 250)],
        [
            actual("2026-01-06T01:00:00Z", 200),
            actual("2026-01-06T01:30:00Z", 220),
        ],
    )

    point = result["points"][1]
    assert point["forecastMw"] is None
    assert point["forecastPublishTime"] is None
    assert point["actualMw"] == 210
    assert point["signedErrorMw"] is None
    assert "later forecasts were not substituted" in result["warnings"][0]


def test_signed_error_metrics_are_forecast_minus_actual() -> None:
    result = analyze(
        [
            forecast("2026-01-06T00:00:00Z", "2026-01-05T07:30:00Z", 110),
            forecast("2026-01-06T01:00:00Z", "2026-01-05T07:30:00Z", 180),
        ],
        [
            actual("2026-01-06T00:00:00Z", 90),
            actual("2026-01-06T00:30:00Z", 100),
            actual("2026-01-06T01:00:00Z", 195),
            actual("2026-01-06T01:30:00Z", 205),
        ],
    )

    # Errors are +15 and -20 MW.
    assert result["points"][0]["signedErrorMw"] == 15
    assert result["points"][1]["signedErrorMw"] == -20
    assert result["metrics"]["maeMw"] == 17.5
    assert result["metrics"]["biasMw"] == -2.5
    assert result["metrics"]["rmseMw"] == pytest.approx(17.67766953)


def test_incomplete_actual_hour_is_not_averaged_as_if_complete() -> None:
    result = analyze(
        [forecast("2026-01-06T00:00:00Z", "2026-01-05T07:30:00Z", 110)],
        [actual("2026-01-06T00:00:00Z", 90)],
    )

    assert result["points"][0]["actualHalfHourCount"] == 1
    assert result["points"][0]["actualMw"] is None
    assert result["points"][0]["signedErrorMw"] is None

