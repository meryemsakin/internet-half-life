"""Curated cultural events and the Wikipedia pages around them."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = PROJECT_ROOT / "catalog" / "events.json"


@dataclass(frozen=True)
class Page:
    article: str
    label: str
    role: str


@dataclass(frozen=True)
class Event:
    slug: str
    title: str
    date: date
    description: str
    primary: str
    pages: tuple[Page, ...]

    @property
    def articles(self) -> list[str]:
        return [page.article for page in self.pages]

    def page(self, article: str) -> Page:
        return next(page for page in self.pages if page.article == article)


def load_catalog(path: str | Path = DEFAULT_CATALOG) -> dict[str, Event]:
    """Load and validate the event catalog."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    events: dict[str, Event] = {}

    for raw in payload["events"]:
        pages = tuple(Page(**page) for page in raw["pages"])
        event = Event(
            slug=raw["slug"],
            title=raw["title"],
            date=date.fromisoformat(raw["date"]),
            description=raw["description"],
            primary=raw["primary"],
            pages=pages,
        )
        if event.slug in events:
            raise ValueError(f"duplicate event slug: {event.slug}")
        if len(set(event.articles)) != len(event.articles):
            raise ValueError(f"duplicate page in {event.slug}")
        if event.primary not in event.articles:
            raise ValueError(f"primary page missing from {event.slug}: {event.primary}")
        events[event.slug] = event

    return events


def get_event(slug: str, path: str | Path = DEFAULT_CATALOG) -> Event:
    events = load_catalog(path)
    try:
        return events[slug]
    except KeyError as error:
        choices = ", ".join(events)
        raise KeyError(f"unknown event {slug!r}; choose one of: {choices}") from error

