import Youtube
import ImageDownload
import random

SHREKLIST= ['http://vignette4.wikia.nocookie.net/trollpasta/images/a/a1/Shrek_scary_face.jpg/revision/latest?cb=20140724065638',
        'https://t7.rbxcdn.com/7ad2cf73acdea316ecc78941d1cc4e6c',
        'http://i0.kym-cdn.com/photos/images/facebook/000/498/869/a3f.jpg',
        'http://i0.kym-cdn.com/photos/images/facebook/000/526/244/aac.png',
        'http://i1.kym-cdn.com/photos/images/newsfeed/000/488/509/54f.png',
        'http://i1.kym-cdn.com/photos/images/newsfeed/000/665/128/cb0.png',
        'http://67.media.tumblr.com/4f50d9c68954b44ae8fb75917a8689a7/tumblr_ns7nqoIGZd1uvuwdlo1_250.jpg',
        'http://i0.kym-cdn.com/photos/images/newsfeed/000/488/341/d27.png',
        'http://t09.deviantart.net/aspYtIM9BsIJlUxR4MxZ3UkpFsA=/300x200/filters:fixed_height(100,100):origin()/pre05/1886/th/pre/f/2014/115/e/9/shreking_intensifies_by_mocadeluxen-d7fz1dr.jpg']

def register(bot):
    pass

register.commands = ["pain", "makeitstop"]
register.enabled = True

# This is a great way to lose all your friends
def call(bot, command_used, arguments):
    if command_used == "pain":
        loop.spam = True;
        Youtube.call(bot, "a", "https://www.youtube.com/watch?v=z48NmdWbquw")
    elif command_used == "makeitstop":
        loop.spam = False
        bot.skip('!s', '')



def loop(bot):
    if loop.spam:
        ImageDownload.call(bot, "i", random.choice(SHREKLIST))

loop.spam = False
loop.time = 1
