"""Fast, cached Spotify lookups for tracks and artists.

Looking things up one at a time was the slow part of every request: each call is a
round trip of ~100-200 ms. Here:
  * tracks are fetched up to 50 per request with sp.tracks(),
  * artist searches (which can't be batched) run in parallel,
  * every answer is remembered in memory and in spotify_lookup_cache.json,
    so a song or artist is only ever looked up once.
"""
import json
import threading
from concurrent.futures import ThreadPoolExecutor

LOOKUP_CACHE_FILE = "spotify_lookup_cache.json"
TRACKS_PER_REQUEST = 50  # Spotify's limit for GET /tracks
SEARCH_WORKERS = 8

_lock = threading.Lock()
_cache = None  # {"tracks": {uri: {...}}, "artists": {name: {...}}}


def _load_cache():
    global _cache
    if _cache is None:
        try:
            with open(LOOKUP_CACHE_FILE, encoding="utf-8") as f:
                _cache = json.load(f)
        except (OSError, ValueError):
            _cache = {}
        _cache.setdefault("tracks", {})
        _cache.setdefault("artists", {})
    return _cache


def _save_cache():
    """Write the cache, keeping entries another process (e.g. the CLI while the web
    app is running) saved since we loaded it, so neither overwrites the other."""
    try:
        with open(LOOKUP_CACHE_FILE, encoding="utf-8") as f:
            on_disk = json.load(f)
        for section in ("tracks", "artists"):
            for key, value in on_disk.get(section, {}).items():
                _cache[section].setdefault(key, value)
    except (OSError, ValueError):
        pass  # nothing saved yet, or unreadable: just write ours
    try:
        with open(LOOKUP_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_cache, f)
    except OSError as error:
        print(f"Couldn't save {LOOKUP_CACHE_FILE}: {error}")


def track_details(sp, uris):
    """{track uri: {"cover": url or None, "album_uri": uri}} for the given track URIs.

    Unknown URIs are fetched in batches of 50; missing/None URIs are left out.
    """
    wanted = [uri for uri in dict.fromkeys(uris) if uri]  # unique, keeps order
    with _lock:
        cache = _load_cache()["tracks"]
        missing = [uri for uri in wanted if uri not in cache]
    if missing:
        found = {}
        for start in range(0, len(missing), TRACKS_PER_REQUEST):
            batch = missing[start:start + TRACKS_PER_REQUEST]
            for uri, track in zip(batch, sp.tracks(batch)["tracks"]):
                if track is None:  # track no longer on Spotify
                    found[uri] = {"cover": None, "album_uri": None}
                    continue
                images = track["album"]["images"]
                found[uri] = {
                    "cover": images[0]["url"] if images else None,  # highest resolution
                    "album_uri": track["album"]["uri"],
                }
        with _lock:
            cache.update(found)
            _save_cache()
    return {uri: cache[uri] for uri in wanted}


def _search_artist(sp, name):
    results = sp.search(q=f"artist:{name}", type="artist", limit=1)
    items = results["artists"]["items"]
    if not items:
        return {"image": None, "uri": None}
    images = items[0]["images"]
    return {"image": images[0]["url"] if images else None, "uri": items[0]["uri"]}


def artist_details(sp, names):
    """{artist name: {"image": url or None, "uri": uri or None}}, searching in parallel."""
    wanted = list(dict.fromkeys(names))
    with _lock:
        cache = _load_cache()["artists"]
        missing = [name for name in wanted if name not in cache]
    if missing:
        with ThreadPoolExecutor(max_workers=SEARCH_WORKERS) as pool:
            found = dict(zip(missing, pool.map(lambda name: _search_artist(sp, name), missing)))
        with _lock:
            cache.update(found)
            _save_cache()
    return {name: cache[name] for name in wanted}
