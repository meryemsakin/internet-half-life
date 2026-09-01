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
) -> pd.DataFrame:
    """Compare multivariate TimesFM-3, univariate TimesFM-3, and weekly naive."""
    context, truth = _forecast_window(
        frame, event, reveal_days, horizon, context_days
    )
    matrix = context[event.articles].to_numpy(dtype=float).T
    backend = TimesFMBackend(device=device)
    outputs = []

    for univariate, mode in ((False, "timesfm-multivariate"), (True, "timesfm-univariate")):
        point, low, high = backend.predict(matrix, horizon, univariate=univariate)
        outputs.append(_long_forecast(event, truth, point, low, high, mode))

    naive = seasonal_naive(context[event.articles], horizon)
    outputs.append(_long_forecast(event, truth, naive, naive, naive, "seasonal-naive"))
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
    """Return per-mode errors normalized by each page's mean actual traffic."""
    rows = []
    for mode, group in forecast.groupby("mode", sort=False):
        absolute_error = (group["forecast"] - group["actual"]).abs()
        denominator = group["actual"].abs().sum()
        rows.append(
            {
                "mode": mode,
                "wape": float(absolute_error.sum() / denominator) if denominator else np.nan,
                "median_absolute_error": float(absolute_error.median()),
                "interval_coverage": float(
                    ((group["actual"] >= group["q10"]) & (group["actual"] <= group["q90"])).mean()
                ),
            }
        )
    return pd.DataFrame(rows)

