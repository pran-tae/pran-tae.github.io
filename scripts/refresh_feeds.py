#!/usr/bin/env python3
"""Refresh the Recent flicks shelf (Letterboxd RSS) and Recent jams deck
(Last.fm API) in index.html. Safe by design: any fetch failure leaves the
current content in place and exits 0."""

import hashlib
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.join(os.path.dirname(__file__), "..")
INDEX = os.path.join(ROOT, "index.html")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) term-site-feed-refresh"

LETTERBOXD_USER = "term_2222"
LASTFM_USER = "term22"
SHELF_SIZE = 8


def fetch(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
    except urllib.error.HTTPError as e:
        detail = e.read()[:200].decode("utf-8", "replace")
        raise RuntimeError(f"HTTP {e.code} from {url.split('?')[0]}: {detail}") from None
    return data if binary else data.decode("utf-8", "replace")


def stars(rating):
    r = float(rating)
    return "★" * int(r) + ("½" if r % 1 else "")


def replace_block(text, start_marker, end_marker, new_inner):
    pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.S)
    if not pattern.search(text):
        raise RuntimeError(f"marker {start_marker} not found")
    return pattern.sub(start_marker + new_inner + end_marker, text)


def refresh_flicks(index):
    rss = fetch(f"https://letterboxd.com/{LETTERBOXD_USER}/rss/")
    items = re.findall(r"<item>(.*?)</item>", rss, re.S)
    films = []
    for it in items:
        title = re.search(r"<letterboxd:filmTitle>(.*?)</letterboxd:filmTitle>", it)
        rating = re.search(r"<letterboxd:memberRating>(.*?)</letterboxd:memberRating>", it)
        link = re.search(r"<link>(.*?)</link>", it)
        poster = re.search(r'src="(https://a\.ltrbxd\.com/resized/[^"]+\.jpg[^"]*)"', it)
        if title and link and poster:
            films.append({
                "title": html.unescape(title.group(1)),
                "stars": stars(rating.group(1)) if rating else "",
                "link": link.group(1),
                "poster": poster.group(1),
            })
        if len(films) == SHELF_SIZE:
            break
    if not films:
        raise RuntimeError("no films parsed from RSS")

    lines = []
    for n, f in enumerate(films):
        path = f"assets/posters/p{n + 1}.jpg"
        data = fetch(f["poster"], binary=True)
        with open(os.path.join(ROOT, path), "wb") as fh:
            fh.write(data)
        path += "?v=" + hashlib.md5(data).hexdigest()[:8]
        t = html.escape(f["title"], quote=True)
        lines.append(
            f'        <a class="case" style="--n:{n};--z:{SHELF_SIZE - n}" href="{f["link"]}" '
            f'data-title="{t}" data-stars="{f["stars"]}" target="_blank" rel="noopener">'
            f'<img src="{path}" alt="{t} poster"></a>'
        )
    return replace_block(index, "<!-- SHELF:START -->", "<!-- SHELF:END -->", "\n" + "\n".join(lines) + "\n")


def refresh_jams(index):
    key = os.environ.get("LASTFM_API_KEY", "").strip()
    if not key:
        print("jams: LASTFM_API_KEY not set, leaving deck unchanged")
        return index
    q = urllib.parse.urlencode({
        "method": "user.getrecenttracks", "user": LASTFM_USER,
        "api_key": key, "format": "json", "limit": 1,
    })
    data = json.loads(fetch(f"https://ws.audioscrobbler.com/2.0/?{q}"))
    tracks = data.get("recenttracks", {}).get("track", [])
    if not tracks:
        print("jams: no scrobbles yet, leaving deck unchanged")
        return index
    t = tracks[0] if isinstance(tracks, list) else tracks
    name = html.escape(t["name"], quote=True)
    artist = html.escape(t["artist"]["#text"], quote=True)
    url = html.escape(t.get("url", f"https://www.last.fm/user/{LASTFM_USER}"), quote=True)
    label_tag = re.compile(r'<div class="disc-label[^"]*" style="background-image:[^"]*">')
    images = [i["#text"] for i in t.get("image", []) if i.get("#text")]
    if images:
        art = fetch(images[-1], binary=True)
        with open(os.path.join(ROOT, "assets/album.jpg"), "wb") as fh:
            fh.write(art)
        v = hashlib.md5(art).hexdigest()[:8]
        index = label_tag.sub(
            f'<div class="disc-label" style="background-image:url(\'assets/album.jpg?v={v}\')">', index)
    else:
        # no artwork for this track: fall back to the imprint label
        index = label_tag.sub('<div class="disc-label default" style="background-image:none">', index)

    index = replace_block(
        index, "<!-- JAM:START -->", "<!-- JAM:END -->",
        f'\n          <p class="track">{name}</p>\n          <p class="artist">{artist}</p>\n',
    )
    return index


def main():
    with open(INDEX) as f:
        index = f.read()
    for job in (refresh_flicks, refresh_jams):
        try:
            index = job(index)
            print(f"{job.__name__}: ok")
        except Exception as e:  # keep the site alive over feed hiccups
            print(f"{job.__name__}: skipped ({e})", file=sys.stderr)
    with open(INDEX, "w") as f:
        f.write(index)


if __name__ == "__main__":
    main()
