from datetime import date

import numpy as np
import pandas as pd

from internet_half_life.catalog import Event, Page

from internet_half_life.study import (
    _two_sample_permutation,
    exact_sign_flip_test,
    exact_sign_test,
    peak_offset_table,
    summarize_peak_timing,
)


def test_exact_sign_test_is_two_sided():
    assert exact_sign_test(5, 0) == 0.0625
    assert exact_sign_test(3, 2) == 1.0
    assert exact_sign_test(0, 0) == 1.0
    assert exact_sign_test(2, 4) == .6875


def test_peak_test_weights_events_equally_not_their_page_counts():
    frame = pd.DataFrame({
        "median_related_peak_offset_14d": [2, -1, 0],
        "related_peaks_after_primary_14d": [20, 0, 0],
        "related_peaks_before_primary_14d": [0, 3, 0],
        "related_peaks_with_primary_14d": [0, 0, 5],
    })
    summary = summarize_peak_timing(frame)
    assert summary["after"] == 20
    assert summary["event_medians"] == {
        "events": 3, "after": 1, "before": 1, "same_day": 1,
        "exact_sign_test_p_value": 1.0,
    }


def test_exact_sign_flip_test_finds_a_consistent_direction():
    assert exact_sign_flip_test(np.array([-1.0, -2.0, -3.0])) == 0.25
    assert exact_sign_flip_test(np.array([])) == 1.0


def test_two_sample_permutation_enumerates_every_partition():
    result = _two_sample_permutation(
        np.array([0.0, 1.0]),
        np.array([10.0, 11.0]),
    )
    assert np.isclose(result, 1 / 3)


def test_peak_offset_table_is_relative_to_the_primary_peak():
    event = Event(
        slug="sample",
        title="Sample",
        date=date(2024, 1, 1),
        description="",
        primary="main",
        pages=(
            Page(article="main", label="Main", role="event"),
            Page(article="later", label="Later", role="idea"),
        ),
    )
    index = pd.date_range("2024-01-01", periods=5, freq="D")
    frame = pd.DataFrame(
        {"main": [1, 8, 2, 1, 1], "later": [1, 2, 9, 1, 1]},
        index=index,
    )
    result = peak_offset_table(frame, event, post_days=5).iloc[0]
    assert result["primary_peak_offset_days"] == 1
    assert result["related_peak_offset_days"] == 2
    assert result["relative_peak_offset_days"] == 1
