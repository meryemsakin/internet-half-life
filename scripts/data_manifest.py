"""Build or verify a deterministic manifest of the published research snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from internet_half_life.catalog import PROJECT_ROOT, load_catalog


def file_record(path: Path) -> dict:
    return {
        "path": path.relative_to(PROJECT_ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def build_manifest() -> dict:
    events = []
    for event in load_catalog().values():
        raw_path = PROJECT_ROOT / "data" / "raw" / f"{event.slug}.csv"
        forecast_path = PROJECT_ROOT / "data" / "processed" / f"{event.slug}-forecast.csv"
        metrics_path = PROJECT_ROOT / "data" / "processed" / f"{event.slug}-metrics.json"
        raw = pd.read_csv(raw_path)
        forecast = pd.read_csv(forecast_path)
        events.append({
            "event_slug": event.slug,
            "event_date": event.date.isoformat(),
            "pages": event.articles,
            "raw": {
                **file_record(raw_path),
                "rows": len(raw),
                "stored_start": raw["date"].min(),
                "stored_end": raw["date"].max(),
            },
            "metrics": file_record(metrics_path),
            "forecasts": {
                **file_record(forecast_path),
                "rows": len(forecast),
                "start": forecast["date"].min(),
                "end": forecast["date"].max(),
                "modes": sorted(forecast["mode"].unique().tolist()),
            },
        })
    return {
        "schema_version": 1,
        "catalog": file_record(PROJECT_ROOT / "catalog" / "events.json"),
        "source": {
            "provider": "Wikimedia Pageviews API",
            "endpoint": "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article",
            "project": "en.wikipedia.org", "access": "all-access",
            "agent": "user", "granularity": "daily",
        },
        "analysis_settings": {
            "baseline_days": 28, "baseline_floor": 1,
            "peak_window_days": 14, "post_event_days": 60,
            "half_life_sustained_days": 3, "late_window_offsets": [53, 59],
        },
        "forecast_settings": {
            "checkpoint": "google/timesfm-3.0-pytorch",
            "revealed_event_day_offsets": [0, 7],
            "forecast_event_day_offsets": [8, 37],
            "maximum_context_days": 512,
            "use_symmetric_averaging": False,
        },
        "provenance_limitations": [
            "Original fetch timestamps and HTTP response provenance were not recorded.",
            "Original forecast package/device details and immutable checkpoint revision were not recorded.",
            "Hashes identify the published files, not a promise of bit-identical model reruns.",
            "Legacy all-zero padding before API availability remains in the Straight Outta Compton raw file; the loader excludes it.",
        ],
        "events": events,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify without writing")
    args = parser.parse_args()
    path = PROJECT_ROOT / "data" / "manifest.json"
    manifest = build_manifest()
    if args.check:
        existing = json.loads(path.read_text(encoding="utf-8"))
        if manifest != existing:
            raise SystemExit("Snapshot differs from data/manifest.json; review and rebuild the manifest.")
        print(f"Verified {len(manifest['events'])} event snapshots.")
    else:
        path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print("Wrote data/manifest.json")


if __name__ == "__main__":
    main()
