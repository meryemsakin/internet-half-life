from datetime import date

import numpy as np
import pandas as pd

from internet_half_life.catalog import Event, Page
from internet_half_life.visualize import render_forecast


def test_forecast_renderer_accepts_all_six_modes(tmp_path):
    event = Event(
        slug="test", title="Test", date=date(2024, 2, 1), description="",
        primary="main", pages=(Page(article="main", label="Main", role="event"),),
    )
    frame = pd.DataFrame({"main": np.ones(70)}, index=pd.date_range("2024-01-01", periods=70))
    rows = []
    for mode in ("timesfm-multivariate", "timesfm-univariate", "exponential-decay",
                 "power-law-decay", "flat-baseline", "seasonal-naive"):
        for timestamp in pd.date_range("2024-02-09", periods=3):
            rows.append({"article": "main", "date": timestamp, "mode": mode,
                         "actual": 1, "forecast": 1, "q10": .5, "q90": 2})
    path = render_forecast(frame, pd.DataFrame(rows), event, output_dir=tmp_path)
    assert path.stat().st_size > 1000
