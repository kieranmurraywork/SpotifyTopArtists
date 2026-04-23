import json
import os
from pprint import pprint

import pykx
from matplotlib import pyplot as plt
from pykx.toq import from_list
import pandas as pd
from collections import Counter
def topArtists(artists, range):
    return Counter(artists).most_common(range)
def topSongs(songs, range):
    return Counter(songs).most_common(range)
def topAlbum(albums, range):
    return Counter(albums).most_common(range)
def main():
    from argparse import ArgumentParser

    parser = ArgumentParser(description="See your top songs of a year.")
    parser.add_argument(
        "-t",
        "--type",
        metavar="type",
        choices=["artists", "songs", "albums"],
        default="songs",
        help="Whether to show top songs, top artists, or top albums."
    )
    parser.add_argument(
        "-y",
        "--year",
        metavar="year",
        choices=["2014","2015","2016","2017","2018","2019","2020","2021","2022","2023","2024","2025","2026","all"],
        default="all",
        help="Year to check top songs (default: 2026)",
    )
    parser.add_argument(
        "-r",
        "--range",
        metavar="range",
        default=10,
        help="Number of items to show (default: 10)",
        type=int
    )
    args = parser.parse_args()
    selected_year: int = args.year
    selected_type: str = args.type
    selected_range: int = args.range
    directory = "Streaming History/Spotify Extended Streaming History"
    data = []
    artists = []
    songs = []
    albums = []
    for filename in os.listdir(directory):
        if selected_year != "all":
            if filename.endswith(".json") and str(selected_year) in filename:
                with open(os.path.join(directory, filename), encoding='utf-8') as json_file:
                    data.append(json.load(json_file))
        else:
            if filename.endswith(".json"):
                with open(os.path.join(directory, filename), encoding='utf-8') as json_file:
                    data.append(json.load(json_file))
    streams = {
        "song": [],
        "album": [],
        "artist": [],
        "uri": []
    }
    for entry in data:
        for stream in entry:
            if stream['master_metadata_track_name'] == None or stream['master_metadata_album_artist_name'] == None or stream['master_metadata_album_album_name']== None:
                continue
            artists.append(stream['master_metadata_album_artist_name'])
            songs.append(stream['master_metadata_track_name'])
            albums.append(stream['master_metadata_album_album_name'])
            streams['song'].append(stream['master_metadata_track_name'])
            streams['album'].append(stream['master_metadata_album_album_name'])
            streams['artist'].append(stream['master_metadata_album_artist_name'])
            streams['uri'].append(stream['spotify_track_uri'])
    song_pairs = list(zip(streams["song"], streams["artist"]))
    if selected_type == "artists":
        print("---- Top Artists ----")
        top_list = topArtists(streams['artist'],selected_range)
        for artist, count in top_list:
            print(artist, count)
        df = pd.DataFrame(top_list, columns=["artist", "count"])
        df.plot.bar(x="artist", y="count", legend=False, figsize=(20, 10))
        plt.title("Top Artists")
        plt.xlabel("Artist")
        plt.ylabel("Streams")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.show()

    if selected_type == "songs":
        print("---- Top Songs ----")
        top_list = topSongs(song_pairs,selected_range)
        for song,count in top_list:
            print(song[0], count)
        df = pd.DataFrame(
            [(song, artist, count) for (song, artist), count in top_list],
            columns=["song", "artist", "count"]
        )
        df.plot.bar(x="song", y="count", legend=False, figsize=(20, 10))
        plt.title("Top Songs")
        plt.xlabel("Song")
        plt.ylabel("Streams")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.show()

    if selected_type == "albums":
        print("---- Top Albums ----")
        top_list = topAlbum(streams['album'],selected_range)
        for album, count in top_list:
            print(album, count)
        df = pd.DataFrame(top_list, columns=["album", "count"])
        df.plot.bar(x="album", y="count", legend=False, figsize=(20, 10))
        plt.title("Top Albums")
        plt.xlabel("Album")
        plt.ylabel("Streams")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.show()
if __name__ == "__main__":
    main()