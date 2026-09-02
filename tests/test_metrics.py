from datetime import date

import numpy as np
import pandas as pd
import pytest

from internet_half_life.catalog import Event, Page
from internet_half_life.metrics import (
    analyze_event,
    calculate_constellation_decay,
    calculate_page_metrics,
)


def sample_event() -> Event:
    return Event(
        slug="sample",
        title="Sample event",
        date=date(2024, 2, 1),
        description="A deterministic test fixture.",
        primary="main",
        pages=(
            Page(article="main", label="Main", role="event"),
            Page(article="related", label="Related", role="idea"),
        ),
    )


def sample_frame() -> pd.DataFrame:
    index = pd.date_range("2023-12-01", "2024-04-30", freq="D")
    main = np.full(len(index), 100.0)
    related = np.full(len(index), 50.0)
    event_index = index.get_loc(pd.Timestamp("2024-02-01"))
    main[event_index : event_index + 6] = [1000, 700, 480, 300, 180, 120]
    related[event_index + 1 : event_index + 7] = [400, 320, 230, 150, 90, 55]
    return pd.DataFrame({"main": main, "related": related}, index=index)


def test_page_metrics_find_peak_and_sustained_half_life():
    metrics = calculate_page_metrics(sample_frame(), sample_event(), "main")
    assert metrics.baseline_views == 100
    assert metrics.peak_offset_days == 0
    assert metrics.peak_lift == 10
    assert metrics.half_life_days == 2
    assert metrics.excess_views_60d == 2180
    assert metrics.half_life_status == "observed"


def test_late_rebound_does_not_redefine_the_initial_peak():
    frame = sample_frame()
    frame.loc["2024-03-27", "main"] = 5000
    metrics = calculate_page_metrics(frame, sample_event(), "main")
    assert metrics.peak_offset_days == 0
    assert metrics.peak_views == 1000
    assert metrics.half_life_days == 2


def test_no_excess_is_not_a_zero_day_half_life():
    frame = sample_frame()
    frame["main"] = 100
    metrics = calculate_page_metrics(frame, sample_event(), "main")
    assert metrics.half_life_days is None
    assert metrics.half_life_status == "no_excess"


def test_no_crossing_is_reported_separately_from_no_excess():
    frame = sample_frame()
    frame.loc["2024-02-01":, "main"] = 1000
    metrics = calculate_page_metrics(frame, sample_event(), "main")
    assert metrics.half_life_days is None
    assert metrics.half_life_status == "not_observed"


def test_constellation_sums_page_excess_and_reports_late_retention():
    frame = sample_frame()
    frame.loc["2024-03-25":"2024-03-31", "main"] = 290
    decay = calculate_constellation_decay(frame, sample_event())
    assert decay.peak_offset_days == 1
    assert decay.peak_excess_views == 950
    assert decay.half_life_days == 2
    assert decay.last_week_mean_excess_views == 190
    assert decay.last_week_retained_peak_share == .2
    assert decay.observation_days_after_peak == 58


def test_constellation_clips_before_summing_and_does_not_cancel_attention():
    frame = sample_frame()
    frame.loc["2024-02-01":, "related"] = 0
    decay = calculate_constellation_decay(frame, sample_event())
    assert decay.peak_excess_views == 900


def test_missing_post_event_days_are_rejected():
    frame = sample_frame().drop(pd.Timestamp("2024-02-10"))
    with pytest.raises(ValueError, match="complete post-event days"):
        calculate_constellation_decay(frame, sample_event())


def test_peak_window_cannot_extend_beyond_the_observation_window():
    with pytest.raises(ValueError, match="peak_window_days"):
        calculate_page_metrics(sample_frame(), sample_event(), "main", peak_window_days=61)


def test_constellation_with_no_spike_has_no_defined_retention_ratio():
    frame = sample_frame()
    frame["main"], frame["related"] = 100, 50
    decay = calculate_constellation_decay(frame, sample_event())
    assert decay.half_life_status == "no_excess"
    assert decay.half_life_days is None
    assert decay.last_week_retained_peak_share is None


def test_page_metrics_accept_a_higher_baseline_floor():
    frame = sample_frame()
    frame.loc[:"2024-01-31", "related"] = 0
    metrics = calculate_page_metrics(
        frame,
        sample_event(),
        "related",
        baseline_floor=10,
    )
    assert metrics.baseline_views == 10


def test_event_metrics_measure_spillover_and_lagged_edges():
    metrics = analyze_event(sample_frame(), sample_event())
    assert metrics.total_excess_views_60d > metrics.page("main").excess_views_60d
    assert 0 < metrics.spillover_share < 1
    assert metrics.edges
    assert metrics.edges[0].source == "main"
    assert metrics.edges[0].target == "related"
    assert metrics.edges[0].lag_days == 1
