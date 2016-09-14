from __future__ import unicode_literals

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
            leaf -= 1  # Since leaf is an index
        except IndexError:
            leaf = None
            if select == 1:
                bot.skipLeaf = True
                if hasattr(bot.leaf, 'branch') and bot.leaf.branch is not None:
                    bot.skipBranch = True
                return
        except ValueError:
            bot.send_msg_current_channel('Invalid value!')
            return
        try:
            select -= 1  # Since select is an index
            if isinstance(bot.queue.audio[select], handles.Branch):
                if leaf is not None:
                    bot.queue.delete_leaf(leaf, select)
                else:
                    bot.queue.delete_branch(select)
            else:
                bot.queue.delete_leaf(select)
        except IndexError:
            bot.send_msg_current_channel('Invalid index')
    else:
        bot.skipLeaf = True
        if hasattr(bot.leaf, 'branch') and bot.leaf.branch is not None:
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
    bot.queue.clear()


def print_queue(bot, command, arguments):
    """Creates a printable queue suited for the Mumble chat. Associated with
    the queue command. Checks the processing and processed song lists of the
    subthread. Possible states: Paused, Playing, Ready.
    """
    if not bot.queue.audio and not bot.queue.ffmpeg:
        queue = 'Queue is empty'
    else:
        queue = ''
        if bot.queue.audio:
            for i, x in enumerate(bot.queue.audio):
                if isinstance(x, handles.Branch):
                    queue += '<br />' + x.title
                    for j, y in enumerate(x):
                        title = y.title
                        status = y.leaf_status()
                        if i == 0 and j == 0:
                            if bot.paused:
                                queue += '<br />|---- {0}<b> - Paused - {1}</b>'.format(title, status)
                            else:
                                queue += '<br />|---- {0}<b> - Playing - {1}</b>'.format(title, status)
                        else:
                            queue += '<br />|---- {0}<b> - Ready - {1}</b>'.format(title, status[9:17])
                else:
                    title = x.title
                    status = x.leaf_status()
                    if i == 0:
                        if bot.paused:
                            queue += '<br />{0}<b> - Paused - {1}</b>'.format(title, status)
                        else:
                            queue += '<br />{0}<b> - Playing - {1}</b>'.format(title, status)
                    else:
                        queue += '<br />{0}<b> - Ready - {1}</b>'.format(title, status[9:17])

        if bot.queue.ffmpeg:
            for z in bot.queue.ffmpeg:
                queue += '<br />{0}<b> - Processing</b>'.format(z[1])

        for module in bot.registered_modules:
            if hasattr(module, 'queue_append'):
                queue += module.queue_append()

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
        seconds = handles.duration2sec(new_time)
    except ValueError:
        bot.send_msg_current_channel('Invalid time')
        return
    if 0 <= seconds <= handles.duration2sec(bot.leaf.duration):
        bot.leaf.seek(seconds)
    else:
        bot.send_msg_current_channel('Cannot seek to specified value.')
