from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def fetch_json(path: str, params: dict[str, str]) -> tuple[bytes, str, int]:
    url = f"{BASE_URL}{path}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "reint-wind-challenge/0.1"})
    with urlopen(request, timeout=60) as response:
        payload = response.read()
    parsed = json.loads(payload)
    if not isinstance(parsed, list):
        raise RuntimeError(f"Expected a JSON array from {url}")
    return payload, url, len(parsed)


def write_snapshot(
    output_dir: Path,
    filename: str,
    payload: bytes,
    *,
    url: str,
    record_count: int,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    path.write_bytes(payload)
    return {
        "path": path.relative_to(PROJECT_ROOT).as_posix(),
        "sourceUrl": url,
        "recordCount": record_count,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch the Elexon 5 January decision sample")
    parser.add_argument("--decision-date", type=date.fromisoformat, default=date(2026, 1, 5))
    parser.add_argument("--cutoff", type=time.fromisoformat, default=time(9, 20))
    parser.add_argument("--timezone", default="Europe/London")
    parser.add_argument("--forecast-lookback-days", type=int, default=7)
    parser.add_argument(
        "--forecast-observation-minutes-after-cutoff",
        type=int,
        default=60,
        help="Also preserve later publications so the cutoff exclusion is auditable.",
    )
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "data" / "raw")
    args = parser.parse_args()

    local_timezone = ZoneInfo(args.timezone)
    cutoff_local = datetime.combine(args.decision_date, args.cutoff, tzinfo=local_timezone)
    cutoff_utc = cutoff_local.astimezone(timezone.utc)
    forecast_from = cutoff_utc - timedelta(days=args.forecast_lookback_days)
    forecast_to = cutoff_utc + timedelta(
        minutes=args.forecast_observation_minutes_after_cutoff
    )
    delivery_date = args.decision_date + timedelta(days=1)

    forecast_payload, forecast_url, forecast_count = fetch_json(
        "/datasets/WINDFOR/stream",
        {
            "publishDateTimeFrom": iso_z(forecast_from),
            "publishDateTimeTo": iso_z(forecast_to),
        },
    )
    actual_payload, actual_url, actual_count = fetch_json(
        "/datasets/FUELHH/stream",
        {
            "settlementDateFrom": delivery_date.isoformat(),
            "settlementDateTo": delivery_date.isoformat(),
            "fuelType": "WIND",
        },
    )

    files = [
        write_snapshot(
            args.output_dir,
            f"windfor_decision_{args.decision_date.isoformat()}.json",
            forecast_payload,
            url=forecast_url,
            record_count=forecast_count,
        ),
        write_snapshot(
            args.output_dir,
            f"fuelhh_delivery_{delivery_date.isoformat()}.json",
            actual_payload,
            url=actual_url,
            record_count=actual_count,
        ),
    ]
    manifest = {
        "schemaVersion": 1,
        "retrievedAt": iso_z(datetime.now(timezone.utc)),
        "decisionDate": args.decision_date.isoformat(),
        "deliveryDate": delivery_date.isoformat(),
        "cutoffLocal": args.cutoff.isoformat(timespec="minutes"),
        "timezone": args.timezone,
        "cutoffUtc": iso_z(cutoff_utc),
        "forecastLookbackDays": args.forecast_lookback_days,
        "forecastObservationMinutesAfterCutoff": (
            args.forecast_observation_minutes_after_cutoff
        ),
        "files": files,
    }
    manifest_path = args.output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

