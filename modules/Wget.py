def register(bot):
    pass

register.commands = ['w']
register.enabled = True

def call(bot, command, arguments):
    url = arguments.replace('<a href="', '')
    end = url.find('">')
    url = url[:end]
    bot.append_audio(url, 'complete', '--')
