import argparse
import glob
import json
import os
from collections import Counter

try:
    import orjson  # roughly twice as fast as json for the big history files
except ImportError:
    orjson = None

import pandas as pd
from dateutil.parser import parse
from matplotlib import pyplot as plt

from main import (average_image, cover_to_rgb, create_playlist, create_spotify_client,
                  download_covers, url_to_image)
from spotify_lookup import track_details

# Every folder whose name starts with this is read, so a second export
# (e.g. "Spotify Extended Streaming History 2") is included automatically.
HISTORY_DIR_PREFIX = "Spotify Extended Streaming History"
# Spotify only counts a play as a stream once it passes 30 seconds.
MIN_STREAM_MS = 30_000
# Cleaned streams are saved here after the first load, so later runs skip the JSON.
CACHE_FILE = "history_cache.parquet"
CACHE_INFO_FILE = "history_cache.json"
# Bump this whenever the cleaning rules in _parse_history change, to force a rebuild.
CACHE_VERSION = 1
STREAM_COLUMNS = ["ts", "song", "album", "artist", "uri"]


def history_files():
    """All audio and video streaming-history JSON files, across every export folder."""
    files = glob.glob(os.path.join(f"{HISTORY_DIR_PREFIX}*", "Streaming_History_*.json"))
    return sorted(f for f in files if os.path.basename(f).startswith(("Streaming_History_Audio",
                                                                       "Streaming_History_Video")))


def available_years():
    """Years that appear in the history file names, e.g. [2013, 2014, ..., 2026]."""
    years = set()
    for path in history_files():
        for part in os.path.basename(path).removesuffix(".json").split("_"):
            # handles both "..._2018.json" and "..._2018-2020_1.json"
            for piece in part.split("-"):
                if len(piece) == 4 and piece.isdigit():
                    years.add(int(piece))
    return sorted(years)


def _read_json(path):
    if orjson is not None:
        with open(path, "rb") as json_file:
            return orjson.loads(json_file.read())
    with open(path, encoding="utf-8") as json_file:
        return json.load(json_file)


def _parse_history(files):
    """Parse the raw export into a DataFrame of counted streams, oldest first.

    Plays shorter than 30 seconds, podcasts, audiobooks and unknown tracks are dropped.
    """
    records = []
    for path in files:
        for stream in _read_json(path):
            song = stream.get("master_metadata_track_name")
            artist = stream.get("master_metadata_album_artist_name")
            album = stream.get("master_metadata_album_album_name")
            if song is None or artist is None or album is None:
                continue  # podcasts, audiobooks and unknown tracks
            if (stream.get("ms_played") or 0) < MIN_STREAM_MS:
                continue  # skipped before it counted as a stream
            records.append((stream["ts"], song, album, artist, stream.get("spotify_track_uri")))
    records.sort()  # timestamps are ISO 8601, so text order is time order
    return pd.DataFrame.from_records(records, columns=STREAM_COLUMNS)


def _history_signature(files):
    """Identifies the current export: each file's name, size and modified time,
    plus the cleaning rules. If any of it changes, the cache is rebuilt."""
    return {
        "version": CACHE_VERSION,
        "min_stream_ms": MIN_STREAM_MS,
        "files": [[path, os.path.getsize(path), os.path.getmtime(path)] for path in files],
    }


_loaded = {"signature": None, "history": None}  # in-memory copy, reused while the files are unchanged


def load_history():
    """All counted streams as a DataFrame (columns: ts, song, album, artist, uri), oldest first.

    Order of preference: the copy already in memory, then the Parquet cache on disk,
    then parsing the JSON export (which also refreshes the cache). Any change to the
    export files rebuilds the cache automatically.
    """
    files = history_files()
    if not files:
        raise FileNotFoundError(
            f"No Streaming_History_*.json files found in a '{HISTORY_DIR_PREFIX}' folder. "
            "Extract your Spotify data export into this directory first."
        )
    signature = _history_signature(files)
    if _loaded["signature"] == signature:
        return _loaded["history"]

    history = None
    try:
        with open(CACHE_INFO_FILE, encoding="utf-8") as info:
            if json.load(info) == signature:
                history = pd.read_parquet(CACHE_FILE)
    except (OSError, ValueError):
        history = None  # no cache yet, or it's unreadable: rebuild below

    if history is None:
        print("Reading streaming history files (first run or export changed)...")
        history = _parse_history(files)
        try:
            history.to_parquet(CACHE_FILE, index=False)
            with open(CACHE_INFO_FILE, "w", encoding="utf-8") as info:
                json.dump(signature, info)
        except (OSError, ImportError) as error:
            print(f"Couldn't save the history cache ({error}); it will be re-read next time.")

    _loaded["signature"], _loaded["history"] = signature, history
    return history


def readInStreams(year, ignore=None):
    """Load every stream from the export, optionally for one year only.

    year: a year (int or str) or "all". Filtering uses each stream's own timestamp,
    so it doesn't matter which file a stream happens to be stored in.
    ignore: artist names to leave out (case-insensitive).
    Plays shorter than 30 seconds are skipped, matching how Spotify counts streams.
    Streams are returned oldest first.
    """
    history = load_history()
    year = str(year)
    if year != "all":
        history = history[history["ts"].str.startswith(year)]
    ignored = {name.casefold() for name in (ignore or [])}
    if ignored:
        history = history[~history["artist"].str.casefold().isin(ignored)]

    uris = history["uri"].astype(object)
    streams = {
        "song": history["song"].tolist(),
        "album": history["album"].tolist(),
        "artist": history["artist"].tolist(),
        "uri": uris.where(uris.notna(), None).tolist(),  # missing URIs stay None
        "date": history["ts"].tolist(),
    }
    song_pairs = list(zip(streams["song"], streams["artist"], streams["uri"]))
    album_pairs = list(zip(streams["album"], streams["artist"], streams["uri"]))
    return streams, song_pairs, streams["artist"], album_pairs


def _latest_uris(items):
    """Map (name, artist) -> the most recent track URI seen for it (skipping missing ones)."""
    uri_map = {}
    for name, artist, uri in items:
        if uri:
            uri_map[(name, artist)] = uri
    return uri_map


def _bar_chart(rows, columns, x, title, xlabel):
    """Bar chart of stream counts (not shown; call plt.show() to display it)."""
    df = pd.DataFrame(rows, columns=columns)
    df.plot.bar(x=x, y="count", legend=False, figsize=(20, 10))
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("Streams")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    #plt.show()


def topArtists(artists, range, plot=True):
    top_list = Counter(artists).most_common(range)
    topArtistsList = []
    for artist, count in top_list:
        print(artist, count)
        topArtistsList.append((artist, count))
    if plot:
        _bar_chart(top_list, ["artist", "count"], "artist", "Top Artists", "Artist")
    return topArtistsList


def topSongs(songs, range, year, sp, make_cover=True, plot=True):
    """Top songs by stream count.

    Returns ([((song, artist, uri), count), ...], average cover image or None).
    make_cover=False skips downloading the covers (the image is only needed for a playlist
    cover), which saves most of the time when you just want the list.
    """
    uri_map = _latest_uris(songs)
    top_list = Counter((song, artist) for song, artist, _ in songs).most_common(range)
    result = [((song, artist, uri_map.get((song, artist))), count) for (song, artist), count in top_list]

    print("---- Top Songs ----")
    for position, ((song, artist), count) in enumerate(top_list, start=1):
        print(position, song, count)

    outputImage = None
    if make_cover:
        details = track_details(sp, [uri for (_, _, uri), _ in result])  # one request per 50 songs
        urls = [details[uri]["cover"] for (_, _, uri), _ in result
                if uri in details and details[uri]["cover"]]
        if urls:
            outputImage = average_image([cover_to_rgb(img) for img in download_covers(urls)])
            outputImage.save("Top Song Average New.jpg")  # save the image as a jpg

    if plot:
        _bar_chart([(song, artist, count) for (song, artist), count in top_list],
                   ["song", "artist", "count"], "song", "Top Songs", "Song")
    return result, outputImage


def topAlbum(albums, range, sp, plot=True):
    """Top albums by stream count. Returns [((album, artist, a track uri), count), ...]."""
    uri_map = _latest_uris(albums)
    top_list = Counter((album, artist) for album, artist, _ in albums).most_common(range)

    print("---- Top Albums ----")
    for position, ((album, artist), count) in enumerate(top_list, start=1):
        print(position, album, count)
    if plot:
        _bar_chart([(album, artist, count) for (album, artist), count in top_list],
                   ["album", "artist", "count"], "album", "Top Albums", "Album")
    return [((album, artist, uri_map.get((album, artist))), count) for (album, artist), count in top_list]


def firstTimePlayed(streams, song, artist):
    """Earliest stream of a song, as (datetime, song, artist), or None if never played.

    Expects streams from readInStreams, which are sorted oldest first.
    """
    song, artist = song.casefold(), artist.casefold()
    for date, s, a in zip(streams["date"], streams["song"], streams["artist"]):
        if s.casefold() == song and a.casefold() == artist:
            return parse(date), s, a
    return None


def main():
    years = available_years()
    parser = argparse.ArgumentParser(description="See your top songs of a year.")
    parser.add_argument(
        "-t",
        "--type",
        metavar="type",
        choices=["artists", "songs", "albums"],
        default="songs",
        help="Whether to show top songs, top artists, or top albums (default: songs)"
    )
    parser.add_argument(
        "-y",
        "--year",
        metavar="year",
        choices=[str(y) for y in years] + ["all"],
        default="all",
        help=f"Year to check ({years[0] if years else '?'}-{years[-1] if years else '?'}, "
             "or 'all'; default: all)",
    )
    parser.add_argument(
        "-r",
        "--range",
        metavar="range",
        default=10,
        help="Number of items to show (default: 10)",
        type=int
    )
    parser.add_argument(
        "-p",
        "--playlist",
        action="store_true",
        help="Create a playlist of your top songs",
    )
    parser.add_argument(
        "-f",
        "--first_played",
        metavar=("SONG", "ARTIST"),
        nargs=2,
        default=None,
        help="Show when you first played a song, e.g. -f \"august\" \"Taylor Swift\"",
    )
    parser.add_argument(
        "-i",
        "--ignore",
        metavar="artist",
        nargs="+",
        default=[],
        help="Artists to leave out of top songs/albums/artists",
    )
    args = parser.parse_args()
    sp = create_spotify_client()

    streams, song_pairs, artists, albums = readInStreams(args.year, ignore=args.ignore)
    if args.first_played is not None:
        # first play is across your whole history, whatever --year is
        all_streams = streams if args.year == "all" else readInStreams("all")[0]
        first = firstTimePlayed(all_streams, *args.first_played)
        if first is None:
            print(f"{args.first_played[0]} by {args.first_played[1]} - never played")
        else:
            date, song, artist = first
            print(f"{song} by {artist} - First Played: {date}")
    match args.type:
        case "artists":
            topArtists(artists, args.range)
        case "songs":
            topSongList, outputImage = topSongs(song_pairs, args.range, args.year, sp)
            if args.playlist:
                uris = [uri for (_, _, uri), _ in topSongList if uri]
                create_playlist(sp, uris, outputImage, args.range, args.year)
        case "albums":
            topAlbum(albums, args.range, sp)


if __name__ == "__main__":
    main()
