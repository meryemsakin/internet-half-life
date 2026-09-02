"""Metrics for the rise, spread, and decay of an attention event."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .catalog import Event, PROJECT_ROOT


DEFAULT_PROCESSED = PROJECT_ROOT / "data" / "processed"
PEAK_WINDOW_DAYS = 14


@dataclass(frozen=True)
class PageMetrics:
    article: str
    label: str
    role: str
    baseline_views: float
    peak_date: str
    peak_offset_days: int
    peak_views: int
    peak_lift: float
    half_life_days: int | None
    excess_views_60d: int
    first_week_share: float
    half_life_status: str


@dataclass(frozen=True)
class ConstellationDecay:
    peak_window_days: int
    peak_date: str
    peak_offset_days: int
    peak_excess_views: float
    half_life_days: int | None
    half_life_status: str
    observation_days_after_peak: int
    last_week_mean_excess_views: float
    last_week_retained_peak_share: float | None


@dataclass(frozen=True)
class AttentionEdge:
    source: str
    target: str
    lag_days: int
    correlation: float


@dataclass(frozen=True)
class EventMetrics:
    slug: str
    title: str
    event_date: str
    primary: str
    total_excess_views_60d: int
    spillover_share: float
    pages: tuple[PageMetrics, ...]
    edges: tuple[AttentionEdge, ...]

    def page(self, article: str) -> PageMetrics:
        return next(page for page in self.pages if page.article == article)


def _baseline(
    series: pd.Series,
    event_day: pd.Timestamp,
    days: int,
    floor: float = 1.0,
) -> float:
    pre = series.loc[event_day - pd.Timedelta(days=days) : event_day - pd.Timedelta(days=1)]
    if pre.empty:
        raise ValueError("not enough pre-event data to calculate a baseline")
    return max(float(pre.median()), floor)


def _sustained_half_life(
    post: pd.Series,
    baseline: float,
    peak_date: pd.Timestamp,
    sustained_days: int,
) -> int | None:
    if sustained_days < 1:
        raise ValueError("sustained_days must be positive")
    peak_excess = max(float(post.loc[peak_date]) - baseline, 0.0)
    if peak_excess <= 0:
        return None
    threshold = peak_excess / 2
    after_peak = post.loc[peak_date + pd.Timedelta(days=1) :]
    excess = (after_peak - baseline).clip(lower=0)
    for index in range(0, len(excess) - sustained_days + 1):
        window = excess.iloc[index : index + sustained_days]
        if bool((window <= threshold).all()):
            return int((window.index[0] - peak_date).days)
    return None


def _half_life_status(peak_excess: float, half_life: int | None) -> str:
    if peak_excess <= 0:
        return "no_excess"
    return "observed" if half_life is not None else "not_observed"


def _post_event_window(
    frame: pd.DataFrame, event: Event, post_days: int, peak_window_days: int
) -> pd.DataFrame:
    if not 1 <= peak_window_days <= post_days:
        raise ValueError("peak_window_days must be between 1 and post_days")
    dates = pd.date_range(event.date, periods=post_days, freq="D")
    post = frame.reindex(dates)[event.articles].astype(float)
    if not np.isfinite(post.to_numpy()).all():
        raise ValueError(f"{event.slug} needs {post_days} complete post-event days")
    return post


def calculate_page_metrics(
    frame: pd.DataFrame,
    event: Event,
    article: str,
    baseline_days: int = 28,
    post_days: int = 60,
    sustained_days: int = 3,
    baseline_floor: float = 1.0,
    peak_window_days: int = PEAK_WINDOW_DAYS,
) -> PageMetrics:
    event_day = pd.Timestamp(event.date)
    series = frame[article].astype(float)
    baseline = _baseline(series, event_day, baseline_days, floor=baseline_floor)
    post = _post_event_window(frame, event, post_days, peak_window_days)[article]
    peak_date = post.iloc[:peak_window_days].idxmax()
    peak_views = int(post.loc[peak_date])
    excess = (post - baseline).clip(lower=0)
    total_excess = float(excess.sum())
    first_week = float(excess.iloc[:7].sum())
    page = event.page(article)
    half_life = _sustained_half_life(post, baseline, peak_date, sustained_days)

    return PageMetrics(
        article=article,
        label=page.label,
        role=page.role,
        baseline_views=baseline,
        peak_date=peak_date.date().isoformat(),
        peak_offset_days=int((peak_date - event_day).days),
        peak_views=peak_views,
        peak_lift=peak_views / baseline,
        half_life_days=half_life,
        excess_views_60d=int(round(total_excess)),
        first_week_share=(first_week / total_excess) if total_excess else 0.0,
        half_life_status=_half_life_status(peak_views - baseline, half_life),
    )


def calculate_constellation_decay(
    frame: pd.DataFrame,
    event: Event,
    baseline_days: int = 28,
    post_days: int = 60,
    peak_window_days: int = PEAK_WINDOW_DAYS,
    sustained_days: int = 3,
    baseline_floor: float = 1.0,
) -> ConstellationDecay:
    """Measure the initial fade and late attention, not permanent forgetting.

    Sum nonnegative page-level excess first, then locate its peak in days
    0..13. The first sustained threshold crossing does not prevent a rebound.
    The last-week mean uses days 53..59, relative to that same initial peak.
    """
    if post_days < 7:
        raise ValueError("post_days must include at least seven days")
    event_day = pd.Timestamp(event.date)
    post = _post_event_window(frame, event, post_days, peak_window_days)
    baselines = pd.Series({
        article: _baseline(frame[article], event_day, baseline_days, baseline_floor)
        for article in event.articles
    })
    excess = (post - baselines).clip(lower=0).sum(axis=1)
    peak_date = excess.iloc[:peak_window_days].idxmax()
    peak_excess = float(excess.loc[peak_date])
    half_life = _sustained_half_life(excess, 0.0, peak_date, sustained_days)
    last_week = float(excess.iloc[-7:].mean())
    return ConstellationDecay(
        peak_window_days=peak_window_days,
        peak_date=peak_date.date().isoformat(),
        peak_offset_days=int((peak_date - event_day).days),
        peak_excess_views=peak_excess,
        half_life_days=half_life,
        half_life_status=_half_life_status(peak_excess, half_life),
        observation_days_after_peak=int((excess.index[-1] - peak_date).days),
        last_week_mean_excess_views=last_week,
        last_week_retained_peak_share=last_week / peak_excess if peak_excess else None,
    )


def _best_lag(
    left: np.ndarray,
    right: np.ndarray,
    max_lag: int,
) -> tuple[int, float]:
    """Return lag where positive means `left` leads `right`."""
    best_lag, best_correlation = 0, -np.inf
    for lag in range(-max_lag, max_lag + 1):
        if lag > 0:
            a, b = left[:-lag], right[lag:]
        elif lag < 0:
            a, b = left[-lag:], right[:lag]
        else:
            a, b = left, right
        if len(a) < 10 or np.std(a) == 0 or np.std(b) == 0:
            continue
        correlation = float(np.corrcoef(a, b)[0, 1])
        if np.isfinite(correlation) and correlation > best_correlation:
            best_lag, best_correlation = lag, correlation
    return best_lag, best_correlation


def calculate_edges(
    frame: pd.DataFrame,
    event: Event,
    page_metrics: list[PageMetrics],
    max_lag: int = 5,
    minimum_correlation: float = 0.35,
) -> list[AttentionEdge]:
    """Estimate lead/lag co-movement; edges are descriptive, not causal."""
    event_day = pd.Timestamp(event.date)
    window = frame.loc[
        event_day - pd.Timedelta(days=7) : event_day + pd.Timedelta(days=45)
    ]
    baselines = {metric.article: metric.baseline_views for metric in page_metrics}
    transformed = {
        article: np.log1p(window[article].to_numpy(dtype=float) / baselines[article])
        for article in event.articles
    }

    edges: list[AttentionEdge] = []
    for left_index, left_article in enumerate(event.articles):
        for right_article in event.articles[left_index + 1 :]:
            lag, correlation = _best_lag(
                transformed[left_article], transformed[right_article], max_lag
            )
            if correlation < minimum_correlation:
                continue
            if lag < 0:
                source, target, lag = right_article, left_article, abs(lag)
            else:
                source, target = left_article, right_article
            edges.append(
                AttentionEdge(
                    source=source,
                    target=target,
                    lag_days=lag,
                    correlation=correlation,
                )
            )

    return sorted(edges, key=lambda edge: edge.correlation, reverse=True)


def analyze_event(
    frame: pd.DataFrame,
    event: Event,
    baseline_days: int = 28,
    post_days: int = 60,
    baseline_floor: float = 1.0,
    peak_window_days: int = PEAK_WINDOW_DAYS,
) -> EventMetrics:
    pages = [
        calculate_page_metrics(
            frame,
            event,
            article,
            baseline_days=baseline_days,
            post_days=post_days,
            baseline_floor=baseline_floor,
            peak_window_days=peak_window_days,
        )
        for article in event.articles
    ]
    total_excess = sum(page.excess_views_60d for page in pages)
    primary_excess = next(
        page.excess_views_60d for page in pages if page.article == event.primary
    )
    spillover = 1 - (primary_excess / total_excess) if total_excess else 0.0
    edges = calculate_edges(frame, event, pages)
    return EventMetrics(
        slug=event.slug,
        title=event.title,
        event_date=event.date.isoformat(),
        primary=event.primary,
        total_excess_views_60d=total_excess,
        spillover_share=spillover,
        pages=tuple(pages),
        edges=tuple(edges),
    )


def save_metrics(
    metrics: EventMetrics,
    output_dir: str | Path = DEFAULT_PROCESSED,
) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{metrics.slug}-metrics.json"
    path.write_text(json.dumps(asdict(metrics), indent=2), encoding="utf-8")
    return path


def load_metrics(
    slug: str,
    input_dir: str | Path = DEFAULT_PROCESSED,
) -> EventMetrics:
    path = Path(input_dir) / f"{slug}-metrics.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if any("half_life_status" not in page for page in payload["pages"]):
        raise ValueError(f"stale metrics for {slug}; run `internet-half-life analyze --event {slug}`")
    payload["pages"] = tuple(PageMetrics(**page) for page in payload["pages"])
    payload["edges"] = tuple(AttentionEdge(**edge) for edge in payload["edges"])
    return EventMetrics(**payload)
