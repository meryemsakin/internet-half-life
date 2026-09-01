from datetime import date

import pandas as pd

from internet_half_life.catalog import Event, Page
from internet_half_life.wikimedia import load_event_frame


def test_load_event_frame_trims_leading_missing_api_days(tmp_path):
    event = Event(
        slug="api-boundary",
        title="API boundary",
        date=date(2015, 8, 1),
        description="",
        primary="main",
        pages=(Page(article="main", label="Main", role="event"),),
    )
    frame = pd.DataFrame(
        {"main": [0.0, 0.0, 12.0, 0.0]},
        index=pd.date_range("2015-06-29", periods=4, freq="D", name="date"),
    )
    frame.to_csv(tmp_path / "api-boundary.csv")

    loaded = load_event_frame(event, input_dir=tmp_path)

    assert loaded.index.min() == pd.Timestamp("2015-07-01")
    assert len(loaded) == 2
