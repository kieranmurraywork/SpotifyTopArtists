import contextlib
import math
import os
from io import BytesIO
from urllib import request

import cv2
import imageio
import numpy as np
from spotipy import Spotify, SpotifyException
from matplotlib import pyplot as plt
from dotenv import load_dotenv
from PIL import Image
from spotipy.oauth2 import SpotifyOAuth
import base64
import glob


def create_spotify_client():
    load_dotenv(dotenv_path=".env")
    cache_path = ".cache"
    auth = SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
        scope="playlist-modify-public user-top-read ugc-image-upload playlist-modify-private",
        cache_path=cache_path,
    )

    try:
        token_info = auth.get_access_token()
        return Spotify(auth_manager=auth)

    except SpotifyException as e:
        if "invalid_grant" in str(e):
            print("Refresh token expired — deleting cache and reauthenticating.")
            os.remove(cache_path)
            auth = SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
        scope="playlist-modify-public user-top-read ugc-image-upload playlist-modify-private",
        cache_path=cache_path,
        )
            auth.get_access_token(as_dict=True)
            return Spotify(auth_manager=auth)

        raise

def url_to_image(url) -> cv2.typing.MatLike:
    """Generate an image from a URL."""
    resp = request.urlopen(url)
    image = np.asarray(bytearray(resp.read()), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("cv2.imdecode failed to create an image.")

    return image


def download_covers(urls, workers=8):
    """Download several cover images at once (in parallel), keeping their order."""
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(url_to_image, urls))


COVER_SIZE = 640  # every cover is scaled to COVER_SIZE x COVER_SIZE before being combined


def cover_to_rgb(image, size=COVER_SIZE):
    """Scale an OpenCV (BGR) cover to size x size and convert it to RGB."""
    image = cv2.resize(image, (size, size), interpolation=cv2.INTER_AREA)
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def average_image(images):
    """Pixel-wise average of RGB covers, returned as a PIL image.

    Each image is scaled to COVER_SIZE first so covers of different sizes line up.
    """
    if not images:
        raise ValueError("No images to average.")
    resized = [cv2.resize(img, (COVER_SIZE, COVER_SIZE), interpolation=cv2.INTER_AREA) for img in images]
    averages = np.mean(np.stack(resized).astype(np.float64), axis=0)
    return Image.fromarray(averages.astype("uint8"))


def create_playlist(sp, results, playlistCover, count, coverage):
    """Create a playlist.

    results is either a current_user_top_tracks response, or a plain list of track URIs.
    """
    username = sp.me()['id']
    if isinstance(results, dict) and "items" in results:
        track = [item["id"] for item in results["items"]]
        playlistName = f"{username}'s Top {count} Songs Generated - {coverage}"
    else:
        track = list(results)
        if coverage == "all":
            playlistName = f"{username}'s Top {count} Songs of All Time"
        else:
            playlistName = f"{username}'s Top {count} Songs of {coverage}"
    playlist = sp.user_playlist_create(name=playlistName,public=True,user=username)
    # Spotify accepts at most 100 tracks per request
    for start in range(0, len(track), 100):
        sp.playlist_add_items(playlist["id"], track[start:start + 100], position=None)
    if playlistCover is None:
        return
    playlistFile = BytesIO()
    playlistCover.save(playlistFile, format="jpeg")
    playlistBytes = playlistFile.getvalue()
    playlistB64 = base64.b64encode(playlistBytes)
    sp.playlist_upload_cover_image(playlist["id"], image_b64=playlistB64)

def create_slideshow(imageList):
    with imageio.get_writer('movie.mp4', mode='I') as writer:  # set the format to mp4 importing multiple images
        for i in range(len(imageList)):  # Loop for appending all images in imageList to the outputted mp4
            image = imageList[i]  # set image to the image in the ith element
            writer.append_data(image)  # append this image to the writer
""" #Commented out as code is currently not working in this iteration

    ###### The below code return a gif but requires downloaded images #############
    # filepaths
    fp_in = "Top Songs/Top Songs *.png"
    fp_out = "image.gif"

    # use exit stack to automatically close opened images
    with contextlib.ExitStack() as stack:
        # lazily load images
        imgs = (stack.enter_context(Image.open(f))
                for f in sorted(glob.glob(fp_in)))

        # extract  first image from iterator
        img = next(imgs)

        # https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#gif
        img.save(fp=fp_out, format='GIF', append_images=imgs,
                 save_all=True, duration=200, loop=0)
"""
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
    parser.add_argument(
        "-p",
        "--playlist",
        action="store_true",
        help="Generate a playlist for your top songs")
    parser.add_argument(
        "-s",
        "--slideshow",
        action="store_true",
        help="Generate a slideshow for your top songs")

    args = parser.parse_args()

    selected_range: str = args.range
    selected_limit: int = args.limit
    selected_playlist: bool = args.playlist
    selected_slideshow: bool = args.slideshow

    sp = create_spotify_client()

    imageList = []  # initialise empty list for storing images
    results = sp.current_user_top_tracks(
        time_range=selected_range, limit=selected_limit
    )  # Returns the top songs with the corresponding timeframe up to the limit
    if results is None:
        raise ValueError("sp.current_user_top_tracks failed to generate any results.")
    # Cover URLs for each track (local files have no cover art, so they're skipped)
    urls = [item["album"]["images"][0]["url"] for item in results["items"] if item["album"]["images"]]
    for img in download_covers(urls):  # numpy arrays of the covers (BGR), downloaded in parallel
        ##### Below line is for placing the name of the song ontop of the cover art #####
        # cv2.putText(img,f"{item['name']}", (0,550),fontFace=2, fontScale=2, color=(255,255,255), thickness=2)
        imageList.append(cover_to_rgb(img))  # same size, RGB, so they can be combined
    if not imageList:
        raise ValueError("None of your top tracks had cover art.")

    # Config:
    result_grid_filename = "./gridnew.jpg"  # Filename for the resulting collage
    cell_inches = 4  # size of each cover in the grid (1 inch = 100px)

    # Grid size follows the number of covers, e.g. 50 covers -> 8 columns x 7 rows
    columns = math.ceil(math.sqrt(len(imageList)))
    rows = math.ceil(len(imageList) / columns)
    fig, axes = plt.subplots(
        rows,
        columns,
        figsize=(columns * cell_inches, rows * cell_inches),
        squeeze=False,
    )
    for position, ax in enumerate(axes.flat):
        ax.axis("off")
        if position < len(imageList):
            ax.imshow(imageList[position])

    plt.subplots_adjust(
        left=0.0, right=1.0, bottom=0.0, top=1.0, wspace=0.0, hspace=0.0
    )
    plt.savefig(result_grid_filename)

    outputImage = average_image(imageList)
    outputImage.save("Top Song Average New.jpg")  # save the image as a jpg
    outputImage.show()  # display the image
    if selected_playlist:
        create_playlist(sp, results,outputImage,selected_limit,selected_range)
    if selected_slideshow:
        create_slideshow(imageList)


if __name__ == "__main__":
    main()
