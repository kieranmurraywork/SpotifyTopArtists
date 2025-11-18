import os
from io import BytesIO
from urllib import request

import cv2
import numpy as np
from spotipy import Spotify
from matplotlib import pyplot as plt
from dotenv import load_dotenv
from PIL import Image
from spotipy.oauth2 import SpotifyOAuth
import base64


def create_spotify_client() -> Spotify:
    """Create a Spotify API instance."""
    load_dotenv(dotenv_path=".env")

    return Spotify(
        auth_manager=SpotifyOAuth(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
            scope="playlist-modify-public user-top-read ugc-image-upload playlist-modify-private",
        )
    )


def url_to_image(url) -> cv2.typing.MatLike:
    """Generate an image from a URL."""
    resp = request.urlopen(url)
    image = np.asarray(bytearray(resp.read()), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("cv2.imdecode failed to create an image.")

    return image
def create_playlist(sp, results,playlistCover):
    """Create a playlist"""
    username = sp.me()['id']
    track = []
    playlist = sp.user_playlist_create(name=f"{username}'s Top Songs Generated",public=True,user=username)
    for result in results["items"]:
        track.append(result["id"])
    sp.playlist_add_items(playlist["id"],track,position=None)
    playlistFile = BytesIO()
    playlistCover.save(playlistFile, format="jpeg")
    playlistBytes = playlistFile.getvalue()
    playlistB64 = base64.b64encode(playlistBytes)
    sp.playlist_upload_cover_image(playlist["id"], image_b64=playlistB64)

def main():
    from argparse import ArgumentParser

    parser = ArgumentParser(description="See your Spotify top tracks.")
    parser.add_argument(
        "-r",
        "--range",
        metavar="range",
        choices=["short_term", "medium_term", "long_term"],
        default="medium_term",
        help="Time range for top tracks (default: medium_term)",
    )
    parser.add_argument(
        "-l",
        "--limit",
        metavar="limit",
        type=int,
        default=50,
        help="Number of tracks to fetch (default: 50)",
    )

    args = parser.parse_args()

    selected_range: str = args.range
    selected_limit: int = args.limit

    sp = create_spotify_client()

    imageList = []  # initialise empty list for storing images
    results = sp.current_user_top_tracks(
        time_range=selected_range, limit=selected_limit
    )  # Returns the top songs with the corresponding timeframe up to the limit
    if results is None:
        raise ValueError("sp.current_user_top_tracks failed to generate any results.")
    i = 0
    for i, item in enumerate(results["items"]):  # For each track in results:
        url = item["album"]["images"][0]["url"]  # Gets the url for the song's cover art
        img = url_to_image(
            url
        )  # calls url_to_image and returns the numpy array of the image
        ##### Below line is for placing the name of the song ontop of the cover art #####
        # cv2.putText(img,f"{item['name']}", (0,550),fontFace=2, fontScale=2, color=(255,255,255), thickness=2)
        imageList.append(img.astype("uint8"))  # Adds the current image to imageList


    # Config:
    images_dir = "./Top Songs"  # Directory for reading the images in for the grid photo
    result_grid_filename = "./gridnew.jpg"  # Filename for the rsulting collage
    result_figsize_resolution = 40  # 1 = 100px # sets the resolution

    # Create plt plot:
    fig, axes = plt.subplots(
        7,
        8,
        figsize=(result_figsize_resolution, result_figsize_resolution),
        sharex=True,
        sharey=True,
    )

    current_file_number = 0
    while current_file_number < len(imageList):
        y_position = current_file_number % 8
        x_position = current_file_number // 8
        imageList[current_file_number] = cv2.cvtColor(
            imageList[current_file_number], cv2.COLOR_BGR2RGB
        )  # flip from BGR to RGB
        plt_image = Image.fromarray(imageList[current_file_number])
        axes[x_position, y_position].imshow(plt_image)
        axes[x_position, y_position].axis("off")

        current_file_number += 1

    plt.subplots_adjust(
        left=0.0, right=1.0, bottom=0.0, top=1.0, wspace=0.0, hspace=0.0
    )
    plt.savefig(result_grid_filename)

    j = 0  # intialises a counter for moving through the songs
    averages = imageList[
        j
    ]  # initialises averages to be the numpy array of the first photo
    while j < i:  # While the counter is less than the length of the number of images:
        readInFile = imageList[j + 1]  # read in the value of the next photo in the list
        averages = averages.astype(int) + readInFile.astype(
            int
        )  # combine the values of both numpy arrays
        j += 1  # increment j
    averages = averages / len(
        imageList
    )  # find the average by dividing by the number of images
    averages = averages.astype("uint8")  # convert averages back to uint8
    outputImage = Image.fromarray(
        averages
    )  # create the image from the numpy array averages
    outputImage.save("Top Song Average New.jpg")  # save the image as a jpg
    outputImage.show()  # display the image
    create_playlist(sp, results,outputImage)


if __name__ == "__main__":
    main()
