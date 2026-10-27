from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def load_sample_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    forecast_path = RAW_DATA_DIR / "windfor_decision_2026-01-05.json"
    actual_path = RAW_DATA_DIR / "fuelhh_delivery_2026-01-06.json"
    missing = [str(path) for path in (forecast_path, actual_path) if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Required data snapshot is missing. Run `python scripts/fetch_elexon.py`. "
            f"Missing: {', '.join(missing)}"
        )
    return (
        pd.DataFrame(json.loads(forecast_path.read_text(encoding="utf-8"))),
        pd.DataFrame(json.loads(actual_path.read_text(encoding="utf-8"))),
    )

