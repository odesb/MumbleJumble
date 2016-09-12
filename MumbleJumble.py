#!/usr/bin/env python
from __future__ import print_function

import subprocess as sp
import io
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

def get_arg_value(arg):
    """Retrieves the values associated to command line arguments
    Possible arguments:
    --server    Mumble server address
    --port      Mumble server port
    --user      Mumble bot's username
    --password  Mumble server password
    --certfile  Mumble certification
    --reconnect Bot reconnects to the server if disconnected
    --debug     Debug=True will generate a lot of stdout messages
    """
    if arg in sys.argv[1:]:
        try:
            return sys.argv[1:][sys.argv[1:].index(arg) + 1]
        except IndexError:
            sys.exit('Value of parameter ' + arg + ' is missing!')


def arg_in_arglist(arg, args_list):
    if arg in args_list:
        return True
    else:
        return False


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
    def __init__(self, call, loop=None):
        self.call = call
        self.loop = loop


class MumbleJumble:
    """Represents the Mumble client interacting with users and outputting sound
    """
    def __init__(self):
        with open(os.path.join(SCRIPTPATH, 'config.json')) as json_config_file:
            self.config = json.load(json_config_file)

        pymumble_parameters = {}
        arglist = ['--server', '--port', '--user', '--password', '--certfile', 
                   '--reconnect', '--debug']

        for arg in arglist:
            if arg == '--user':
                try:
                    pymumble_parameters[arg[2:]] = self.config['bot'][arg[2:]][num_scripts()]
                except IndexError:
                    if arg in sys.argv[1:]:
                        pymumble_parameters[arg[2:]] = get_arg_value(arg)
                    else:
                        sys.exit('Usernames already taken')
            else:
                pymumble_parameters[arg[2:]] = self.config['bot'][arg[2:]]
            if arg_in_arglist(arg, sys.argv[1:]):
                pymumble_parameters[arg[2:]] = get_arg_value(arg)
            if arg == '--server':
                if pymumble_parameters['server'] == "":
                    sys.exit('Server address is missing!')

        writepid()

        self.client = pymumble.Mumble(host=pymumble_parameters['server'], 
                                      port=int(pymumble_parameters['port']),
                                      user=pymumble_parameters['user'], 
                                      password=pymumble_parameters['password'],
                                      certfile=pymumble_parameters['certfile'],
                                      reconnect=pymumble_parameters['reconnect'], 
                                      debug=pymumble_parameters['debug'])

        # Sets to client to call command_received when a user sends text
        self.client.callbacks.set_callback('text_received', self.command_received)

        self.audio_queue = [] # Queue of audio ready to be sent
        self.branches = {}

        self.client.start() # Start the mumble thread

        self.volume = 1.00
        self.paused = False
        self.skipLeaf = False
        self.skipBranch = False
        self.reload_count = 0
        self.client.is_ready() # Wait for the connection
        self.client.set_bandwidth(200000)
        self.client.users.myself.unmute() # Be sure the client is not muted
        with open(os.path.join(SCRIPTPATH, 'comment')) as comment:
            self.client.users.myself.comment(comment.read())

        self.load_modules()

        self.ffmpegthread = ffmpegThread(self)
        self.ffmpegthread.start()

        self.loopthread = LoopThread(self)
        self.loopthread.start()

        self.audio_loop() # Loops the main thread

    def load_modules(self):
        print('\nLoading bot modules')
        self.registered_commands = {'c' :clear_queue,
                                    'clear' :clear_queue,
                                    'p' :toggle_pause,
                                    'pause' :toggle_pause,
                                    'q' :print_queue,
                                    'queue' :print_queue,
                                    'r' :reload_modules,
                                    'reload' :reload_modules,
                                    's' :skip,
                                    'seek' :seek,
                                    'skip' :skip,
                                    'v' :chg_vol,
                                    'vol' :chg_vol,
                                    'volume' :chg_vol}
        self.registered_modules = [] # List of module objects

        # Lists modules
        filenames = []
        for fn in os.listdir(os.path.join(SCRIPTPATH, 'modules')):
            if fn.endswith('.py') and not fn.startswith('_'):
                filenames.append(os.path.join(SCRIPTPATH, 'modules', fn))

        # Tries to import modules
        modules = []
        for filename in filenames:
            name = os.path.basename(filename)[:-3]
            try: module = imp.load_source(name, filename)
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

                    if hasattr(module, 'loop'):
                        module_object = MJModule(module.call, module.loop)
                    else:
                        module_object = MJModule(module.call)

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
                    print("Could not register '{0}', for it is missing the 'register' function".format(module), file=sys.stderr)
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
        channel = self.get_current_channel()
        channel.send_text_message(msg)


    def command_received(self, text):
        """Main function that reads commands in chat and outputs accordingly
        Takes text, a class from pymumble.mumble_pb2. Commands have to start with a !
        """
        message = text.message.lstrip().split(' ', 1)
        if message[0].startswith('!'):
            command = message[0][1:]
            arguments = ''.join(message[1]).strip(' ') if len(message) > 1 else ''

            # Module loaded commands
            if command in self.registered_commands.keys():
                self.registered_commands[command](self, command, arguments)
     

    def append_audio(self, audio_file, audio_title, branchname=None, pipe=False):
            self.ffmpegthread.audio2process.append((audio_file, audio_title, branchname, pipe))

    def append_branch(self, branch):
        self.audio_queue.append(branch)
        self.branches[str(branch)] = branch.leaves

    def append_leaf(self, leaf, branch=None):
        if branch is None: #Doesn't need to be in self.branches
            self.audio_queue.append(leaf)
        else:
            if str(branch) in self.branches:
                for i, x in enumerate(self.audio_queue):
                    if str(x) == str(branch):
                        self.audio_queue[i].add(leaf) # Will add to self.branches too
                        break
            else:
                self.append_branch(branch)

    def delete_branch(self, branch_index):
        branch = self.audio_queue[branch_index]
        del self.audio_queue[branch_index]
        del self.branches[str(branch)]

    def delete_leaf(self, leaf_index, branch_index=None):
        if branch_index is None: #Doesn't need to be in self.branches
            del self.audio_queue[leaf_index]
        else:
            self.audio_queue[branch_index].remove_leaf(leaf_index)
            if not self.audio_queue[branch_index]:
                self.delete_branch(branch_index)

    def audio_loop(self):
        """Main loop that sends audio samples to the server. Sends the first
        song in SubThread's song queue
        """
        while True:
            try:
                if self.audio_queue:
                    try:
                        self.leaf = self.audio_queue[0].leaves[0]
                    except:
                        self.leaf = self.audio_queue[0]
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
                                self.delete_branch(0)
                                self.skipBranch = False
                            else:
                                self.delete_leaf(0, 0)

                        else:
                            self.delete_leaf(0)
                    except:
                        pass
                    finally:
                        del self.leaf
                else:
                    time.sleep(0.5)
            except Exception as e:
                print(e)
            except KeyboardInterrupt:
                deletepid()
                sys.exit('Exiting!')


class ffmpegThread(threading.Thread):
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.audio2process = []
        self.parent = parent
        self.daemon = True


    def run(self):
        while True:
            if self.audio2process:
                leaf = handles.Leaf(self.audio2process[0][0], self.audio2process[0][1])
                branchname = self.audio2process[0][2]
                try:
                    leaf = self.process(leaf, self.audio2process[0][3])
                    if branchname is None:
                        branch = None
                    else:
                        branch = handles.Branch(branchname, leaf)
                    self.parent.append_leaf(leaf, branch)
                    del self.audio2process[0]
                except Exception as e:
                    print(e)
                    print('Cannot process audio file, aborting!')
                    del self.audio2process[0]
            else:
                time.sleep(0.5)


    def process(self, leaf, pipe):
        """ Converts and splits the song into the suitable format to stream to
        mumble server (mono PCM 16 bit little-endian), using ffmpeg
        """
        command = ['ffmpeg', '-nostdin', '-i', '-', '-f', 's16le', '-acodec', 
                   'pcm_s16le', '-ac', '1', '-ar', '48000', '-']
        if pipe:
            p = sp.Popen(command, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
            stdout, stderr = p.communicate(input=leaf.file)
        else:
            command[3] = leaf.file
            p = sp.Popen(command, stdout=sp.PIPE, stderr=sp.PIPE)
            stdout, stderr = p.communicate()
        print(stderr)
        counter = 1
        start = stderr.rfind('time=')
        leaf.duration = stderr[start + 5:start + 17]
        with io.BytesIO(stdout) as out:
            while True:
                leaf.samples[counter] = out.read(88200)
                if not leaf.samples[counter]:   #If last fragment is empty
                    leaf.total_samples = counter
                    return leaf
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


if __name__ == '__main__':
    musicbot = MumbleJumble()
