"""Cross-event evaluation for the full Internet Half-Life catalog."""

from __future__ import annotations

from itertools import combinations, product
import json
from math import comb
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .catalog import Event, PROJECT_ROOT, load_catalog
from .forecasting import forecast_scores
from .metrics import load_metrics


DEFAULT_PROCESSED = PROJECT_ROOT / "data" / "processed"
DEFAULT_RESULTS = PROJECT_ROOT / "results"
DEFAULT_FIGURES = PROJECT_ROOT / "figures"

MODE_COLUMNS = {
    "timesfm-multivariate": "timesfm_multivariate_wape",
    "timesfm-univariate": "timesfm_univariate_wape",
    "exponential-decay": "exponential_decay_wape",
    "power-law-decay": "power_law_decay_wape",
    "seasonal-naive": "seasonal_naive_wape",
}


def exact_sign_test(wins: int, losses: int) -> float:
    """Two-sided exact binomial sign test, ignoring ties."""
    trials = wins + losses
    if trials == 0:
        return 1.0
    tail = min(wins, losses)
    probability = 2 * sum(comb(trials, k) for k in range(tail + 1)) / (2**trials)
    return min(float(probability), 1.0)


def exact_sign_flip_test(differences: np.ndarray) -> float:
    """Two-sided paired randomization test for the mean difference."""
    differences = np.asarray(differences, dtype=float)
    differences = differences[np.isfinite(differences)]
    if len(differences) == 0:
        return 1.0
    observed = abs(float(differences.mean()))
    permuted = [
        abs(float(np.mean(differences * np.asarray(signs))))
        for signs in product((-1.0, 1.0), repeat=len(differences))
    ]
    return float(np.mean(np.asarray(permuted) >= observed - 1e-12))


def collect_catalog_study(
    events: list[Event] | None = None,
    processed_dir: str | Path = DEFAULT_PROCESSED,
) -> pd.DataFrame:
    """Collect comparable metrics and forecasts for every catalog event."""
    events = events or list(load_catalog().values())
    processed_dir = Path(processed_dir)
    rows: list[dict] = []

    for event in events:
        metrics = load_metrics(event.slug, input_dir=processed_dir)
        forecast_path = processed_dir / f"{event.slug}-forecast.csv"
        if not forecast_path.exists():
            raise FileNotFoundError(
                f"missing {forecast_path}; run `internet-half-life forecast --event all`"
            )
        scores = forecast_scores(pd.read_csv(forecast_path)).set_index("mode")
        missing_modes = set(MODE_COLUMNS) - set(scores.index)
        if missing_modes:
            raise ValueError(
                f"{forecast_path} is missing modes: {sorted(missing_modes)}"
            )

        row = {
            "event_slug": event.slug,
            "event_title": event.title,
            "event_date": event.date.isoformat(),
            "pages": len(event.pages),
            "total_excess_views_60d": metrics.total_excess_views_60d,
            "spillover_share": metrics.spillover_share,
            "primary_half_life_days": metrics.page(event.primary).half_life_days,
        }
        for mode, column in MODE_COLUMNS.items():
            row[column] = float(scores.loc[mode, "wape"])
        for prefix, mode in (
            ("multivariate", "timesfm-multivariate"),
            ("univariate", "timesfm-univariate"),
        ):
            row[f"{prefix}_interval_coverage"] = float(
                scores.loc[mode, "interval_coverage"]
            )
            row[f"{prefix}_relative_interval_width"] = float(
                scores.loc[mode, "relative_interval_width"]
            )

        row["multivariate_minus_univariate_wape"] = (
            row["timesfm_multivariate_wape"] - row["timesfm_univariate_wape"]
        )
        row["best_decay_wape"] = min(
            row["exponential_decay_wape"], row["power_law_decay_wape"]
        )
        row["decay_beats_both_timesfm"] = row["best_decay_wape"] < min(
            row["timesfm_multivariate_wape"], row["timesfm_univariate_wape"]
        )
        rows.append(row)

    return pd.DataFrame(rows)


TRAINING_CUTOFF = "2023-12-01"


def training_cutoff_split(study: pd.DataFrame, cutoff: str = TRAINING_CUTOFF) -> dict:
    """Compare forecast skill either side of TimesFM 3.0's Wikipedia cutoff.

    The model card states the pretraining pageview data was cut off in November
    2023. Pageviews before December may have been available to the model;
    observations after November could not have been. If skill comes partly from
    having seen these series, it should be higher on the earlier side.

    Raw WAPE cannot answer this on its own, because the two groups are also
    separated in time and Wikipedia traffic has changed for reasons that have
    nothing to do with any model. So the comparison is run on the ratio of
    TimesFM's error to the best parametric decay fit on the same event. A
    parametric fit has no training corpus and cannot have memorised anything,
    so if an era is simply harder, both degrade and the ratio holds steady. A
    shift in the ratio is a statement about the model.
    """
    frame = study.copy()
    frame["pre_training_cutoff"] = (
        pd.to_datetime(frame["event_date"]) < pd.Timestamp(cutoff)
    )
    frame["skill_vs_decay"] = (
        frame["timesfm_multivariate_wape"] / frame["best_decay_wape"]
    )

    groups = {}
    for seen, part in frame.groupby("pre_training_cutoff"):
        key = "seen" if seen else "unseen"
        groups[key] = {
            "events": int(len(part)),
            "median_wape": float(part["timesfm_multivariate_wape"].median()),
            "median_skill_vs_decay": float(part["skill_vs_decay"].median()),
            "slugs": part["event_slug"].tolist(),
        }

    seen = frame.loc[frame["pre_training_cutoff"], "skill_vs_decay"].to_numpy(float)
    unseen = frame.loc[~frame["pre_training_cutoff"], "skill_vs_decay"].to_numpy(float)
    return {
        "cutoff": cutoff,
        "groups": groups,
        "median_difference": (
            float(np.median(seen) - np.median(unseen))
            if len(seen) and len(unseen) else None
        ),
        "permutation_p_value": _two_sample_permutation(seen, unseen),
    }


def _two_sample_permutation(a: np.ndarray, b: np.ndarray) -> float:
    """Exact two-sided permutation test on the difference of medians."""
    a = a[np.isfinite(a)]
    b = b[np.isfinite(b)]
    if len(a) < 2 or len(b) < 2:
        return 1.0
    observed = abs(float(np.median(a) - np.median(b)))
    pool = np.concatenate([a, b])
    hits = 0
    partitions = 0
    for left_indices in combinations(range(len(pool)), len(a)):
        mask = np.zeros(len(pool), dtype=bool)
        mask[list(left_indices)] = True
        difference = abs(float(np.median(pool[mask]) - np.median(pool[~mask])))
        if difference >= observed - 1e-12:
            hits += 1
        partitions += 1
    return float(hits / partitions)


def summarize_catalog_study(study: pd.DataFrame) -> dict:
    deltas = study["multivariate_minus_univariate_wape"].to_numpy(dtype=float)
    wins = int((deltas < 0).sum())
    losses = int((deltas > 0).sum())
    total_excess = int(study["total_excess_views_60d"].sum())
    weighted_spillover = float(
        (
            study["total_excess_views_60d"] * study["spillover_share"]
        ).sum()
        / total_excess
    )
    model_medians = {
        mode: float(study[column].median()) for mode, column in MODE_COLUMNS.items()
    }
    interval_diagnostics = {}
    for prefix in ("multivariate", "univariate"):
        coverage = study[f"{prefix}_interval_coverage"]
        relative_width = study[f"{prefix}_relative_interval_width"]
        interval_diagnostics[prefix] = {
            "mean_event_coverage": float(coverage.mean()),
            "coverage_range": [float(coverage.min()), float(coverage.max())],
            "events_at_or_above_80_percent": int((coverage >= 0.8).sum()),
            "median_relative_interval_width": float(relative_width.median()),
            "maximum_relative_interval_width": float(relative_width.max()),
        }

    highest_spillover = study.loc[study["spillover_share"].idxmax()]
    return {
        "catalog_events": len(study),
        "total_excess_views_60d": total_excess,
        "weighted_spillover_share": weighted_spillover,
        "median_event_spillover_share": float(study["spillover_share"].median()),
        "highest_spillover_event": {
            "slug": highest_spillover["event_slug"],
            "share": float(highest_spillover["spillover_share"]),
        },
        "multivariate_vs_univariate": {
            "multivariate_wins": wins,
            "univariate_wins": losses,
            "ties": int(len(deltas) - wins - losses),
            "median_wape_difference": float(np.median(deltas)),
            "mean_wape_difference": float(np.mean(deltas)),
            "exact_sign_test_p_value": exact_sign_test(wins, losses),
            "exact_sign_flip_mean_p_value": exact_sign_flip_test(deltas),
        },
        "decay_beats_both_timesfm_events": study.loc[
            study["decay_beats_both_timesfm"], "event_slug"
        ].tolist(),
        "median_event_wape": model_medians,
        "interval_diagnostics": interval_diagnostics,
        "training_cutoff_split": training_cutoff_split(study),
    }


def save_catalog_study(
    study: pd.DataFrame,
    summary: dict,
    output_dir: str | Path = DEFAULT_RESULTS,
) -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    table_path = output_dir / "catalog-study.csv"
    summary_path = output_dir / "study-summary.json"
    study.to_csv(table_path, index=False, float_format="%.6f")
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return table_path, summary_path


def _figure_setup(figsize: tuple[float, float]):
    fig, ax = plt.subplots(figsize=figsize, facecolor="#fbfaf7")
    ax.set_facecolor("#fbfaf7")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", color="#dedbd2", linewidth=0.7, alpha=0.8)
    return fig, ax


def render_catalog_study(
    study: pd.DataFrame,
    output_dir: str | Path = DEFAULT_FIGURES,
) -> list[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    spillover = study.sort_values("spillover_share")
    fig, ax = _figure_setup((10.5, 6.2))
    colors = [
        "#ef5b5b" if slug == "barbenheimer" else "#7c5cff"
        for slug in spillover["event_slug"]
    ]
    ax.barh(
        spillover["event_title"],
        100 * spillover["spillover_share"],
        color=colors,
        alpha=0.92,
    )
    for y, share in enumerate(spillover["spillover_share"]):
        ax.text(100 * share + 1, y, f"{share:.0%}", va="center", fontsize=9)
    ax.set_xlim(0, 105)
    ax.set_xlabel("share of 60-day excess views outside the primary page")
    ax.set_title(
        "The event page is rarely where attention ends up",
        loc="left",
        fontsize=17,
        weight="bold",
    )
    fig.tight_layout()
    path = output_dir / "catalog-spillover.png"
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    paths.append(path)

    delta = study.sort_values("multivariate_minus_univariate_wape")
    fig, ax = _figure_setup((10.5, 6.2))
    values = delta["multivariate_minus_univariate_wape"]
    colors = ["#2db7a3" if value < 0 else "#ef5b5b" for value in values]
    ax.barh(delta["event_title"], values, color=colors, alpha=0.92)
    ax.axvline(0, color="#222222", linewidth=1.2)
    ax.set_xscale("symlog", linthresh=0.01)
    ax.set_xlabel(
        "multivariate − univariate WAPE  (negative favors multivariate; symmetric log scale)"
    )
    ax.set_title(
        "Related pages do not provide a consistent forecasting gain",
        loc="left",
        fontsize=17,
        weight="bold",
    )
    fig.tight_layout()
    path = output_dir / "multivariate-delta-by-event.png"
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    paths.append(path)

    labels = [
        "TimesFM-3\nmultivariate",
        "TimesFM-3\nunivariate",
        "exponential\ndecay",
        "power-law\ndecay",
        "weekly\nnaive",
    ]
    columns = list(MODE_COLUMNS.values())
    palette = ["#ef5b5b", "#3a86ff", "#2db7a3", "#7c5cff", "#8d8a82"]
    fig, ax = _figure_setup((10.5, 6.2))
    arrays = [study[column].to_numpy(dtype=float) for column in columns]
    try:
        box = ax.boxplot(
            arrays, tick_labels=labels, patch_artist=True, showfliers=False
        )
    except TypeError:  # Matplotlib 3.8 used the previous keyword.
        box = ax.boxplot(arrays, labels=labels, patch_artist=True, showfliers=False)
    for patch, color in zip(box["boxes"], palette):
        patch.set_facecolor(color)
        patch.set_alpha(0.35)
    for index, (values, color) in enumerate(zip(arrays, palette), start=1):
        offsets = np.linspace(-0.08, 0.08, len(values))
        ax.scatter(
            index + offsets,
            values,
            s=28,
            color=color,
            edgecolor="#fbfaf7",
            linewidth=0.5,
            zorder=3,
        )
    ax.set_yscale("log")
    ax.grid(axis="y", color="#dedbd2", linewidth=0.7, alpha=0.8)
    ax.grid(axis="x", visible=False)
    ax.set_ylabel("event-level WAPE  (log scale; lower is better)")
    ax.set_title(
        "A 330M-parameter model does not make the simple null models irrelevant",
        loc="left",
        fontsize=17,
        weight="bold",
    )
    fig.tight_layout()
    path = output_dir / "forecast-model-comparison.png"
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    paths.append(path)

    calibration = study.sort_values("multivariate_interval_coverage")
    y = np.arange(len(calibration))
    fig, (coverage_ax, width_ax) = plt.subplots(
        1,
        2,
        figsize=(13.5, 6.5),
        sharey=True,
        facecolor="#fbfaf7",
        gridspec_kw={"width_ratios": [1, 1.15], "wspace": 0.08},
    )
    for ax in (coverage_ax, width_ax):
        ax.set_facecolor("#fbfaf7")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="x", color="#dedbd2", linewidth=0.7, alpha=0.8)
    coverage_ax.scatter(
        calibration["multivariate_interval_coverage"],
        y,
        color="#ef5b5b",
        s=48,
        label="multivariate",
        zorder=3,
    )
    coverage_ax.scatter(
        calibration["univariate_interval_coverage"],
        y,
        color="#3a86ff",
        s=48,
        label="univariate",
        zorder=3,
    )
    coverage_ax.axvline(0.8, color="#222222", linestyle="--", linewidth=1)
    coverage_ax.set_xlim(0.5, 1.02)
    coverage_ax.set_yticks(y, labels=calibration["event_title"])
    coverage_ax.set_xlabel("observed coverage of the nominal 80% interval")
    coverage_ax.legend(frameon=False, fontsize=9, loc="lower right")

    width_ax.scatter(
        calibration["multivariate_relative_interval_width"],
        y,
        color="#ef5b5b",
        s=48,
        zorder=3,
    )
    width_ax.scatter(
        calibration["univariate_relative_interval_width"],
        y,
        color="#3a86ff",
        s=48,
        zorder=3,
    )
    width_ax.axvline(1, color="#222222", linestyle="--", linewidth=1)
    width_ax.set_xscale("log")
    width_ax.set_xlabel("mean interval width ÷ mean actual traffic  (log scale)")
    fig.suptitle(
        "Coverage alone hides how wide TimesFM-3's intervals are",
        x=0.08,
        y=0.99,
        ha="left",
        fontsize=17,
        weight="bold",
    )
    fig.subplots_adjust(left=0.29, right=0.98, top=0.88, bottom=0.14, wspace=0.08)
    path = output_dir / "interval-calibration.png"
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    paths.append(path)

    return paths
