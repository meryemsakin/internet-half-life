"""Forecast attention decay with a transparent baseline or TimesFM-3."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from .catalog import Event, PROJECT_ROOT


DEFAULT_PROCESSED = PROJECT_ROOT / "data" / "processed"


def _forecast_window(
    frame: pd.DataFrame,
    event: Event,
    reveal_days: int,
    horizon: int,
    context_days: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    context_end = pd.Timestamp(event.date + timedelta(days=reveal_days))
    forecast_start = context_end + pd.Timedelta(days=1)
    forecast_end = forecast_start + pd.Timedelta(days=horizon - 1)
    context = frame.loc[:context_end].tail(context_days)
    truth = frame.loc[forecast_start:forecast_end]
    if len(context) < 32:
        raise ValueError(f"TimesFM needs more context; found {len(context)} days")
    if len(truth) != horizon:
        raise ValueError(f"forecast truth has {len(truth)} rows, expected {horizon}")
    return context, truth


def seasonal_naive(
    context: pd.DataFrame,
    horizon: int,
    period: int = 7,
) -> np.ndarray:
    tail = context.iloc[-period:].to_numpy(dtype=float).T
    return np.stack([tail[:, step % period] for step in range(horizon)], axis=1)


def flat_baseline(
    context: pd.DataFrame,
    event: Event,
    horizon: int,
    baseline_days: int = 28,
) -> np.ndarray:
    """Return each page to its pre-event median for the full horizon."""
    baselines = _pre_event_baselines(context, event, baseline_days)
    return np.repeat(baselines[:, np.newaxis], horizon, axis=1)


def _pre_event_baselines(
    context: pd.DataFrame,
    event: Event,
    days: int = 28,
) -> np.ndarray:
    event_day = pd.Timestamp(event.date)
    pre_event = context.loc[
        event_day - pd.Timedelta(days=days) : event_day - pd.Timedelta(days=1),
        event.articles,
    ]
    if len(pre_event) < days:
        raise ValueError(
            f"decay baselines need {days} pre-event days; found {len(pre_event)}"
        )
    return np.maximum(pre_event.median().to_numpy(dtype=float), 1.0)


def parametric_decay(
    context: pd.DataFrame,
    event: Event,
    horizon: int,
    kind: str,
    baseline_days: int = 28,
) -> np.ndarray:
    """Fit a two-parameter decay curve to each page's revealed excess traffic.

    The ordinary-day level is fixed to the median of the 28 days before the
    event. The two fitted parameters are the spike amplitude and decay rate.
    Only observations from the revealed peak onward are used, so the curve is
    a deliberately simple null model for post-spike attention decay.
    """
    if kind not in {"exponential", "power-law"}:
        raise ValueError("kind must be 'exponential' or 'power-law'")

    event_day = pd.Timestamp(event.date)
    revealed = context.loc[event_day:, event.articles]
    if revealed.empty:
        raise ValueError("no revealed post-event observations for decay fit")
    baselines = _pre_event_baselines(context, event, baseline_days)
    predictions = np.empty((len(event.articles), horizon), dtype=float)

    for article_index, article in enumerate(event.articles):
        values = revealed[article].to_numpy(dtype=float)
        peak_index = int(np.argmax(values))
        excess = np.maximum(values[peak_index:] - baselines[article_index], 1.0)
        elapsed = np.arange(len(excess), dtype=float)

        if len(excess) >= 2:
            if kind == "exponential":
                transformed_time = elapsed
            else:
                transformed_time = np.log1p(elapsed)
            slope, intercept = np.polyfit(transformed_time, np.log(excess), 1)
            slope = min(float(slope), 0.0)
            intercept = float(intercept)
        else:
            slope = 0.0
            intercept = float(np.log(excess[0]))

        future_elapsed = np.arange(
            len(excess), len(excess) + horizon, dtype=float
        )
        if kind == "exponential":
            future_time = future_elapsed
        else:
            future_time = np.log1p(future_elapsed)
        predictions[article_index] = (
            baselines[article_index] + np.exp(intercept + slope * future_time)
        )

    return predictions


class TimesFMBackend:
    """Lazy TimesFM wrapper so the rest of the project stays lightweight."""

    def __init__(self, device: str | None = None, batch_size: int = 1) -> None:
        try:
            import torch
            from timesfm3 import ModelConfig, TimesFM3Evaluator
        except ImportError as error:
            raise RuntimeError(
                "TimesFM support is optional. Install it with "
                "`pip install -e '.[timesfm]'`."
            ) from error

        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
            elif torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
        self.device = device
        self.model = TimesFM3Evaluator(
            ModelConfig(
                checkpoint_path="google/timesfm-3.0-pytorch",
                per_core_batch_size=batch_size,
                device=device,
            )
        )

    def predict(
        self,
        context: np.ndarray,
        horizon: int,
        univariate: bool,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        output = next(
            self.model.predict_batch(
                [context.astype(np.float32)],
                horizon=horizon,
                return_quantiles=True,
                use_symmetric_averaging=False,
                univariate=univariate,
            )
        )
        point = np.asarray(output.forecast, dtype=float)
        quantiles = np.asarray(output.quantiles, dtype=float)
        return point, quantiles[:, :, 0], quantiles[:, :, -1]


def _long_forecast(
    event: Event,
    truth: pd.DataFrame,
    point: np.ndarray,
    low: np.ndarray,
    high: np.ndarray,
    mode: str,
) -> pd.DataFrame:
    rows = []
    for article_index, article in enumerate(event.articles):
        page = event.page(article)
        for step, timestamp in enumerate(truth.index):
            rows.append(
                {
                    "date": timestamp.date().isoformat(),
                    "article": article,
                    "label": page.label,
                    "role": page.role,
                    "mode": mode,
                    "actual": float(truth.iloc[step][article]),
                    "forecast": float(point[article_index, step]),
                    "q10": float(low[article_index, step]),
                    "q90": float(high[article_index, step]),
                }
            )
    return pd.DataFrame(rows)


def forecast_event(
    frame: pd.DataFrame,
    event: Event,
    reveal_days: int = 7,
    horizon: int = 30,
    context_days: int = 512,
    device: str | None = None,
    backend: TimesFMBackend | None = None,
) -> pd.DataFrame:
    """Compare TimesFM-3 with explicit post-spike attention-decay baselines."""
    context, truth = _forecast_window(
        frame, event, reveal_days, horizon, context_days
    )
    matrix = context[event.articles].to_numpy(dtype=float).T
    backend = backend or TimesFMBackend(device=device)
    outputs = []

    for univariate, mode in (
        (False, "timesfm-multivariate"),
        (True, "timesfm-univariate"),
    ):
        point, low, high = backend.predict(matrix, horizon, univariate=univariate)
        outputs.append(_long_forecast(event, truth, point, low, high, mode))

    missing_interval = np.full((len(event.articles), horizon), np.nan)
    for kind, mode in (
        ("exponential", "exponential-decay"),
        ("power-law", "power-law-decay"),
    ):
        point = parametric_decay(context, event, horizon, kind=kind)
        outputs.append(
            _long_forecast(
                event, truth, point, missing_interval, missing_interval, mode
            )
        )

    flat = flat_baseline(context, event, horizon)
    outputs.append(
        _long_forecast(
            event,
            truth,
            flat,
            missing_interval,
            missing_interval,
            "flat-baseline",
        )
    )

    naive = seasonal_naive(context[event.articles], horizon)
    outputs.append(
        _long_forecast(
            event,
            truth,
            naive,
            missing_interval,
            missing_interval,
            "seasonal-naive",
        )
    )
    return pd.concat(outputs, ignore_index=True)


def save_forecast(
    forecast: pd.DataFrame,
    event: Event,
    output_dir: str | Path = DEFAULT_PROCESSED,
) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{event.slug}-forecast.csv"
    forecast.to_csv(path, index=False)
    return path


def forecast_scores(forecast: pd.DataFrame) -> pd.DataFrame:
    """Return point errors and interval diagnostics for each forecast mode."""
    rows = []
    for mode, group in forecast.groupby("mode", sort=False):
        absolute_error = (group["forecast"] - group["actual"]).abs()
        denominator = group["actual"].abs().sum()
        if "article" in group:
            page_wape_values = []
            for _, page in group.groupby("article", sort=False):
                page_denominator = page["actual"].abs().sum()
                page_wape_values.append(
                    (page["forecast"] - page["actual"]).abs().sum()
                    / page_denominator
                    if page_denominator
                    else np.nan
                )
            median_page_wape = float(np.nanmedian(page_wape_values))
        else:
            median_page_wape = (
                float(absolute_error.sum() / denominator) if denominator else np.nan
            )
        interval_rows = group[
            group["q10"].notna()
            & group["q90"].notna()
            & np.isfinite(group["q10"])
            & np.isfinite(group["q90"])
            & (group["q90"] >= group["q10"])
        ]
        if interval_rows.empty:
            coverage = np.nan
            mean_width = np.nan
            relative_width = np.nan
        else:
            widths = interval_rows["q90"] - interval_rows["q10"]
            actual_scale = interval_rows["actual"].abs().mean()
            coverage = float(
                (
                    (interval_rows["actual"] >= interval_rows["q10"])
                    & (interval_rows["actual"] <= interval_rows["q90"])
                ).mean()
            )
            mean_width = float(widths.mean())
            relative_width = (
                float(mean_width / actual_scale) if actual_scale else np.nan
            )
        rows.append(
            {
                "mode": mode,
                "wape": float(absolute_error.sum() / denominator) if denominator else np.nan,
                "median_page_wape": median_page_wape,
                "median_absolute_error": float(absolute_error.median()),
                "interval_coverage": coverage,
                "mean_interval_width": mean_width,
                "relative_interval_width": relative_width,
                "interval_observations": len(interval_rows),
            }
        )
    return pd.DataFrame(rows)


def forecast_error_breakdown(forecast: pd.DataFrame) -> pd.DataFrame:
    """Expose each page's denominator and contribution to pooled model error."""
    rows = []
    for mode, group in forecast.groupby("mode", sort=False):
        group = group.copy()
        group["absolute_error"] = (group["forecast"] - group["actual"]).abs()
        total_error = float(group["absolute_error"].sum())
        for article, page in group.groupby("article", sort=False):
            denominator = float(page["actual"].abs().sum())
            error = float(page["absolute_error"].sum())
            worst = page.loc[page["absolute_error"].idxmax()]
            rows.append({
                "mode": mode,
                "article": article,
                "actual_total": denominator,
                "absolute_error_total": error,
                "page_wape": error / denominator if denominator else np.nan,
                "share_of_mode_absolute_error": error / total_error if total_error else 0.0,
                "worst_error_date": worst["date"],
                "worst_error_actual": float(worst["actual"]),
                "worst_error_forecast": float(worst["forecast"]),
            })
    return pd.DataFrame(rows)
