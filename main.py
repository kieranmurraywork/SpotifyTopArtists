import os
import urllib

import cv2
import numpy as np
import spotipy
from matplotlib import pyplot as plt
from dotenv import load_dotenv
from PIL import Image
from spotipy.oauth2 import SpotifyOAuth
load_dotenv(dotenv_path='.env') # Search for the .env file within the repository
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID') # Get the client ID from the .env
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET') # Get the client secret from the .env
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI') # Get the redirect URI from the .env

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID, #Initialise an instance of the Spotipy API
                                               client_secret=SPOTIFY_CLIENT_SECRET,
                                               redirect_uri=SPOTIFY_REDIRECT_URI,
                                               scope="user-top-read"))


def url_to_image(url):
	# download the image, convert it to a NumPy array, and then read
	# it into OpenCV format
	resp = urllib.request.urlopen(url)
	image = np.asarray(bytearray(resp.read()), dtype="uint8")
	image = cv2.imdecode(image, cv2.IMREAD_COLOR)
	# return the image
	return image
ranges = ['short_term', 'medium_term', 'long_term']
imageList = [] # initialise empty list for storing images
results = sp.current_user_top_tracks(time_range=ranges[2], limit=50) # Returns the top 50 songs with the corresponding timeframe


for i, item in enumerate(results['items']): # For each track in results:
    url = item['album']['images'][0]['url'] # Gets the url for the song's cover art
    img = url_to_image(url) # calls url_to_image and returns the numpy array of the image
    ##### Below line is for placing the name of the song ontop of the cover art #####
    #cv2.putText(img,f"{item['name']}", (0,550),fontFace=2, fontScale=2, color=(255,255,255), thickness=2)
    imageList.append(img.astype('uint8')) # Adds the current image to imageList

# Config:
images_dir = './Top Songs' # Directory for reading the images in for the grid photo
result_grid_filename = './gridnew.jpg' # Filename for the rsulting collage
result_figsize_resolution = 40 # 1 = 100px # sets the resolution

# Create plt plot:
fig, axes = plt.subplots(7, 8, figsize=(result_figsize_resolution, result_figsize_resolution),sharex=True, sharey=True)

current_file_number = 0
while current_file_number < len(imageList):
    y_position = current_file_number % 8
    x_position = current_file_number // 8
    imageList[current_file_number] = cv2.cvtColor(imageList[current_file_number], cv2.COLOR_BGR2RGB) # flip from BGR to RGB
    plt_image = Image.fromarray(imageList[current_file_number])
    axes[x_position, y_position].imshow(plt_image)
    axes[x_position, y_position].axis('off')

    current_file_number += 1

plt.subplots_adjust(left=0.0, right=1.0, bottom=0.0, top=1.0, wspace=0.0, hspace=0.0)
plt.savefig(result_grid_filename)

j = 0 # intialises a counter for moving through the songs
averages = imageList[j] # initialises averages to be the numpy array of the first photo
while j < i: # While the counter is less than the length of the number of images:
    readInFile = imageList[j+1] # read in the value of the next photo in the list
    averages = averages.astype(int) + readInFile.astype(int) # combine the values of both numpy arrays
    j+=1 # increment j
averages = averages / len(imageList) # find the average by dividing by the number of images
averages = averages.astype('uint8') # convert averages back to uint8
outputImage = Image.fromarray(averages) # create the image from the numpy array averages
outputImage.save('Top Song Average New.png') # save the image as a png
outputImage.show() # display the image
