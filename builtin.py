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
                bot.skipLeaf = True
                return
            leaf -= 1 # Since leaf is an index
        except IndexError:
            leaf = None
            if select == 1:
                bot.skipLeaf = True
                if bot.leaf.branch is not None:
                    bot.skipBranch = True
                return
        except ValueError:
            bot.send_msg_current_channel('Invalid value!')
            return
        try:
            select -= 1 # Since select is an index
            if isinstance(bot.audio_queue[select], handles.Branch):
                if leaf is not None:
                    bot.delete_leaf(leaf, select)
                else:
                    bot.delete_branch(select)
            else:
                bot.delete_leaf(select)
        except IndexError:
            bot.send_msg_current_channel('Invalid index')
    else:
        bot.skipLeaf = True
        if bot.leaf.branch is not None:
            bot.skipBranch = True


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
    bot.skipLeaf = True
    bot.audio_queue = []


def print_queue(bot, command, arguments):
    """Creates a printable queue suited for the Mumble chat. Associated with
    the queue command. Checks the processing and processed song lists of the
    subthread. Possible states: Paused, Playing, Ready.
    """
    if not bot.audio_queue:
        queue = 'Queue is empty'
    else:
        queue = ''
        for i, x in enumerate(bot.audio_queue):
            if isinstance(x, handles.Branch):
                queue += '<br />' + str(x)
                for j, y in enumerate(x):
                    title = str(y)
                    status = y.leaf_status()
                    if i == 0 and j == 0:
                        if bot.paused:
                            queue += '<br />|---- {0}<b> - Paused - {1}</b>'.format(title, status)
                        else:
                            queue += '<br />|---- {0}<b> - Playing - {1}</b>'.format(title, status)
                    else:
                        queue += '<br />|---- {0}<b> - Ready - {1}</b>'.format(title, status[9:17])
            else:
                title = str(x)
                status = x.leaf_status()
                if i == 0:
                    if bot.paused:
                        queue += '<br />{0}<b> - Paused - {1}</b>'.format(title, status)
                    else:
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
