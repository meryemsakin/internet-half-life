from internet_half_life.catalog import load_catalog


def test_catalog_has_unique_valid_events():
    events = load_catalog()
    assert "straight-outta-compton" in events
    assert "barbenheimer" in events
    assert len(events) == 10
    for event in events.values():
        assert len(event.pages) >= 5
        assert event.primary in event.articles
