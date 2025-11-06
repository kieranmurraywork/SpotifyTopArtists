import imageio
from main import imageList
import glob
import contextlib
from PIL import Image
######## The below code returns an mp4 without requiring downloaded images #########
i=0

with imageio.get_writer('movie.mp4', mode='I') as writer: # set the format to mp4 importing multiple images
    for i in range(len(imageList)) : # Loop for appending all images in imageList to the outputted mp4
        image = imageList[i] # set image to the image in the ith element
        writer.append_data(image) # append this image to the writer

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