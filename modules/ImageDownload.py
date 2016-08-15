import urllib
import uuid
import nltk

from urllib import urlopen
IMAGE_CACHE=".image_cache"

def call(bot, command_used, arguments):
    raw = nltk.clean_html(arguments) 
    print("Calling with {0}".format(raw))
    unique_filename = uuid.uuid4()
    try:
        urllib.urlretrieve(arguments, unique_filename)
    except Exception as e:
        print(e)

def register(bot):
    print("Registering bot")

register.commands = ["i", "images"]
