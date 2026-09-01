"""Small, cached client for Wikimedia's public Pageviews API."""

from __future__ import annotations

from datetime import date, timedelta
import hashlib
import json
import os
from pathlib import Path
import time
from urllib.parse import quote

import pandas as pd
import requests

from .catalog import Event, PROJECT_ROOT


API = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
API_DATA_START = date(2015, 7, 1)
DEFAULT_CACHE = PROJECT_ROOT / "data" / "cache"
DEFAULT_RAW = PROJECT_ROOT / "data" / "raw"
DEFAULT_SAMPLE = PROJECT_ROOT / "data" / "sample"


class WikimediaClient:
    def __init__(
        self,
        cache_dir: str | Path = DEFAULT_CACHE,
        user_agent: str | None = None,
        pace_seconds: float = 0.25,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.user_agent = user_agent or os.environ.get(
            "ATTENTION_AFTERLIFE_USER_AGENT",
            "internet-half-life/0.2 (educational research; contact via repository issues)",
        )
        self.pace_seconds = pace_seconds
        self.session = requests.Session()

    def daily_views(
        self,
        article: str,
        start: date,
        end: date,
        project: str = "en.wikipedia.org",
    ) -> pd.Series:
        """Return a complete daily series, filling absent dates with zero."""
        encoded = quote(article.replace(" ", "_"), safe="")
        start_text = start.strftime("%Y%m%d")
        end_text = end.strftime("%Y%m%d")
        url = (
            f"{API}/{project}/all-access/user/{encoded}/daily/"
            f"{start_text}/{end_text}"
        )
        payload = self._get_json(url)
        values = {
            pd.Timestamp(item["timestamp"][:8]): int(item["views"])
            for item in payload.get("items", [])
        }
        index = pd.date_range(start, end, freq="D")
        return pd.Series(values, index=index, dtype="float64").fillna(0).rename(article)

    def _get_json(self, url: str, retries: int = 7) -> dict:
        key = hashlib.sha256(url.encode("utf-8")).hexdigest()
        cache_path = self.cache_dir / f"{key}.json"
        if cache_path.exists():
            return json.loads(cache_path.read_text(encoding="utf-8"))

        response: requests.Response | None = None
        for attempt in range(retries):
            time.sleep(self.pace_seconds)
            response = self.session.get(
                url,
                headers={"User-Agent": self.user_agent, "Accept": "application/json"},
                timeout=45,
            )
            if response.status_code == 200:
                payload = response.json()
                cache_path.write_text(json.dumps(payload), encoding="utf-8")
                return payload
            if response.status_code == 404:
                return {"items": []}
            if response.status_code not in {429, 500, 502, 503, 504}:
                response.raise_for_status()
            retry_after = response.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else min(2**attempt, 30)
            time.sleep(delay)

        assert response is not None
        response.raise_for_status()
        raise RuntimeError("unreachable")


def fetch_event(
    event: Event,
    before: int = 512,
    after: int = 90,
    client: WikimediaClient | None = None,
    output_dir: str | Path = DEFAULT_RAW,
) -> pd.DataFrame:
    """Fetch all pages in one event universe and save a wide CSV."""
    client = client or WikimediaClient()
    start = max(event.date - timedelta(days=before), API_DATA_START)
    end = event.date + timedelta(days=after)
    columns = [client.daily_views(article, start, end) for article in event.articles]
    frame = pd.concat(columns, axis=1)
    frame.index.name = "date"

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_dir / f"{event.slug}.csv", date_format="%Y-%m-%d")
    return frame


def load_event_frame(
    event: Event,
    input_dir: str | Path = DEFAULT_RAW,
) -> pd.DataFrame:
    path = Path(input_dir) / f"{event.slug}.csv"
    if not path.exists():
        sample_path = DEFAULT_SAMPLE / f"{event.slug}.csv"
        if sample_path.exists():
            path = sample_path
        else:
            raise FileNotFoundError(
                f"missing {path}; run `internet-half-life fetch --event {event.slug}` first"
            )
    frame = pd.read_csv(path, index_col="date", parse_dates=True)
    missing = set(event.articles) - set(frame.columns)
    if missing:
        raise ValueError(f"{path} is missing catalog pages: {sorted(missing)}")
    frame = frame[event.articles].sort_index()
    available = frame.ne(0).any(axis=1)
    if not available.any():
        raise ValueError(f"{path} contains no pageview observations")
    # The API has no daily observations before July 2015. Older requests used
    # to be padded with zeros, which must not be passed to forecasting models
    # as if they were real traffic.
    return frame.loc[available.idxmax() :]
