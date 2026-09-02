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
from .metrics import analyze_event, load_metrics
from .wikimedia import load_event_frame


DEFAULT_PROCESSED = PROJECT_ROOT / "data" / "processed"
DEFAULT_RESULTS = PROJECT_ROOT / "results"
DEFAULT_FIGURES = PROJECT_ROOT / "figures"

MODE_COLUMNS = {
    "timesfm-multivariate": "timesfm_multivariate_wape",
    "timesfm-univariate": "timesfm_univariate_wape",
    "exponential-decay": "exponential_decay_wape",
    "power-law-decay": "power_law_decay_wape",
    "flat-baseline": "flat_baseline_wape",
    "seasonal-naive": "seasonal_naive_wape",
}

PEAK_WINDOW_DAYS = 14
BASELINE_FLOORS = (1, 5, 10)
BASELINE_WINDOWS = (14, 28, 56)


def peak_offset_table(
    frame: pd.DataFrame,
    event: Event,
    post_days: int = PEAK_WINDOW_DAYS,
) -> pd.DataFrame:
    """Measure whether related pages peak before, with, or after the primary."""
    event_day = pd.Timestamp(event.date)
    post = frame.loc[
        event_day : event_day + pd.Timedelta(days=post_days - 1),
        event.articles,
    ]
    primary_peak = int((post[event.primary].idxmax() - event_day).days)
    rows = []
    for page in event.pages:
        if page.article == event.primary:
            continue
        peak = int((post[page.article].idxmax() - event_day).days)
        rows.append(
            {
                "event_slug": event.slug,
                "event_title": event.title,
                "article": page.article,
                "page_label": page.label,
                "primary_peak_offset_days": primary_peak,
                "related_peak_offset_days": peak,
                "relative_peak_offset_days": peak - primary_peak,
            }
        )
    return pd.DataFrame(rows)


def collect_peak_offsets(
    events: list[Event] | None = None,
    post_days: int = PEAK_WINDOW_DAYS,
) -> pd.DataFrame:
    events = events or list(load_catalog().values())
    return pd.concat(
        [peak_offset_table(load_event_frame(event), event, post_days) for event in events],
        ignore_index=True,
    )


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
        frame = load_event_frame(event)
        peak_offsets = peak_offset_table(frame, event)
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
            row[column.replace("_wape", "_median_page_wape")] = float(
                scores.loc[mode, "median_page_wape"]
            )
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
        relative_offsets = peak_offsets["relative_peak_offset_days"]
        row["related_peaks_after_primary_14d"] = int((relative_offsets > 0).sum())
        row["related_peaks_with_primary_14d"] = int((relative_offsets == 0).sum())
        row["related_peaks_before_primary_14d"] = int((relative_offsets < 0).sum())
        row["median_related_peak_offset_14d"] = float(relative_offsets.median())

        for floor in BASELINE_FLOORS:
            sensitivity = analyze_event(frame, event, baseline_floor=float(floor))
            row[f"spillover_floor_{floor}"] = sensitivity.spillover_share
            row[f"total_excess_floor_{floor}"] = sensitivity.total_excess_views_60d
        for days in BASELINE_WINDOWS:
            sensitivity = analyze_event(frame, event, baseline_days=days)
            row[f"spillover_baseline_{days}d"] = sensitivity.spillover_share
            row[f"total_excess_baseline_{days}d"] = sensitivity.total_excess_views_60d
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
    page_model_medians = {
        mode: float(study[column.replace("_wape", "_median_page_wape")].median())
        for mode, column in MODE_COLUMNS.items()
    }
    page_deltas = (
        study["timesfm_multivariate_median_page_wape"]
        - study["timesfm_univariate_median_page_wape"]
    )
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
    flat_wins = study.loc[
        study["flat_baseline_wape"]
        < study[["timesfm_multivariate_wape", "timesfm_univariate_wape"]].min(axis=1),
        "event_slug",
    ].tolist()
    peak_counts = {
        "after": int(study["related_peaks_after_primary_14d"].sum()),
        "same_day": int(study["related_peaks_with_primary_14d"].sum()),
        "before": int(study["related_peaks_before_primary_14d"].sum()),
    }
    floor_sensitivity = {}
    for floor in BASELINE_FLOORS:
        excess = study[f"total_excess_floor_{floor}"]
        share = study[f"spillover_floor_{floor}"]
        floor_sensitivity[str(floor)] = {
            "median_event_spillover_share": float(share.median()),
            "traffic_weighted_spillover_share": float((excess * share).sum() / excess.sum()),
        }
    window_sensitivity = {}
    for days in BASELINE_WINDOWS:
        excess = study[f"total_excess_baseline_{days}d"]
        share = study[f"spillover_baseline_{days}d"]
        window_sensitivity[str(days)] = {
            "total_excess_views_60d": int(excess.sum()),
            "median_event_spillover_share": float(share.median()),
            "traffic_weighted_spillover_share": float((excess * share).sum() / excess.sum()),
        }
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
        "flat_baseline_beats_both_timesfm_events": flat_wins,
        "peak_timing_14d": peak_counts,
        "baseline_floor_sensitivity": floor_sensitivity,
        "baseline_window_sensitivity": window_sensitivity,
        "median_event_wape": model_medians,
        "median_event_median_page_wape": page_model_medians,
        "page_level_multivariate_vs_univariate": {
            "multivariate_wins": int((page_deltas < 0).sum()),
            "univariate_wins": int((page_deltas > 0).sum()),
            "median_wape_difference": float(page_deltas.median()),
        },
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


def save_peak_offsets(
    peak_offsets: pd.DataFrame,
    output_dir: str | Path = DEFAULT_RESULTS,
) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "peak-offsets.csv"
    peak_offsets.to_csv(path, index=False)
    return path


def _figure_setup(figsize: tuple[float, float]):
    fig, ax = plt.subplots(figsize=figsize, facecolor="#fbfaf7")
    ax.set_facecolor("#fbfaf7")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", color="#dedbd2", linewidth=0.7, alpha=0.8)
    return fig, ax


def render_catalog_study(
    study: pd.DataFrame,
    peak_offsets: pd.DataFrame | None = None,
    output_dir: str | Path = DEFAULT_FIGURES,
) -> list[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    if peak_offsets is not None:
        order = study.sort_values("median_related_peak_offset_14d")["event_slug"]
        labels = study.set_index("event_slug")["event_title"]
        y_by_slug = {slug: index for index, slug in enumerate(order)}
        fig, ax = _figure_setup((10.5, 6.2))
        for slug, group in peak_offsets.groupby("event_slug", sort=False):
            y = y_by_slug[slug]
            values = group["relative_peak_offset_days"].to_numpy(dtype=float)
            jitter = np.linspace(-0.12, 0.12, len(values))
            ax.scatter(
                values,
                y + jitter,
                s=42,
                color="#ef5b5b" if slug == "barbenheimer" else "#7c5cff",
                alpha=0.88,
                edgecolor="#fbfaf7",
                linewidth=0.5,
                zorder=3,
            )
        ax.axvline(0, color="#222222", linewidth=1.2)
        ax.set_yticks(range(len(order)), labels=[labels[slug] for slug in order])
        ax.set_xlabel("related-page peak day − primary-page peak day  (first 14 days)")
        ax.set_title(
            "Related pages usually peak with the event, not after it",
            loc="left",
            fontsize=17,
            weight="bold",
        )
        ax.text(
            0.99,
            0.02,
            "35 same day  ·  19 before  ·  11 after",
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=10,
            color="#4b4a46",
        )
        fig.tight_layout()
        path = output_dir / "peak-offsets.png"
        fig.savefig(path, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        paths.append(path)

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
        "flat pre-event\nmedian",
    ]
    columns = [
        MODE_COLUMNS["timesfm-multivariate"],
        MODE_COLUMNS["timesfm-univariate"],
        MODE_COLUMNS["exponential-decay"],
        MODE_COLUMNS["power-law-decay"],
        MODE_COLUMNS["flat-baseline"],
    ]
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
