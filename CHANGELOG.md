# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Six post-cutoff cultural events, expanding the catalog to sixteen cases.
- An exact pre/post comparison around TimesFM-3's published November 2023
  Wikipedia Pageviews training cutoff.
- A zero-parameter return-to-baseline forecast.
- Fourteen-day related-page peak offsets and a catalog-level timing figure.
- Sensitivity checks for the pre-event window and zero-traffic baseline floor.
- Median page-level WAPE as a robustness check on pooled event-level error.
- Constellation-level half-lives and day-53–59 retained attention, with a
  per-event figure and 7/14/21-day peak-window sensitivity.
- Event-level median peak-offset sign test, respecting within-event clustering.
- Full source CSVs, saved forecasts, page metrics, a SHA-256 snapshot manifest,
  and offline regression checks linking published results to those inputs.
- Page-level error contributions identifying the Ever Given overprediction.
- Literature references and explicit data/provenance and model-output terms.

### Changed

- Reframed outside-page attention as a descriptive property of the manually
  curated constellations, not evidence of page-to-page diffusion.
- Restricted descriptive peak search to event days 0–13 rather than the whole
  60-day window. Later surges no longer replace the initial peak. This changes
  affected page half-lives but not the recorded model forecasts.
- Separated no-excess and unobserved half-lives from observed crossings; neither
  is displayed as zero or as an invented 60-day observation.
- Fixed the forecast renderer to support the flat baseline and removed
  page-to-page travel language from the descriptive network figure.

### Removed

- The Turkish publication draft, keeping editorial work outside the code repository.

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
