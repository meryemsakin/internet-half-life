# Published data snapshot

This directory contains the inputs and saved outputs for the sixteen-event,
81-series study. These are 81 event–page assignments covering 80 unique
Wikipedia titles; Paris appears in two events.

| Location | Contents |
|---|---|
| `raw/<event>.csv` | Daily pageviews, one date row and one column per selected article |
| `processed/<event>-forecast.csv` | Actuals, point forecasts, and q10/q90 for all six methods |
| `processed/<event>-metrics.json` | Page metrics and descriptive lead/lag edges |
| `manifest.json` | Exact file hashes, date ranges, API filters, and analysis settings |
| `sample/` | Small standalone example retained for the quick start |

The aggregate tables and figures are in [`results/`](../results/) and
[`figures/`](../figures/). No model weights or reader-level data are included.

## Source and preparation

Counts come from the public Wikimedia
[per-article Pageviews API](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/reference/page-views.html),
using `en.wikipedia.org`, `all-access`, `user`, and `daily`. The `user` filter
excludes traffic identified by Wikimedia as automated; it is not a count of
unique people. Page choices and event dates are in
[`catalog/events.json`](../catalog/events.json).

The client fills absent API dates with zero and returns an empty series for a
404. Those zeros do not independently establish that a page had no readers:
page creation, title changes, redirects, and missing responses can matter. The
stored series do not reconcile historical titles or referral paths.

The older Straight Outta Compton CSV contains all-zero padding before the
API's 1 July 2015 coverage boundary. `load_event_frame` removes leading
all-zero rows before analysis. This leaves 44 pre-event days, so the requested
56-day baseline sensitivity uses 44 available days for that event; all events
have the full 28-day default baseline. Each sensitivity's actual baseline
length is recorded in the catalog result table.

The events and related pages were selected retrospectively by narrative
relevance, including subjects whose importance became clear later (for example,
the new pope). This is an exploratory atlas, not a prospectively specified
forecasting benchmark or a representative sample of internet attention.

## Definitions and missing results

The default baseline for page j is its median traffic on event days −28..−1,
floored at one view. Daily excess is `max(views - baseline, 0)`.

- The initial peak is the **first** maximum within event days 0..13.
- Page half-life is the first day after that peak starting a run of three
  consecutive days at or below half the peak excess. It need not stay there
  forever; later rebounds are allowed.
- Constellation half-life applies the same rule to the **sum of each page's
  clipped excess**, not to the primary page or the mean page half-life.
- The late-attention ratio is mean constellation excess on days 53..59 divided
  by the initial constellation peak. It is not a baseline ratio and does not
  establish a permanent new traffic level or complete forgetting.
- `half_life_status=not_observed` means no qualifying three-day run was seen by
  event day 59. Blank half-life values are never replaced with 60. Follow-up
  after the peak varies and is reported explicitly.
- `half_life_status=no_excess` means no positive initial spike above baseline;
  its half-life is undefined, not zero. Supply chain in the Ever Given group
  is the one such page in this snapshot.

All sixteen constellations and 80 responding page-series cross the threshold
under the default 14-day peak window. The remaining page has no excess. The
7-day sensitivity leaves ChatGPT's constellation crossing unobserved, while
14 and 21 days do not; the median of observed half-lives is two days in each
case. This sensitivity is not evidence of a universal decay constant.

## Forecasts and reproducibility

The saved forecasts reveal event days 0..7 and evaluate days 8..37, with up to
512 context days. This cutoff is unrelated to the retrospective 14-day peak
window used for descriptive metrics. No future peak enters a forecast fit.
Point-only baselines have blank q10/q90 fields.

The immutable model revision, original package/device versions, and exact API
fetch timestamps were not recorded. We do not reconstruct or invent them. The
checked-in predictions and SHA-256 manifest allow exact rescoring; fresh model
runs or API fetches may differ. New model runs should record this provenance.

From the repository root, after `make setup`:

```bash
.venv/bin/python scripts/data_manifest.py --check
.venv/bin/python -m internet_half_life analyze --event all
.venv/bin/python -m internet_half_life study
make test
```

These commands do not call the API or load TimesFM. To deliberately refresh
source data, use `fetch --event all --refresh`; to rerun inference, install the
optional TimesFM dependencies and run `forecast --event all`. Both overwrite
the corresponding local snapshots, so review the resulting Git diff before
running `scripts/data_manifest.py` to record a new snapshot.

## Reuse and attribution

Attribute the source counts to Wikimedia Pageviews and cite this repository's
catalog and method when using its event groupings. Refer to Wikimedia's
[API documentation](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/reference/page-views.html)
and [terms](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use) for the source service.

The repository's MIT license covers its original code; it does not override
third-party terms. The saved TimesFM predictions are research outputs produced
with Google's checkpoint. Its
[TimesFM Non-Commercial License](https://huggingface.co/google/timesfm-3.0-pytorch/blob/main/LICENSE)
restricts commercial/production use, including use of outputs. Model weights
and Google inference code are not redistributed here. Check those terms before
reusing model-derived results beyond non-commercial research.
