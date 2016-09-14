def register(bot):
    pass

register.commands = ['w']
register.enabled = True


def call(bot, command, arguments):
    url = arguments.replace('<a href="', '')
    end = url.find('">')
    url = url[:end]
    title_index = url.rfind('/') + 1
    title = url[title_index:]
    bot.send_msg_current_channel('Adding <b>{0}</b> to the queue'.format(title))
    bot.append_audio(url, title)
