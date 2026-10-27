from datetime import date, datetime, time

from pydantic import BaseModel, Field


class DecisionPoint(BaseModel):
    start_time: datetime = Field(alias="startTime")
    forecast_mw: float | None = Field(alias="forecastMw")
    forecast_publish_time: datetime | None = Field(alias="forecastPublishTime")
    actual_mw: float | None = Field(alias="actualMw")
    actual_half_hour_count: int = Field(alias="actualHalfHourCount")
    signed_error_mw: float | None = Field(alias="signedErrorMw")

    model_config = {"populate_by_name": True}


class DecisionMetrics(BaseModel):
    expected_periods: int = Field(alias="expectedPeriods")
    forecast_periods: int = Field(alias="forecastPeriods")
    matched_periods: int = Field(alias="matchedPeriods")
    forecast_coverage: float = Field(alias="forecastCoverage")
    matched_coverage: float = Field(alias="matchedCoverage")
    mae_mw: float | None = Field(alias="maeMw")
    rmse_mw: float | None = Field(alias="rmseMw")
    bias_mw: float | None = Field(alias="biasMw")

    model_config = {"populate_by_name": True}


class DecisionResponse(BaseModel):
    decision_date: date = Field(alias="decisionDate")
    delivery_date: date = Field(alias="deliveryDate")
    cutoff_local: time = Field(alias="cutoffLocal")
    timezone: str
    cutoff_utc: datetime = Field(alias="cutoffUtc")
    units: str = "MW"
    error_definition: str = Field(
        default="forecast minus actual", alias="errorDefinition"
    )
    retrospective: bool = True
    metrics: DecisionMetrics
    warnings: list[str]
    points: list[DecisionPoint]

    model_config = {"populate_by_name": True}

