from __future__ import annotations

from datetime import date, datetime, time, timedelta
from math import sqrt
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pandas as pd


FORECAST_COLUMNS = {"startTime", "publishTime", "generation"}
ACTUAL_COLUMNS = {"startTime", "publishTime", "generation", "fuelType"}


def _require_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{label} data is missing columns: {sorted(missing)}")


def _as_utc(frame: pd.DataFrame, label: str) -> pd.DataFrame:
    result = frame.copy()
    for column in ("startTime", "publishTime"):
        result[column] = pd.to_datetime(result[column], utc=True, errors="coerce")
    result["generation"] = pd.to_numeric(result["generation"], errors="coerce")
    if result[["startTime", "publishTime"]].isna().any().any():
        raise ValueError(f"{label} data contains an invalid timestamp")
    return result


def decision_window(
    decision_date: date, cutoff: time, timezone_name: str
) -> tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp]:
    try:
        timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown timezone: {timezone_name}") from exc

    cutoff_local = datetime.combine(decision_date, cutoff, tzinfo=timezone)
    delivery_date = decision_date + timedelta(days=1)
    delivery_start_local = datetime.combine(delivery_date, time.min, tzinfo=timezone)
    delivery_end_local = datetime.combine(
        delivery_date + timedelta(days=1), time.min, tzinfo=timezone
    )
    return (
        pd.Timestamp(cutoff_local).tz_convert("UTC"),
        pd.Timestamp(delivery_start_local).tz_convert("UTC"),
        pd.Timestamp(delivery_end_local).tz_convert("UTC"),
    )


def select_latest_forecasts(
    forecasts: pd.DataFrame,
    *,
    cutoff_utc: pd.Timestamp,
    delivery_start_utc: pd.Timestamp,
    delivery_end_utc: pd.Timestamp,
) -> pd.DataFrame:
    """Select the latest eligible publication independently for each target hour."""
    _require_columns(forecasts, FORECAST_COLUMNS, "Forecast")
    data = _as_utc(forecasts, "Forecast")
    eligible = data.loc[
        (data["publishTime"] <= cutoff_utc)
        & (data["startTime"] >= delivery_start_utc)
        & (data["startTime"] < delivery_end_utc)
    ]
    selected = (
        eligible.sort_values(["startTime", "publishTime"], kind="stable")
        .drop_duplicates(subset=["startTime"], keep="last")
        .loc[:, ["startTime", "publishTime", "generation"]]
        .rename(
            columns={
                "publishTime": "forecastPublishTime",
                "generation": "forecastMw",
            }
        )
    )
    expected = pd.DataFrame(
        {
            "startTime": pd.date_range(
                delivery_start_utc,
                delivery_end_utc,
                freq="1h",
                inclusive="left",
            )
        }
    )
    return expected.merge(selected, on="startTime", how="left", validate="one_to_one")


def aggregate_hourly_actuals(
    actuals: pd.DataFrame,
    *,
    delivery_start_utc: pd.Timestamp,
    delivery_end_utc: pd.Timestamp,
) -> pd.DataFrame:
    """Average two half-hour MW observations; incomplete hours remain missing."""
    _require_columns(actuals, ACTUAL_COLUMNS, "Actual")
    data = _as_utc(actuals, "Actual")
    data = data.loc[data["fuelType"].eq("WIND")]
    data = data.loc[
        (data["startTime"] >= delivery_start_utc)
        & (data["startTime"] < delivery_end_utc)
    ]

    # A later FUELHH publication supersedes an earlier record for the same target.
    data = data.sort_values(["startTime", "publishTime"], kind="stable").drop_duplicates(
        subset=["startTime", "fuelType"], keep="last"
    )
    data["hourStart"] = data["startTime"].dt.floor("h")
    hourly = (
        data.groupby("hourStart", as_index=False)
        .agg(actualMw=("generation", "mean"), actualHalfHourCount=("generation", "count"))
        .rename(columns={"hourStart": "startTime"})
    )
    hourly.loc[hourly["actualHalfHourCount"] != 2, "actualMw"] = pd.NA
    return hourly


def build_decision_analysis(
    forecasts: pd.DataFrame,
    actuals: pd.DataFrame,
    *,
    decision_date: date,
    cutoff: time,
    timezone_name: str = "Europe/London",
) -> dict:
    cutoff_utc, delivery_start, delivery_end = decision_window(
        decision_date, cutoff, timezone_name
    )
    selected = select_latest_forecasts(
        forecasts,
        cutoff_utc=cutoff_utc,
        delivery_start_utc=delivery_start,
        delivery_end_utc=delivery_end,
    )
    actual_hourly = aggregate_hourly_actuals(
        actuals,
        delivery_start_utc=delivery_start,
        delivery_end_utc=delivery_end,
    )
    result = selected.merge(actual_hourly, on="startTime", how="left", validate="one_to_one")
    result["actualHalfHourCount"] = result["actualHalfHourCount"].fillna(0).astype(int)
    result["signedErrorMw"] = result["forecastMw"] - result["actualMw"]

    expected_count = len(result)
    forecast_count = int(result["forecastMw"].notna().sum())
    matched = result.loc[result[["forecastMw", "actualMw"]].notna().all(axis=1)]
    matched_count = len(matched)
    errors = matched["signedErrorMw"]

    warnings: list[str] = []
    if forecast_count < expected_count:
        warnings.append(
            f"{expected_count - forecast_count} delivery hour(s) have no forecast "
            "published by the cutoff; later forecasts were not substituted."
        )
    complete_actual_count = int(result["actualMw"].notna().sum())
    if complete_actual_count < expected_count:
        warnings.append(
            f"{expected_count - complete_actual_count} delivery hour(s) do not have "
            "both half-hour FUELHH observations."
        )

    points = []
    for row in result.itertuples(index=False):
        points.append(
            {
                "startTime": row.startTime.to_pydatetime(),
                "forecastMw": None if pd.isna(row.forecastMw) else float(row.forecastMw),
                "forecastPublishTime": (
                    None
                    if pd.isna(row.forecastPublishTime)
                    else row.forecastPublishTime.to_pydatetime()
                ),
                "actualMw": None if pd.isna(row.actualMw) else float(row.actualMw),
                "actualHalfHourCount": int(row.actualHalfHourCount),
                "signedErrorMw": (
                    None if pd.isna(row.signedErrorMw) else float(row.signedErrorMw)
                ),
            }
        )

    return {
        "decisionDate": decision_date,
        "deliveryDate": decision_date + timedelta(days=1),
        "cutoffLocal": cutoff,
        "timezone": timezone_name,
        "cutoffUtc": cutoff_utc.to_pydatetime(),
        "units": "MW",
        "errorDefinition": "forecast minus actual",
        "retrospective": True,
        "metrics": {
            "expectedPeriods": expected_count,
            "forecastPeriods": forecast_count,
            "matchedPeriods": matched_count,
            "forecastCoverage": forecast_count / expected_count if expected_count else 0.0,
            "matchedCoverage": matched_count / expected_count if expected_count else 0.0,
            "maeMw": float(errors.abs().mean()) if matched_count else None,
            "rmseMw": float(sqrt((errors.pow(2)).mean())) if matched_count else None,
            "biasMw": float(errors.mean()) if matched_count else None,
        },
        "warnings": warnings,
        "points": points,
    }

