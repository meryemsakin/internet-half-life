# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-09-01

### Added

- Two-parameter exponential and power-law attention-decay baselines.
- A paired evaluation across all ten catalog events, with exact tests.
- Checked-in cross-event results and spillover, model, delta, and interval figures.
- Interval sharpness diagnostics alongside 10th–90th percentile coverage.
- A Barbenheimer hero case and a result-first rewrite of the Turkish article.

### Changed

- Reframed the project around attention dispersal before forecasting.
- Left interval coverage blank for point-only baselines.
- Reused one TimesFM backend across full-catalog forecasts.
- Respected Wikimedia's July 2015 Pageviews coverage boundary.
- Upgraded the GitHub Actions runtime to the current Node 24-based releases.

## [0.1.0] - 2026-09-01

### Added

- A curated catalog of ten pop-culture and public-attention events.
- A cached Wikimedia Pageviews data pipeline.
- Peak lift, sustained attention half-life, spillover, and lead/lag metrics.
- A reproducible Straight Outta Compton sample dataset and atlas.
- TimesFM-3 multivariate, univariate, and weekly-naive forecast comparisons.
- Publication-ready atlas and forecast figures.
- A Turkish Medium draft containing the first case-study results.
- Tests on Python 3.10, 3.12, and 3.13 through GitHub Actions.

[Unreleased]: https://github.com/meryemsakin/internet-half-life/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/meryemsakin/internet-half-life/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/meryemsakin/internet-half-life/releases/tag/v0.1.0
