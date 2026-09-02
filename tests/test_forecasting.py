from datetime import date

import numpy as np
import pandas as pd

from internet_half_life.catalog import Event, Page
from internet_half_life.forecasting import (
    flat_baseline,
    forecast_scores,
    parametric_decay,
    seasonal_naive,
)


def test_flat_baseline_returns_each_pre_event_median():
    event = sample_forecast_event()
    index = pd.date_range("2024-01-01", "2024-02-08", freq="D")
    frame = pd.DataFrame({"Test": np.arange(1, len(index) + 1)}, index=index)
    result = flat_baseline(frame, event, horizon=3, baseline_days=28)
    np.testing.assert_array_equal(result, [[17.5, 17.5, 17.5]])


def sample_forecast_event() -> Event:
    return Event(
        slug="test",
        title="Test",
        date=date(2024, 2, 1),
        description="",
        primary="Test",
        pages=(Page(article="Test", label="Test", role="event"),),
    )


def test_seasonal_naive_repeats_the_last_week_for_every_variate():
    frame = pd.DataFrame(
        {
            "one": np.arange(14),
            "two": np.arange(100, 114),
        }
    )
    result = seasonal_naive(frame, horizon=10, period=7)
    assert result.shape == (2, 10)
    np.testing.assert_array_equal(result[0], [7, 8, 9, 10, 11, 12, 13, 7, 8, 9])
    np.testing.assert_array_equal(result[1], [107, 108, 109, 110, 111, 112, 113, 107, 108, 109])


def test_forecast_scores_are_aggregated_by_mode():
    frame = pd.DataFrame(
        {
            "mode": ["good", "good", "bad", "bad"],
            "actual": [10, 20, 10, 20],
            "forecast": [11, 19, 20, 40],
            "q10": [9, 18, 20, 40],
            "q90": [12, 22, 20, 40],
        }
    )
    scores = forecast_scores(frame).set_index("mode")
    assert np.isclose(scores.loc["good", "wape"], 2 / 30)
    assert scores.loc["good", "interval_coverage"] == 1
    assert scores.loc["bad", "interval_coverage"] == 0
    assert np.isclose(scores.loc["good", "mean_interval_width"], 3.5)
    assert np.isclose(scores.loc["good", "median_page_wape"], 2 / 30)


def test_forecast_scores_leave_missing_intervals_unscored():
    frame = pd.DataFrame(
        {
            "mode": ["point-only", "point-only"],
            "actual": [10, 20],
            "forecast": [11, 19],
            "q10": [np.nan, np.nan],
            "q90": [np.nan, np.nan],
        }
    )
    score = forecast_scores(frame).iloc[0]
    assert np.isnan(score["interval_coverage"])
    assert np.isnan(score["relative_interval_width"])
    assert score["interval_observations"] == 0


def test_parametric_decay_follows_a_revealed_exponential_spike():
    event = sample_forecast_event()
    index = pd.date_range("2024-01-04", periods=36, freq="D")
    values = np.full(len(index), 100.0)
    values[-8:] = 100 + 900 * np.exp(-0.25 * np.arange(8))
    frame = pd.DataFrame({"Test": values}, index=index)

    forecast = parametric_decay(frame, event, horizon=5, kind="exponential")

    expected = 100 + 900 * np.exp(-0.25 * np.arange(8, 13))
    np.testing.assert_allclose(forecast[0], expected)
    assert np.all(np.diff(forecast[0]) < 0)
