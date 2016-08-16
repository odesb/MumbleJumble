
def call(bot, command_used, arguments):
    loaded_count = bot.load_modules()
    bot.send_msg_current_channel("Reloaded '{0}' bot modules".format(loaded_count))

def register(bot):
    pass

register.commands = ["reload"]
