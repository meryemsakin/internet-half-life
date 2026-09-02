import datetime as dt

from internet_half_life.catalog import load_catalog

TRAINING_CUTOFF = dt.date(2023, 12, 1)


def test_catalog_has_unique_valid_events():
    events = load_catalog()
    assert "straight-outta-compton" in events
    assert "barbenheimer" in events
    # a floor, not an exact count: adding an event is supposed to be one entry
    # in catalog/events.json, and that should not break the suite
    assert len(events) >= 10
    assert len(set(events)) == len(events)
    for event in events.values():
        assert len(event.pages) >= 4
        assert event.primary in event.articles


def test_catalog_spans_the_training_cutoff():
    """Both sides of TimesFM's November 2023 pageview cutoff must stay populated.

    The contamination check in study.py compares events the model may have been
    trained on against events outside the stated Pageviews window. If the catalog ever drifts to
    one side of that date the comparison silently stops meaning anything, so it
    is asserted here rather than discovered in a result table.
    """
    dates = [e.date for e in load_catalog().values()]
    before = sum(d < TRAINING_CUTOFF for d in dates)
    after = len(dates) - before
    assert before >= 5, f"only {before} pre-cutoff events"
    assert after >= 5, f"only {after} post-cutoff events"
