import json
import os
import cv2
import numpy as np
from PIL import Image
from main import create_spotify_client, url_to_image, create_playlist
from matplotlib import pyplot as plt
import pandas as pd
from collections import Counter

def readInStreams(year): # function to open the Streaming_History_Audio_* files,
    directory = "Spotify Extended Streaming History"
    data = []
    artists = []
    songs = []
    albums = []
    for filename in os.listdir(directory):
        if year != "all":
            if filename.endswith(".json") and str(year) in filename and filename.startswith("Streaming_History_Audio"):
                with open(os.path.join(directory, filename), encoding='utf-8') as json_file:
                    data.append(json.load(json_file))
        else:
            if filename.endswith(".json") and filename.startswith("Streaming_History_Audio"):
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
            if stream['master_metadata_track_name'] == None or stream['master_metadata_album_artist_name'] == None or \
                    stream['master_metadata_album_album_name'] == None:
                continue
            artists.append(stream['master_metadata_album_artist_name'])
            songs.append(stream['master_metadata_track_name'])
            albums.append(stream['master_metadata_album_album_name'])
            streams['song'].append(stream['master_metadata_track_name'])
            streams['album'].append(stream['master_metadata_album_album_name'])
            streams['artist'].append(stream['master_metadata_album_artist_name'])
            streams['uri'].append(stream['spotify_track_uri'])
    song_pairs = list(zip(streams["song"], streams["artist"], streams["uri"]))
    return streams, song_pairs, artists, albums

def topArtists(artists, range):
    top_list = Counter(artists).most_common(range)
    for artist, count in top_list:
        print(artist, count)
    # WIP - figuring out how to display this data properly
    # artistImage = sp.search(q='artist:' + artist, type='artist')
    # img = url_to_image(artistImage['artists']['items'][0]['images'][0]['url'])
    # output = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # output = Image.fromarray(output)
    # output.show()
    df = pd.DataFrame(top_list, columns=["artist", "count"])
    df = pd.DataFrame(top_list, columns=["artist", "count"])
    df.plot.bar(x="artist", y="count", legend=False, figsize=(20, 10))
    plt.title("Top Artists")
    plt.xlabel("Artist")
    plt.ylabel("Streams")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()

def topSongs(songs, range, year, sp):
    uri_map = {}
    pairs = []
    for song, artist, uri in songs:
        uri_map[(song, artist)] = uri
        pairs.append((song, artist))
    top_list = Counter(pairs).most_common(range)
    imageList = []
    uriList = []
    print("---- Top Songs ----")
    for song, count in top_list:
        print(song[0], count)
        cover = sp.track(uri_map[(song[0], song[1])])
        url = cover["album"]["images"][0]["url"]
        img = url_to_image(url)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        imageList.append(img.astype("uint8"))
        uriList.append(uri_map[(song[0], song[1])])
    j = 0  # intialises a counter for moving through the songs
    averages = imageList[j]  # initialises averages to be the numpy array of the first photo
    while j < range - 1:  # While the counter is less than the length of the number of images:
        readInFile = imageList[j + 1]  # read in the value of the next photo in the list
        readInFileFixed = np.resize(readInFile, (640, 640, 3))
        averages = averages.astype(int) + readInFileFixed.astype(int)  # combine the values of both numpy arrays
        j += 1  # increment j
    averages = averages / len(imageList)  # find the average by dividing by the number of images
    averages = averages.astype("uint8")  # convert averages back to uint8
    outputImage = Image.fromarray(averages)  # create the image from the numpy array averages
    outputImage.save("Top Song Average New.jpg")  # save the image as a jpg
    outputImage.show()
    create_playlist(sp, uriList, outputImage, range, year)

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
def topAlbum(albums, range):
    top_list = Counter(albums).most_common(range)
    print("---- Top Albums ----")
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

def main():
    from argparse import ArgumentParser
    sp = create_spotify_client()
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
    streams, song_pairs , artists, albums = readInStreams(selected_year)

    match selected_type:
        case "artists":
            topArtists(artists, selected_range)
        case "songs":
            topSongs(song_pairs, selected_range, selected_year, sp)
        case "albums":
            topAlbum(albums, selected_range)

if __name__ == "__main__":
    main()