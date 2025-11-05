import math
import os
import urllib

import cv2
import numpy as np
import spotipy
from matplotlib import pyplot as plt
from dotenv import load_dotenv
from natsort import natsorted
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials


load_dotenv(dotenv_path=".env")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope="user-top-read",
    )
)


def url_to_image(url):
    # download the image, convert it to a NumPy array, and then read
    # it into OpenCV format
    resp = urllib.request.urlopen(url)
    image = np.asarray(bytearray(resp.read()), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    # return the image
    return image


ranges = ["short_term", "medium_term", "long_term"]

print("range:", ranges[0])
results = sp.current_user_top_tracks(time_range=ranges[0], limit=50)
for i, item in enumerate(results["items"]):
    url = item["album"]["images"][0]["url"]
    img = url_to_image(url)
    print("downloading %s" % url)
    # cv2.putText(img,f"{item['name']}", (0,550),fontFace=2, fontScale=2, color=(255,255,255), thickness=2)
    cv2.imwrite(f"Top Songs/Top Songs {i + 1}.png", img)
    image = cv2.imread(f"Top Songs/Top Songs {i + 1}.png")
    cv2.imread(f"Top Songs/Top Songs {i + 1}.png")
    print(i, item["name"], "//", item["artists"][0]["name"])
print()
# Config:
images_dir = "./Top Songs"
result_grid_filename = "./gridnew.jpg"
result_figsize_resolution = 40  # 1 = 100px

images_list = natsorted(os.listdir(images_dir))
images_count = len(images_list)
print("Images: ", images_list)
print("Images count: ", images_count)

# Calculate the grid size:
grid_size = math.ceil(math.sqrt(images_count))

# Create plt plot:
fig, axes = plt.subplots(
    7,
    8,
    figsize=(result_figsize_resolution, result_figsize_resolution),
    sharex=True,
    sharey=True,
)

current_file_number = 0
for image_filename in images_list:
    y_position = current_file_number % 8
    x_position = current_file_number // 8

    plt_image = plt.imread(images_dir + "/" + images_list[current_file_number])
    axes[x_position, y_position].imshow(plt_image)
    axes[x_position, y_position].axis("off")
    print((current_file_number + 1), "/", images_count, ": ", image_filename)

    current_file_number += 1

plt.subplots_adjust(left=0.0, right=1.0, bottom=0.0, top=1.0)
plt.subplots_adjust(wspace=0, hspace=0)
plt.savefig(result_grid_filename)

j = 0
averages = cv2.imread(f"Top Songs/Top Songs {j + 1}.png")
while j < i:
    readInFile = cv2.imread(f"Top Songs/Top Songs {j + 2}.png")
    averages = averages.astype(int) + readInFile.astype(int)
    j += 1
averages = averages / images_count
cv2.imwrite(f"Top Song Average.png", averages)
