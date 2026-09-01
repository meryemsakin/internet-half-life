# Internet Half-Life

[![tests](https://github.com/meryemsakin/internet-half-life/actions/workflows/ci.yml/badge.svg)](https://github.com/meryemsakin/internet-half-life/actions/workflows/ci.yml)
[![Python 3.10–3.13](https://img.shields.io/badge/python-3.10%E2%80%933.13-3776AB)](https://www.python.org/)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**How many days does it take the internet to forget something?**

The first answer is that it often does something else: it disperses.

Internet Half-Life follows ten cultural events through constellations of
related English Wikipedia pages. Across this deliberately selected catalog,
the pages received **96.6 million views above their ordinary-day baselines** in
the first 60 days. A traffic-weighted **77.5% of that excess landed outside the
page chosen to represent the event**.

For Barbenheimer, the share was **97.8%**. People did not stay on the page for
the portmanteau. They moved toward the films, actors, J. Robert Oppenheimer,
and the Manhattan Project.

![The Barbenheimer attention atlas](figures/barbenheimer-atlas.png)

This repository makes that dispersal visible, measures how it fades, and then
asks a harder question: can TimesFM-3 predict it?

## What the atlas measures

Each event is a dated set of related pages: a primary event page plus people,
works, places, organizations, objects, and ideas. For every page, the project
calculates:

- **Ordinary-day traffic:** the median of the 28 days immediately before the
  event. A one-view floor avoids division by zero for newly created pages.
- **Peak lift:** peak traffic divided by ordinary-day traffic. Atlas timelines
  use a logarithmic scale so a new or previously dormant page does not flatten
  every other series.
- **Attention half-life:** the first day after the peak when excess traffic
  stays below half its peak excess for three consecutive days.
- **Spillover:** the share of 60-day excess traffic outside the primary page.
- **Lead/lag co-movement:** the strongest timing relationships between pages.
  These edges are descriptive, never causal.

![Spillover across the ten selected events](figures/catalog-spillover.png)

The catalog is small on purpose. Its ten events were hand-picked because they
produced visible attention shocks; it is an atlas of interesting cases, not a
representative sample of everything that happened online. The **77.5%** result
is conditional on those event and page choices.

## The forecasting test

[TimesFM-3](https://www.research.google/blog/timesfm-3-a-zero-shot-foundation-model-for-multivariate-forecasting/)
is natively pretrained for multivariate forecasting. That makes the page
constellation part of the experiment rather than decoration:

> After observing the event day and the following seven days, do related pages
> help forecast the next 30 days?

Every event uses the same cutoff and is forecast five ways:

1. TimesFM-3 with all pages modeled jointly.
2. TimesFM-3 with each page modeled independently.
3. A two-parameter exponential decay fitted after the revealed peak.
4. A two-parameter power-law decay fitted after the revealed peak.
5. A weekly seasonal-naive forecast.

The decay curves share the same fixed 28-day median baseline used by the atlas.
They are the obvious null models for a project about fading attention; the
weekly naive remains as a deliberately simple seasonal reference.

### What happened across all ten events

| model | median event WAPE ↓ |
|---|---:|
| TimesFM-3 multivariate | **0.261** |
| TimesFM-3 univariate | 0.286 |
| exponential decay | 0.472 |
| power-law decay | 0.439 |
| weekly naive | 5.008 |

The median alone makes the multivariate model look convincing. The paired
event-level result does not. Multivariate TimesFM won six events and lost four;
the median multivariate-minus-univariate difference was only **−0.004 WAPE**.
An exact two-sided sign test gives **p = 0.754**. With ten selected events, the
data do not distinguish the multivariate gain from zero.

![Multivariate minus univariate WAPE for every event](figures/multivariate-delta-by-event.png)

The simple baselines matter, too. In **five of ten events**, at least one of the
two parametric decay curves beat both TimesFM modes. On Straight Outta Compton,
for example, power-law decay scored **0.234 WAPE**, versus **0.248** for
multivariate TimesFM. A 330M-parameter foundation model can still lose to a
two-parameter description of the process being forecast.

![Forecast model comparison](figures/forecast-model-comparison.png)

Barbenheimer shows the opposite case: multivariate TimesFM scored **0.246**,
univariate TimesFM **0.269**, exponential decay **0.411**, and power-law decay
**0.475**.

![Barbenheimer forecast comparison](figures/barbenheimer-forecast.png)

## Coverage is not enough

TimesFM returns 10th–90th percentile intervals. A calibrated nominal 80%
interval should cover roughly 80% of observations over repeated cases. Across
the ten events, mean event-level coverage was **88.9%** for multivariate and
**88.1%** for univariate TimesFM. Some events reached 100%; Chandrayaan-3 fell
to 57.3% in the multivariate run.

High coverage was often purchased with broad bands. The median interval width
was **2.26 times mean actual traffic** for multivariate and **2.04 times** for
univariate forecasts. The maximum event-level ratio reached 59.2. Coverage is
therefore reported beside sharpness, not as a standalone success metric.
Point-only baselines have no interval and are left blank rather than assigned a
misleading zero.

![Coverage and relative interval width](figures/interval-calibration.png)

The checked-in [event table](results/catalog-study.csv) and
[machine-readable summary](results/study-summary.json) contain the exact
results behind these figures.

## Reproduce it

The atlas does not require model weights:

```bash
make setup
make sample
```

This renders the checked-in Straight Outta Compton sample without a network
request. To rebuild Barbenheimer or another event from Wikimedia:

```bash
.venv/bin/internet-half-life fetch --event barbenheimer
.venv/bin/internet-half-life analyze --event barbenheimer
.venv/bin/internet-half-life render --event barbenheimer
```

To reproduce the full forecasting study:

```bash
make setup-timesfm
.venv/bin/internet-half-life fetch --event all
.venv/bin/internet-half-life analyze --event all
.venv/bin/internet-half-life forecast --event all
.venv/bin/internet-half-life study
```

The first model run downloads the TimesFM-3 checkpoint. API responses and raw
page-level CSVs are cached locally. The public Pageviews API begins on 1 July
2015; the loader explicitly removes unavailable leading dates instead of
mistaking them for zero traffic.

## Add an event

```bash
internet-half-life list
```

The included universes are Barbenheimer, Straight Outta Compton, ChatGPT's
launch, James Webb's first images, Ever Given, the 2022 World Cup final,
Chandrayaan-3, the first GTA VI trailer, the 2024 total solar eclipse, and
Inside Out 2. Add another by editing [`catalog/events.json`](catalog/events.json);
the analysis code does not need to change.

## Interpretation and licensing

Daily traffic comes from Wikimedia's public
[Pageviews API](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/reference/page-views.html)
with recognized automated traffic excluded. Pageviews are not people,
approval, sentiment, or the whole internet. Search engines, news placement,
redirects, page creation dates, and editorial choices all affect the series.

TimesFM source code and weights do not share the same terms. The source
repository is Apache-2.0, while the TimesFM-3.0 checkpoint used here is under
Google's separate
[non-commercial, non-production license](https://huggingface.co/google/timesfm-3.0-pytorch/blob/main/LICENSE).
Review those terms before running or publishing model-derived work.

## Project layout

```text
catalog/events.json                    curated event universes
src/internet_half_life/wikimedia.py   cached Pageviews client
src/internet_half_life/metrics.py     half-life and spillover metrics
src/internet_half_life/forecasting.py TimesFM and decay baselines
src/internet_half_life/study.py       paired cross-event evaluation
src/internet_half_life/visualize.py   publication-ready figures
results/                              checked-in aggregate results
article/medium-tr.md                  Turkish article draft
tests/                                deterministic unit tests
```

The interesting cases are often the ones that refuse to decay cleanly.
