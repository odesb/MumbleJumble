
def call(bot, command_used, arguments):
    bot.send_msg_current_channel("Reloading bot config")
    bot.setup()

def register(bot):
    pass

register.commands = ["reload"]
