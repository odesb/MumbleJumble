import modules.ImageDownload
import modules.Youtube

# This is a great way to lose all your friends
def call(bot, command_used, arguments):
    if command_used == "pain":
        register.gospam = True;
        Youtube.call(bot, "a", "https://www.youtube.com/watch?v=z48NmdWbquw")
    elif command_used == "makeitstop":
        register.gospam = False
        bot.clear_queue()

def register(bot):
    pass

def loop(bot):
    if(register.gospam):
        ImageDownload.call(bot, "i", "https://t7.rbxcdn.com/7ad2cf73acdea316ecc78941d1cc4e6c")

register.gospam = False
register.commands = ["pain", "makeitstop"]
register.enabled = False
