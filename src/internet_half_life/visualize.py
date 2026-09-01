"""Publication-ready figures for an event's attention afterlife."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import networkx as nx
import numpy as np
import pandas as pd

from .catalog import Event, PROJECT_ROOT
from .metrics import AttentionEdge, EventMetrics


DEFAULT_FIGURES = PROJECT_ROOT / "figures"
ROLE_COLORS = {
    "event": "#ef5b5b",
    "work": "#7c5cff",
    "person": "#ff9f43",
    "history": "#2db7a3",
    "organization": "#3a86ff",
    "technology": "#00a8cc",
    "idea": "#58a65c",
    "place": "#8d6e63",
    "object": "#d65db1",
}


def _relative_days(index: pd.DatetimeIndex, event: Event) -> np.ndarray:
    return (index - pd.Timestamp(event.date)).days.to_numpy()


def _display_edges(metrics: EventMetrics) -> list[AttentionEdge]:
    """Keep a maximum spanning tree plus the two strongest extra relations."""
    graph = nx.Graph()
    for page in metrics.pages:
        graph.add_node(page.article)
    for edge in metrics.edges:
        graph.add_edge(edge.source, edge.target, weight=edge.correlation, edge=edge)
    if graph.number_of_edges() == 0:
        return []
    tree = nx.maximum_spanning_tree(graph, weight="weight")
    selected = {frozenset((left, right)) for left, right in tree.edges}
    extras = [
        edge
        for edge in metrics.edges
        if frozenset((edge.source, edge.target)) not in selected
    ][:2]
    result = [graph[left][right]["edge"] for left, right in tree.edges]
    return result + extras


def render_event_atlas(
    frame: pd.DataFrame,
    event: Event,
    metrics: EventMetrics,
    output_dir: str | Path = DEFAULT_FIGURES,
) -> Path:
    """Render the hero timeline and the attention constellation."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{event.slug}-atlas.png"

    fig = plt.figure(figsize=(15, 7.6), facecolor="#fbfaf7")
    grid = fig.add_gridspec(1, 2, width_ratios=[1.25, 1], wspace=0.08)
    timeline = fig.add_subplot(grid[0, 0])
    network_ax = fig.add_subplot(grid[0, 1])
    timeline.set_facecolor("#fbfaf7")
    network_ax.set_facecolor("#fbfaf7")

    event_day = pd.Timestamp(event.date)
    display = frame.loc[event_day - pd.Timedelta(days=30) : event_day + pd.Timedelta(days=60)]
    x = _relative_days(display.index, event)
    for page_metrics in metrics.pages:
        page = event.page(page_metrics.article)
        attention_index = display[page.article] / page_metrics.baseline_views
        timeline.plot(
            x,
            attention_index,
            label=page.label,
            color=ROLE_COLORS.get(page.role, "#666666"),
            linewidth=2.4 if page.article == event.primary else 1.35,
            alpha=1 if page.article == event.primary else 0.82,
        )
    timeline.axvline(0, color="#222222", linewidth=1, linestyle="--")
    timeline.axhline(1, color="#b9b5aa", linewidth=0.8)
    timeline.set_yscale("log")
    timeline.set_xlim(-30, 60)
    timeline.set_xlabel("days relative to the event", fontsize=10)
    timeline.set_ylabel("attention index  (ordinary day = 1)", fontsize=10)
    timeline.set_title("HOW ATTENTION ROSE AND FADED", loc="left", fontsize=10, weight="bold")
    timeline.spines[["top", "right"]].set_visible(False)
    timeline.grid(axis="y", color="#dedbd2", linewidth=0.7, alpha=0.7)
    timeline.legend(frameon=False, fontsize=8, ncol=2, loc="upper right")

    graph = nx.DiGraph()
    for page_metrics in metrics.pages:
        graph.add_node(page_metrics.article)
    display_edges = _display_edges(metrics)
    for edge in display_edges:
        graph.add_edge(edge.source, edge.target, weight=edge.correlation, lag=edge.lag_days)
    positions = nx.spring_layout(graph, seed=12, k=1.15)

    excess = np.array([max(page.excess_views_60d, 1) for page in metrics.pages], dtype=float)
    node_sizes = 900 + 2600 * (np.log1p(excess) - np.log1p(excess).min()) / max(
        np.ptp(np.log1p(excess)), 1
    )
    node_colors = [ROLE_COLORS.get(page.role, "#777777") for page in metrics.pages]
    nx.draw_networkx_nodes(
        graph,
        positions,
        node_size=node_sizes,
        node_color=node_colors,
        edgecolors="#fbfaf7",
        linewidths=2.5,
        ax=network_ax,
    )
    widths = [1 + 4 * graph[u][v]["weight"] for u, v in graph.edges]
    nx.draw_networkx_edges(
        graph,
        positions,
        width=widths,
        edge_color="#8d8a82",
        alpha=0.55,
        arrows=True,
        arrowsize=14,
        connectionstyle="arc3,rad=0.06",
        ax=network_ax,
    )
    labels = {
        page.article: (
            f"{page.label}\n"
            f"half-life: {page.half_life_days if page.half_life_days is not None else '60+'}d"
        )
        for page in metrics.pages
    }
    nx.draw_networkx_labels(graph, positions, labels=labels, font_size=8, ax=network_ax)
    edge_labels = {
        (u, v): (f"+{data['lag']}d" if data["lag"] else "same day")
        for u, v, data in graph.edges(data=True)
    }
    nx.draw_networkx_edge_labels(
        graph,
        positions,
        edge_labels=edge_labels,
        font_size=7,
        font_color="#67645e",
        rotate=False,
        ax=network_ax,
    )
    network_ax.set_title("WHERE ATTENTION TRAVELLED", loc="left", fontsize=10, weight="bold")
    network_ax.axis("off")

    primary = metrics.page(event.primary)
    fig.suptitle(event.title, x=0.055, y=0.98, ha="left", fontsize=26, weight="bold")
    subtitle = (
        f"{event.date.isoformat()}  ·  primary half-life {primary.half_life_days or '60+'} days  ·  "
        f"{metrics.spillover_share:.0%} of excess attention landed on related pages"
    )
    fig.text(0.056, 0.925, subtitle, ha="left", fontsize=11, color="#5d5a54")
    fig.text(
        0.056,
        0.025,
        "Source: Wikimedia daily pageviews. Arrows show strongest lead/lag co-movement, not causality.",
        fontsize=8,
        color="#77736b",
    )
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def render_forecast(
    frame: pd.DataFrame,
    forecast: pd.DataFrame,
    event: Event,
    output_dir: str | Path = DEFAULT_FIGURES,
) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{event.slug}-forecast.png"
    primary = event.primary
    subset = forecast[forecast["article"] == primary].copy()
    subset["date"] = pd.to_datetime(subset["date"])
    start = subset["date"].min()
    actual = subset[subset["mode"] == "timesfm-multivariate"]
    context = frame.loc[start - pd.Timedelta(days=30) : start - pd.Timedelta(days=1), primary]

    fig, ax = plt.subplots(figsize=(11, 5.2), facecolor="#fbfaf7")
    ax.set_facecolor("#fbfaf7")
    ax.plot(context.index, context, color="#9b978e", linewidth=1.2, label="revealed history")
    ax.plot(actual["date"], actual["actual"], color="#151515", linewidth=2.2, label="actual")
    palette = {
        "timesfm-multivariate": "#ef5b5b",
        "timesfm-univariate": "#3a86ff",
        "exponential-decay": "#2db7a3",
        "power-law-decay": "#7c5cff",
        "seasonal-naive": "#8d8a82",
    }
    for mode, group in subset.groupby("mode", sort=False):
        ax.plot(
            group["date"],
            group["forecast"],
            color=palette[mode],
            linewidth=2 if mode != "seasonal-naive" else 1.1,
            linestyle="--" if "decay" in mode or mode == "seasonal-naive" else "-",
            label=(
                mode.replace("timesfm-", "TimesFM-3 ")
                .replace("exponential-decay", "exponential decay")
                .replace("power-law-decay", "power-law decay")
                .replace("seasonal-naive", "weekly naive")
            ),
        )
        if mode == "timesfm-multivariate":
            ax.fill_between(
                group["date"], group["q10"], group["q90"],
                color=palette[mode], alpha=0.13, linewidth=0,
            )
    ax.axvline(start, color="#333333", linestyle=":", linewidth=1)
    ax.set_title(f"Can related pages forecast the afterlife of {event.title}?", loc="left", fontsize=16, weight="bold")
    ax.set_ylabel("daily pageviews")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#dedbd2", linewidth=0.7)
    ax.legend(frameon=False, fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path
