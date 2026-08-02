# pran-tae.github.io

My personal site: one static page, no build step.

- `index.html` — the whole site.
- `scripts/refresh_feeds.py` — rewrites the "Recent flicks" shelf from my
  [Letterboxd RSS](https://letterboxd.com/term_2222/rss/) and the "Recent jams"
  deck from the Last.fm API, downloading poster and album art into `assets/`.
- `.github/workflows/refresh-feeds.yml` — runs that script daily (and on demand
  from the Actions tab). Needs a `LASTFM_API_KEY` repository secret; without it,
  the jams deck simply keeps its current record.

Any feed failure leaves the last good content in place — the site cannot break
from an upstream hiccup.
