#!/usr/bin/env python2
from __future__ import print_function

import subprocess as sp
import io
import getopt
import os
import imp
import sys
import audioop
import time
import traceback
import threading
import json
from builtin import *
import handles

SCRIPTPATH = os.path.dirname(__file__)
# Add pymumble folder to python PATH for importing
sys.path.append(os.path.join(SCRIPTPATH, 'pymumble'))
import pymumble

PIDFILE = '/tmp/mj.pid'


def num_scripts():
    if os.path.isfile(PIDFILE):
        with open(PIDFILE) as f:
            return len(f.readlines())
    return 0


def writepid():
    mode = 'a' if os.path.isfile(PIDFILE) else 'w'
    with open(PIDFILE, mode) as f:
        f.write(str(os.getpid()) + '\n')
        

def deletepid():
    with open(PIDFILE, 'r') as f:
        lines = f.readlines()
    with open(PIDFILE, 'w') as f:
        for line in lines:
            if line != str(os.getpid()) + '\n':
                f.write(line)


class MJModule:
    """Object of MumbleJumble's modules"""
    def __init__(self):
        pass


class MumbleJumble:
    """Represents the Mumble client interacting with users and outputting sound
    """
    def __init__(self):
        with open(os.path.join(SCRIPTPATH, 'config.json')) as json_config_file:
            self.config = json.load(json_config_file)

        pymumble_parameters = {}
        arglist = ['server=', 'port=', 'user=', 'password=', 'certfile=', 
                   'reconnect=', 'debug=']

        self.config_username = False

        try:
            opt, arg = getopt.getopt(sys.argv[1:], '', arglist)
            for arg_value in opt:
                pymumble_parameters[arg_value[0][2:]] = arg_value[1]
        except getopt.GetoptError:
            sys.exit('usage: MumbleJumble.py --argument1 <value> --argument2 <value>')

        for arg in arglist:
            arg = arg[:-1]
            if arg not in pymumble_parameters:
                if arg == 'user':
                    try:
                        pymumble_parameters[arg] = self.config['bot'][arg][num_scripts()]
                        writepid()
                        self.config_username = True
                    except IndexError:
                        print('Usernames already taken by other MumbleJumble scripts')
                        sys.exit('''If you think this is an error, try deleting {0} and restarting all MumbleJumble instances'''.format(PIDFILE))
                else:
                    pymumble_parameters[arg] = self.config['bot'][arg]

        self.client = pymumble.Mumble(host=pymumble_parameters['server'],
                                      port=int(pymumble_parameters['port']),
                                      user=pymumble_parameters['user'], 
                                      password=pymumble_parameters['password'],
                                      certfile=pymumble_parameters['certfile'],
                                      reconnect=pymumble_parameters['reconnect'], 
                                      debug=pymumble_parameters['debug'])

        # Sets to client to call command_received when a user sends text
        self.client.callbacks.set_callback('text_received', self.command_received)

        self.queue = Queues()
        # Shortcuts for API
        self.build_mirror = self.queue.build_mirror
        self.append_audio = self.queue.append_audio

        self.client.start()  # Start the mumble thread

        try:
            self.volume = float(self.config['bot']['volume'])
        except (KeyError, ValueError):
            self.volume = 1.00
        self.paused = False
        self.skipLeaf = False
        self.skipBranch = False
        self.leaf = None
        self.reload_count = 0
        self.client.is_ready()  # Wait for the connection
        self.client.set_bandwidth(200000)
        self.client.users.myself.unmute()  # Be sure the client is not muted
        with open(os.path.join(SCRIPTPATH, 'comment')) as comment:
            self.client.users.myself.comment(comment.read())

        self.load_modules()

        self.ffmpegthread = FfmpegThread(self)
        self.ffmpegthread.start()

        self.loopthread = LoopThread(self)
        self.loopthread.start()

        self.audio_loop()  # Loops the main thread

    def load_modules(self):
        print('\nLoading bot modules')
        self.registered_commands = {'c': clear_queue,
                                    'clear': clear_queue,
                                    'p': toggle_pause,
                                    'pause': toggle_pause,
                                    'q': print_queue,
                                    'queue': print_queue,
                                    'r': reload_modules,
                                    'reload': reload_modules,
                                    's': skip,
                                    'seek': seek,
                                    'skip': skip,
                                    'v': chg_vol,
                                    'vol': chg_vol,
                                    'volume': chg_vol}
        self.registered_modules = []  # List of module objects

        # Lists modules
        filenames = []
        for fn in os.listdir(os.path.join(SCRIPTPATH, 'modules')):
            if fn.endswith('.py') and not fn.startswith('_'):
                filenames.append(os.path.join(SCRIPTPATH, 'modules', fn))

        # Tries to import modules
        modules = []
        for filename in filenames:
            name = os.path.basename(filename)[:-3]
            try:
                module = imp.load_source(name, filename)
            except Exception as e:
                print('Could not load module ' + name)
                print('  ' + str(e))
                continue
            modules.append(module)

        # Registers modules and creates modules objects
        for module in modules:
            try:
                if hasattr(module, 'register'):
                    if hasattr(module.register, 'enabled') and not module.register.enabled:
                        continue

                    print('Loading module ', module.__name__)
                    module.register(self)

                    module_object = MJModule()

                    l = ['call', 'loop', 'queue_append']
                    for attr in l:
                        try:
                            value = getattr(module, attr)
                            setattr(module_object, attr, value)
                        except AttributeError:
                            continue

                    self.registered_modules.append(module_object)

                    try:
                        for command in module.register.commands:
                            if command in self.registered_commands.keys():
                                print('Command "{0}" already registered'.format(command), file=sys.stderr)
                            else:
                                print("  Registering '{0}' - for module '{1}'".format(command, module.__name__))
                                self.registered_commands[command] = module_object.call
                    except TypeError:
                        print("  No commands registered for module '{0}'".format(module.__name__))

                else:
                    print("Could not register '{0}', for it is missing the 'register' function".format(module),
                          file=sys.stderr)
            except Exception as e:
                print("Error registering module '{0}'".format(module.__name__))
                traceback.print_exc()
        return len(modules)

    def get_current_channel(self):
        """Get the client's current channel (dict)"""
        try:
            return self.client.channels[self.client.users.myself['channel_id']]
        except KeyError:
            print('Currently assuming bot is in channel 0, try moving it')
            return self.client.channels[0]
    
    def send_msg_current_channel(self, msg):
        """Send a message in the client's current channel"""
        self.get_current_channel().send_text_message(msg)

    def command_received(self, text):
        """Main function that reads commands in chat and outputs accordingly
        Takes text, a class from pymumble.mumble_pb2. Commands have to start with a !
        """
        message = text.message.lstrip().split(' ', 1)
        if message[0].startswith('!'):
            command = message[0][1:]
            arguments = ''.join(message[1]).strip(' ') if len(message) > 1 else ''
            try:
                self.registered_commands[command](self, command, arguments)
            except KeyError:
                pass
     
    def audio_loop(self):
        """Main loop that sends audio samples to the server. Sends the first
        """
        while True:
            try:
                if self.queue.audio:
                    try:
                        self.leaf = self.queue.audio[0].leaves[0]
                    except AttributeError:
                        self.leaf = self.queue.audio[0]
                    while self.leaf.current_sample <= self.leaf.total_samples:
                        while self.paused:
                            time.sleep(0.1)
                        while self.client.sound_output.get_buffer_size() > 0.5:
                            time.sleep(0.1)
                        if not self.skipLeaf:
                            self.client.sound_output.add_sound(audioop.mul(
                                            self.leaf.samples[self.leaf.current_sample],
                                            2, self.volume))
                            self.leaf.current_sample += 1
                        elif self.skipLeaf:
                            self.skipLeaf = False
                            break
                    try:
                        # Removes the first song from the queue
                        # Will fail if clear command is passed, not a problem though
                        if self.leaf.branch is not None:
                            if self.skipBranch: 
                                del self.queue.audio[0]
                                self.skipBranch = False
                            else:
                                self.queue.delete_leaf(0, 0)

                        else:
                            self.queue.delete_leaf(0)
                    except:
                        pass
                    finally:
                        self.leaf = None
                else:
                    time.sleep(0.5)
            except Exception as e:
                print(e)
            except KeyboardInterrupt:
                if self.config_username:
                    deletepid()
                sys.exit('Exiting!')


class FfmpegThread(threading.Thread):
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.parent = parent
        self.daemon = True

    def run(self):
        while True:
            if self.parent.queue.ffmpeg:
                try:
                    leaf = self.parent.queue.ffmpeg[0].leaves[0]
                except AttributeError:
                    leaf = self.parent.queue.ffmpeg[0]
                try:
                    process(leaf)
                    self.parent.queue.append_leaf(leaf)
                except AssertionError:
                    self.parent.send_msg_current_channel(u'Could not process <b>{0}</b>'.format(leaf.title))
                finally:
                    self.parent.queue.remove_audio()
            else:
                time.sleep(0.5)


def process(leaf):
    """ Converts and splits the song into the suitable format to stream to
    mumble server (mono PCM 16 bit little-endian), using ffmpeg
    """
    command = ['ffmpeg', '-nostdin', '-i', '-', '-f', 's16le', '-acodec',
               'pcm_s16le', '-ac', '1', '-ar', '48000', '-']
    if leaf.pipe:
        p = sp.Popen(command, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
        stdout, stderr = p.communicate(input=leaf.file)
    else:
        command[3] = leaf.file
        p = sp.Popen(command, stdout=sp.PIPE, stderr=sp.PIPE)
        stdout, stderr = p.communicate()
    print(stderr)
    assert len(stdout) > 0
    counter = 1
    start = stderr.rfind('time=')
    leaf.duration = stderr[start + 5:start + 17]
    with io.BytesIO(stdout) as out:
        while True:
            leaf.samples[counter] = out.read(88200)
            if not leaf.samples[counter]:  # If last fragment is empty
                leaf.total_samples = counter
                return
            counter += 1


class LoopThread(threading.Thread):
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.parent = parent
        self.daemon = True

    def run(self):
        counter = 0
        while True:
            time.sleep(1)
            counter += 1
            for module in self.parent.registered_modules:
                if hasattr(module, 'loop') and hasattr(module.loop, 'time'):
                    if counter % module.loop.time == 0:
                        module.loop(self.parent)


class Queues:
    def __init__(self):
        self.ffmpeg = []
        self.audio = []

    def __iter__(self):
        for i in self.audio:
            yield i
        for j in self.ffmpeg:
            yield j

    def append_audio(self, audio_file, audio_title, branchname=None, pipe=False):
        leaf = handles.Leaf(audio_file, audio_title, pipe)
        if branchname is not None:
            branch = handles.Branch(branchname, leaf)
            self.ffmpeg.append(branch)
        else:
            self.ffmpeg.append(leaf)

    def remove_audio(self):
        del self.ffmpeg[0]

    def append_leaf(self, leaf):
        if leaf.branch is None:
            self.audio.append(leaf)
        else:
            for i in self.audio:
                if i.title == leaf.branch.title and isinstance(i, handles.Branch):
                    i.append(leaf)
                    return
            self.audio.append(leaf.branch)

    def delete_leaf(self, leaf_index, branch_index=None):
        if branch_index is None:
            del self.audio[leaf_index]
        else:
            self.audio[branch_index].remove_leaf(leaf_index)
            if not self.audio[branch_index]:
                self.delete_branch(branch_index)

    def delete_branch(self, branch_index):
        del self.audio[branch_index]

    def build_mirror(self):
        mirror = {}
        for i in self:
            if isinstance(i, handles.Branch):
                try:
                    for leaf in i:
                        mirror[i.title].append(leaf.title)
                except KeyError:
                    mirror[i.title] = [leaf.title for leaf in i]
            else:
                try:
                    mirror[i.title] += 1
                except KeyError:
                    mirror[i.title] = 1
        return mirror

    def clear(self):
        # TODO fix cause it keeps failing with current ffmpeg thread
        self.ffmpeg = []
        self.audio = []


if __name__ == '__main__':
    bot = MumbleJumble()
