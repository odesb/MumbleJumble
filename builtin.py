import handles


def reload_modules(bot, command, arguments):
    bot.reload_count += 1
    loaded_count = bot.load_modules()
    bot.send_msg_current_channel('Reloaded <b>{0}</b> bot modules'.format(loaded_count))



def skip(bot, command, arguments):
    if arguments != '':
        try:
            select = int(arguments.split(';', 1)[0])
            leaf = int(arguments.split(';', 1)[1])
            if select == 1 and leaf == 1:
                bot.skipFlag = True
                return
        except IndexError:
            leaf = None
            if select == 1:
                bot.skipFlag = True
                return
        except ValueError:
            bot.send_msg_current_channel('Not a valid value!')
            return
        try:
            if isinstance(bot.audio_queue[select - 1], handles.Branch) and leaf is not None:
               bot.audio_queue[select - 1].remove_leaf(leaf - 1)
            else:
                del bot.audio_queue[select - 1]
        except IndexError:
            bot.send_msg_current_channel('Not a valid value!')
    else:
        bot.skipFlag = True


def chg_vol(bot, command, arguments):
    if arguments != '':
        try:
            bot.volume = float(arguments)
            bot.send_msg_current_channel('Changing volume to <b>{0}</b>'.format(bot.volume)) 
        except ValueError:
            bot.send_msg_current_channel('Not a valid value!')
    else:
        bot.send_msg_current_channel('Current volume: <b>{0}</b>'.format(bot.volume))


def clear_queue(bot, command, arguments):
    bot.skipFlag = True
    bot.audio_queue = []


def print_queue(bot, command, arguments):
    """Creates a printable queue suited for the Mumble chat. Associated with
    the queue command. Checks the processing and processed song lists of the
    subthread. Possible states: Paused, Playing, Ready, Downloading.
    """
    if not bot.audio_queue:
        queue = 'Queue is empty'
    else:
        queue = ''
        for i in range(len(bot.audio_queue)):
            if isinstance(bot.audio_queue[i], handles.Branch):
                queue += '<br />' + str(bot.audio_queue[i])
                for j in range(len(bot.audio_queue[i].leaves)):
                    title = bot.audio_queue[i].leaves[j].printable_queue_format()[0]
                    status = bot.audio_queue[i].leaves[j].printable_queue_format()[1]
                    if i == 0 and j == 1:
                        if bot.paused:
                            queue += '<br />|---- {0}<b> - Paused - {1}</b>'.format(title, status)
                        elif not bot.paused:
                            queue += '<br />|---- {0}<b> - Playing - {1}</b>'.format(title, status)
                    else:
                        queue += '<br />|---- {0}<b> - Ready - {1}</b>'.format(title, status[9:17])
            else:
                title = bot.audio_queue[i].printable_queue_format()[0]
                status = bot.audio_queue[i].printable_queue_format()[1]
                if i == 0:
                    if bot.paused:
                        queue += '<br />{0}<b> - Paused - {1}</b>'.format(title, status)
                    elif not bot.paused:
                        queue += '<br />{0}<b> - Playing - {1}</b>'.format(title, status)
                else:
                    queue += '<br />{0}<b> - Ready - {1}</b>'.format(title, status[9:17])

    bot.send_msg_current_channel(queue)


def toggle_pause(bot, command, arguments):
    """Toggle the pause command"""
    if bot.paused:
        bot.paused = False
    else:
        bot.paused = True


def seek(bot, command, arguments):
    mod_arg = arguments.replace(':', '').zfill(6)
    new_time = '{0}:{1}:{2}.00'.format(mod_arg[0:2], mod_arg[2:4], mod_arg[4:6])
    try:
        seconds = duration2sec(new_time)
        if 0 <= seconds <= duration2sec(bot.leaf):
            bot.leaf.seek(seconds)
        else:
            bot.send_msg_current_channel('Cannot seek to specified value.')
    except:
        bot.send_msg_current_channel('Cannot seek to specified value.')
