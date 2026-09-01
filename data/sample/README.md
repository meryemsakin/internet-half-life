# Sample data

`straight-outta-compton.csv` contains daily English Wikipedia pageviews from
1 July through 12 November 2015 for the five pages in the Straight Outta
Compton event universe.

The file is a small, reproducible fixture generated from Wikimedia's public
[per-article Pageviews API](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/reference/page-views.html)
using the `all-access` and `user` filters. Recognized automated traffic is
therefore excluded. The checked-in sample lets the atlas render without making
network requests; `internet-half-life fetch` regenerates page-level data from
the source API.

Pageviews are aggregate counts. The sample contains no user-level or personal
data.

