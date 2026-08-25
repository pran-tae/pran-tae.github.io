# pran-tae.github.io

My personal site

- `index.html` - the site.
- `scripts/refresh_feeds.py` - rewrites the "Recent flicks" shelf from my
  [Letterboxd RSS](https://letterboxd.com/term_2222/rss/) and the "Recent jams"
  deck from the Last.fm API, downloading poster and album art into `assets/`.
- `.github/workflows/refresh-feeds.yml` — runs that script daily (and on demand
  from the Actions tab).
