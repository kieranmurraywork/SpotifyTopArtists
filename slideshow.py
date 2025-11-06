import imageio
from main import imageList
import glob
import contextlib
from PIL import Image
######## The below code returns a broken gif without requiring downloaded images #########
i=0
with imageio.get_writer('movie.gif', mode='I',duration=0.5) as writer:
    for i in range(len(imageList)) :
        image = Image.fromarray(imageList[i])
        writer.append_data(image)

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