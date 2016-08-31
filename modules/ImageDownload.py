import requests
import os
import base64
import magic
import hashlib
import traceback
import glob
from PIL import Image
from bs4 import BeautifulSoup

IMAGE_CACHE=".image_cache"
MAX_IMAGE_SIZE = 64000
LOWEST_QUALITY = 20
LOWEST_SCALE = 0.10

def get_resized_filename(original):
    filename, extension = os.path.splitext(original)
    resized_filename = filename + "resized" + extension
    return resized_filename


def resize(original, desired_quality, scale_factor):
    image = Image.open(original)
    resized_filename = get_resized_filename(original)
    width, height = image.size
    resized_width = int(width*scale_factor)
    resized_height = int(height*scale_factor)
    if scale_factor is not 1:
        image = image.resize((resized_width, resized_height), Image.ANTIALIAS) 
    image.save(resized_filename, quality=desired_quality, optimize=True)
    file_size = os.stat(resized_filename).st_size
    print("Resizing image '{0}' with quality '{1}' and size factor '{2}' ({3}x{4}) - new filesize: {5}".format(resized_filename, desired_quality, scale_factor, resized_width, resized_height, file_size))
    if file_size < MAX_IMAGE_SIZE:
        return resized_filename
    else:
        return -1

def call(bot, command_used, arguments):
    soup = BeautifulSoup(arguments, 'lxml')

    # extract text from potential HTML
    text = str(soup.get_text().encode('utf-8'))
    sha_1 = hashlib.sha1()
    sha_1.update(text)

    # reuse file names
    unique_filename = str(sha_1.hexdigest())
    try:
        image_filename = IMAGE_CACHE + "/" + unique_filename 
        cached_filename = get_resized_filename(image_filename)
        cached_filename = glob.glob(cached_filename + "*")
        if not cached_filename:
            # download
            file_handle = open(image_filename, 'wb')
            response = requests.get(text, headers={"User-Agent": "Mozilla/5.0"})
            file_handle.write(response.content)
            file_handle.close()

            # resize
            file_type = magic.from_file(image_filename, mime=True)
            file_ext = file_type.rsplit('/')[1]
            file_size = os.stat(image_filename).st_size
            old_filename = image_filename
            image_filename += "." + file_ext
            os.rename(old_filename, image_filename)

            print("Downloaded '{0}' ({1}), size: {2}".format(text, file_type, file_size))

            if file_type == "text/html":
                bot.send_msg_current_channel("You're getting denied by that website, sorry")
                return -1
            
            resized_filename = image_filename
            if file_size > MAX_IMAGE_SIZE:
                # work on a copy of the original
                print("Image {0} is too big".format(image_filename))
                quality = 90
                resize_factor = 1
                giving_up = False
                while not giving_up:
                    resized_filename = resize(image_filename, quality, resize_factor)
                    if resized_filename != -1:
                        giving_up = True
                    else:
                        if quality > LOWEST_QUALITY:
                            quality -= 20
                        else: 
                            if resize_factor > LOWEST_SCALE:
                                quality = 100
                                resize_factor *= 0.75
                            else:
                                bot.send_msg_current_channel("Giving up on image '{0}'".format(text))
                                return -1
            

        else:
            print("Cache hit")
            resized_filename = cached_filename[0]
            file_type = magic.from_file(resized_filename, mime=True)

        # convert to base64
        with open(resized_filename, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
            bot.send_msg_current_channel('<img src="data:{0};base64,{1}"/>'.format(file_type, encoded_string))
    except Exception as e:
        traceback.print_exc()

def register(bot):
    if not os.path.exists(IMAGE_CACHE):
        os.mkdir(IMAGE_CACHE)

register.commands = ["i", "img"]
register.background = True
# register.call_in_loop = True

