from datetime import date

import numpy as np
import pandas as pd

from internet_half_life.catalog import Event, Page
from internet_half_life.metrics import analyze_event, calculate_page_metrics


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
