"""Command-line entry point for the attention atlas."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

from .catalog import PROJECT_ROOT, Event, get_event, load_catalog
from .forecasting import TimesFMBackend, forecast_event, forecast_scores, save_forecast
from .metrics import analyze_event, load_metrics, save_metrics
from .visualize import render_event_atlas, render_forecast
from .wikimedia import fetch_event, load_event_frame


def _selected_events(slug: str) -> list[Event]:
    catalog = load_catalog()
    return list(catalog.values()) if slug == "all" else [get_event(slug)]


def _print_metrics(metrics) -> None:
    print(f"\n{metrics.title} — {metrics.event_date}")
    print(f"60-day excess views: {metrics.total_excess_views_60d:,}")
    print(f"attention outside the primary page: {metrics.spillover_share:.1%}\n")
    print(f"{'page':24} {'peak':>8} {'lift':>9} {'half-life':>11}")
    print("-" * 56)
    for page in sorted(metrics.pages, key=lambda item: item.excess_views_60d, reverse=True):
        half_life = f"{page.half_life_days}d" if page.half_life_days is not None else "60+d"
        print(f"{page.label[:24]:24} {page.peak_offset_days:>+7}d {page.peak_lift:>8.1f}x {half_life:>11}")


def cmd_list(_: argparse.Namespace) -> None:
    for event in load_catalog().values():
        print(f"{event.slug:26} {event.date.isoformat()}  {event.title}")


def cmd_fetch(args: argparse.Namespace) -> None:
    for event in _selected_events(args.event):
        path = PROJECT_ROOT / "data" / "raw" / f"{event.slug}.csv"
        if path.exists() and not args.refresh:
            print(f"cached: {path.relative_to(PROJECT_ROOT)}")
            continue
        print(f"fetching {event.title} ({len(event.pages)} pages)...")
        frame = fetch_event(event, before=args.before, after=args.after)
        print(f"saved {len(frame):,} days × {len(frame.columns)} pages -> {path.relative_to(PROJECT_ROOT)}")


def cmd_analyze(args: argparse.Namespace) -> None:
    for event in _selected_events(args.event):
        frame = load_event_frame(event)
        metrics = analyze_event(frame, event)
        path = save_metrics(metrics)
        _print_metrics(metrics)
        print(f"\nmetrics -> {path.relative_to(PROJECT_ROOT)}")


def cmd_forecast(args: argparse.Namespace) -> None:
    events = _selected_events(args.event)
    print(f"loading TimesFM-3 on {args.device or 'auto'}...")
    backend = TimesFMBackend(device=args.device)
    for event in events:
        frame = load_event_frame(event)
        print(f"\nforecasting {event.title}...")
        forecast = forecast_event(
            frame,
            event,
            reveal_days=args.reveal_days,
            horizon=args.horizon,
            context_days=args.context,
            device=args.device,
            backend=backend,
        )
        path = save_forecast(forecast, event)
        print(forecast_scores(forecast).to_string(index=False, float_format=lambda value: f"{value:.3f}"))
        print(f"forecast -> {path.relative_to(PROJECT_ROOT)}")


def cmd_render(args: argparse.Namespace) -> None:
    for event in _selected_events(args.event):
        frame = load_event_frame(event)
        metrics_path = PROJECT_ROOT / "data" / "processed" / f"{event.slug}-metrics.json"
        if metrics_path.exists():
            metrics = load_metrics(event.slug)
        else:
            metrics = analyze_event(frame, event)
            save_metrics(metrics)
        atlas_path = render_event_atlas(frame, event, metrics)
        print(f"atlas -> {atlas_path.relative_to(PROJECT_ROOT)}")

        forecast_path = PROJECT_ROOT / "data" / "processed" / f"{event.slug}-forecast.csv"
        if forecast_path.exists():
            forecast = pd.read_csv(forecast_path)
            figure_path = render_forecast(frame, forecast, event)
            print(f"forecast figure -> {figure_path.relative_to(PROJECT_ROOT)}")


def cmd_build(args: argparse.Namespace) -> None:
    for event in _selected_events(args.event):
        raw_path = PROJECT_ROOT / "data" / "raw" / f"{event.slug}.csv"
        sample_path = PROJECT_ROOT / "data" / "sample" / f"{event.slug}.csv"
        if (not raw_path.exists() and not sample_path.exists()) or args.refresh:
            print(f"fetching {event.title}...")
            fetch_event(event, before=args.before, after=args.after)
        frame = load_event_frame(event)
        metrics = analyze_event(frame, event)
        save_metrics(metrics)
        figure = render_event_atlas(frame, event, metrics)
        _print_metrics(metrics)
        print(f"\natlas -> {figure.relative_to(PROJECT_ROOT)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="internet-half-life",
        description="Measure and forecast how Wikipedia attention spreads and fades.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    list_parser = commands.add_parser("list", help="list curated cultural events")
    list_parser.set_defaults(func=cmd_list)

    fetch_parser = commands.add_parser("fetch", help="download Wikimedia pageviews")
    fetch_parser.add_argument("--event", default="straight-outta-compton")
    fetch_parser.add_argument("--before", type=int, default=512)
    fetch_parser.add_argument("--after", type=int, default=90)
    fetch_parser.add_argument("--refresh", action="store_true")
    fetch_parser.set_defaults(func=cmd_fetch)

    analyze_parser = commands.add_parser("analyze", help="calculate attention half-lives")
    analyze_parser.add_argument("--event", default="straight-outta-compton")
    analyze_parser.set_defaults(func=cmd_analyze)

    forecast_parser = commands.add_parser("forecast", help="compare TimesFM-3 forecasting modes")
    forecast_parser.add_argument("--event", default="straight-outta-compton")
    forecast_parser.add_argument("--reveal-days", type=int, default=7)
    forecast_parser.add_argument("--horizon", type=int, default=30)
    forecast_parser.add_argument("--context", type=int, default=512)
    forecast_parser.add_argument("--device", choices=["cpu", "mps", "cuda"])
    forecast_parser.set_defaults(func=cmd_forecast)

    render_parser = commands.add_parser("render", help="render atlas and forecast figures")
    render_parser.add_argument("--event", default="straight-outta-compton")
    render_parser.set_defaults(func=cmd_render)

    build = commands.add_parser("build", help="fetch, analyze, and render one event")
    build.add_argument("--event", default="straight-outta-compton")
    build.add_argument("--before", type=int, default=512)
    build.add_argument("--after", type=int, default=90)
    build.add_argument("--refresh", action="store_true")
    build.set_defaults(func=cmd_build)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except (FileNotFoundError, KeyError, ValueError, RuntimeError) as error:
        parser.exit(2, f"error: {error}\n")
