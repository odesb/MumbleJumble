
def call(bot, command_used, arguments):
    bot.send_msg_current_channel("Reloading bot config")
    bot.load_modules()

def register(bot):
    pass

register.commands = ["reload"]
