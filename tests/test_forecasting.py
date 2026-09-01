from datetime import date

import numpy as np
import pandas as pd

from internet_half_life.forecasting import forecast_scores, seasonal_naive


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
