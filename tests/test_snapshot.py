"""Offline checks connecting the published inputs, forecasts, and results."""

import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from internet_half_life.catalog import PROJECT_ROOT, load_catalog
from internet_half_life.forecasting import forecast_scores
from internet_half_life.metrics import analyze_event
from internet_half_life.study import (
    MODE_COLUMNS, collect_catalog_study, summarize_catalog_study,
)
from internet_half_life.wikimedia import load_event_frame


def test_published_snapshot_hashes_match():
    manifest = json.loads((PROJECT_ROOT / "data/manifest.json").read_text())
    assert {e["event_slug"] for e in manifest["events"]} == set(load_catalog())
    records = [manifest["catalog"]]
    for event in manifest["events"]:
        records.extend(event[name] for name in ("raw", "metrics", "forecasts"))
    for record in records:
        payload = (PROJECT_ROOT / record["path"]).read_bytes()
        assert len(payload) == record["bytes"]
        assert hashlib.sha256(payload).hexdigest() == record["sha256"]


def test_forecast_truth_and_scores_match_the_published_source_data():
    for event in load_catalog().values():
        raw = load_event_frame(event)
        forecast = pd.read_csv(PROJECT_ROOT / "data/processed" / f"{event.slug}-forecast.csv")
        assert not forecast.duplicated(["mode", "article", "date"]).any()
        assert set(forecast["mode"]) == set(MODE_COLUMNS)
        for (_, article), group in forecast.groupby(["mode", "article"]):
            dates = pd.to_datetime(group["date"])
            expected_dates = pd.date_range(pd.Timestamp(event.date) + pd.Timedelta(days=8), periods=30)
            assert dates.tolist() == expected_dates.tolist()
            np.testing.assert_array_equal(group["actual"].to_numpy(), raw.loc[dates, article].to_numpy())
        assert np.isfinite(forecast_scores(forecast)["wape"]).all()


def test_saved_page_metrics_match_current_definitions():
    for event in load_catalog().values():
        saved = json.loads((PROJECT_ROOT / "data/processed" / f"{event.slug}-metrics.json").read_text())
        recalculated = analyze_event(load_event_frame(event), event)
        for page, expected in zip(recalculated.pages, saved["pages"]):
            assert page.half_life_days == expected["half_life_days"]
            assert page.half_life_status == expected["half_life_status"]
            assert page.peak_date == expected["peak_date"]
            assert page.excess_views_60d == expected["excess_views_60d"]


def test_catalog_results_can_be_rebuilt_without_network_or_model_weights():
    rebuilt = collect_catalog_study()
    published = pd.read_csv(PROJECT_ROOT / "results/catalog-study.csv")
    pd.testing.assert_frame_equal(rebuilt, published, check_dtype=False, atol=5.1e-7, rtol=1e-10)
    summary = summarize_catalog_study(rebuilt)
    expected = json.loads((PROJECT_ROOT / "results/study-summary.json").read_text())
    assert summary["peak_timing_14d"] == expected["peak_timing_14d"]
    assert summary["constellation_decay"] == expected["constellation_decay"]
    for mode, score in summary["median_event_wape"].items():
        assert score == pytest.approx(expected["median_event_wape"][mode])
