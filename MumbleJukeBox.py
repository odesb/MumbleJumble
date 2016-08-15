#!/usr/bin/env python
from __future__ import print_function

from collections import deque
import os
import imp
import sys
import subprocess as sp
import audioop
import time
import threading

# Add pymumble folder to python PATH for importing
sys.path.append(os.path.join(os.path.dirname(__file__), "pymumble"))
import pymumble

def get_arg_value(arg, args_list, default=None):
    """Retrieves the values associated to command line arguments
    Possible arguments:
    --server    Mumble server address
    --port      Mumble server port
    --user      Mumble bot's username
    --password  Mumble server password
    --certfile  Mumble certification
    --reconnect Bot reconnects to the server if disconnected
    --debug     Debug=True will generate a lot of stdout messages
    --dl_folder User set location of the downloaded songs
    """
    if arg in args_list:
        return args_list[args_list.index(arg) + 1]
    elif default != None or arg == '--certfile':
        # Falls back to default if no parameter given
        # Parameter --certfile's default has to be None
        return default
    else:
        sys.exit('Parameter ' + arg + ' is missing!')


def get_dl_folder():
    """Gets the path of the user set or default download folder"""
    return get_arg_value('--dl_folder', sys.argv[1:], default='./.song_library/')


def get_short_url(message):
    """Gives a shorter version of URL, useful to store files"""
    patterns = ['watch?v=', 'youtu.be/']
    for i in patterns:
        if i in message:
            start = message.find(i) + len(i)
            return message[start:start + 11]


class MumbleJukeBox:
    """Represents the Mumble client interacting with users and outputting sound
    """
    def __init__(self):
        host = get_arg_value('--server', sys.argv[1:])
        port = int(get_arg_value('--port', sys.argv[1:], default=64738))
        user = get_arg_value('--user', sys.argv[1:], default='@MumbleJukeBox')
        password = get_arg_value('--password', sys.argv[1:], default='')
        certfile = get_arg_value('--certfile', sys.argv[1:], default=None)
        reconnect = get_arg_value('--reconnect', sys.argv[1:], default=False)
        debug = get_arg_value('--debug', sys.argv[1:], default=False)

        self.bot = pymumble.Mumble(host=host, port=port, user=user, password=
                                   password, certfile=certfile,
                                   reconnect=reconnect, debug=debug)

        # Sets to bot to call command_received when a user sends text
        self.bot.callbacks.set_callback('text_received', self.command_received)

        self.registered_commands = {}

        self.bot.start() # Start the mumble thread
        self.subthread = SubThread()
        self.subthread.daemon = True
        self.subthread.start()

        self.setup()
        self.loop() # Loops the main thread

    def setup(self):
        print()
        print("Loading bot modules")
        self.registered_commands = {}
        self.volume = 1.00
        self.paused = False
        self.skipFlag = False
        self.current_song_sample = 0
        self.bot.is_ready() # Wait for the connection
        self.bot.set_bandwidth(200000)
        self.bot.users.myself.unmute() # Be sure the bot is not muted

        home = os.path.dirname(__file__)
        filenames = []
        for fn in os.listdir(os.path.join(home, 'modules')): 
            if fn.endswith('.py') and not fn.startswith('_'): 
                filenames.append(os.path.join(home, 'modules', fn))

        modules = []
        for filename in filenames: 
            name = os.path.basename(filename)[:-3]
            try: module = imp.load_source(name, filename)
            except Exception as e:
                print(e)
            modules.append(module)
        for module in modules:
            print("Loaded module '{0}'".format(module.__name__))
            if hasattr(module, 'register'): 
                module.register(self)
                for command in module.register.commands:
                    if command in self.registered_commands.keys():
                        print("Command '{0}' already registered by another module".format(command), file=sys.stderr)
                        sys.exit(1)
                    else:
                        print("  Registering '{0}' - for module '{1}'".format(command, module.__name__))
                        self.registered_commands[command] = module.call
            else:
                print("Could not register '{0}', for it is missing the 'register' function".format(module), file=sys.stderr)

    def get_current_channel(self):
        """Get the bot's current channel (a dict)"""
        try:
            return self.bot.channels[self.bot.users.myself['channel_id']]
        except KeyError:
            print('Currently assuming bot is in channel 0, try moving it')
            return self.bot.channels[0]


    def send_msg_current_channel(self, msg):
        """Send a message in the bot's current channel"""
        channel = self.get_current_channel()
        channel.send_text_message(msg)


    def command_received(self, text):
        """Main function that reads commands in chat and outputs accordingly
        Takes text, a class from pymumble.mumble_pb2
        The main loop pickups the change of states and the non-empty song queue
        Commands have to start with a !:
        a, add          Adds a song from URL to the current queue
        c, clear        Clears the queue and stops current song
        p, pause        Pause the current playing song
        q, queue        Displays the current queue in the chat
        s, skip         Skips the song currently playing
        v, vol, volume  Returns the current volume or changes it
        """
        message = text.message
        if message[0] == '!':
            message = message[1:].split(' ', 1)
            command = message[0]
            if len(message) > 1:
                parameter = message[1]
                if command == 'a' or command == 'add':
                    try:
                        short_url = get_short_url(parameter)
                    except:
                        self.send_msg_current_channel('Could not retrieve URL')
                        return
                    self.send_msg_current_channel('Adding ' + '<b>' + short_url
                                                  + '</b>' + ' to queue.')
                    # Subthread will process its newly populated url_list
                    self.subthread.url_list.append(short_url)

                elif command == 'v' or command == 'vol' or command == 'volume':
                    try:
                        self.volume = float(parameter)
                        self.send_msg_current_channel('Changing volume to '
                                                  + '<b>' + str(self.volume)
                                                  + '</b>')
                    except ValueError:
                        self.send_msg_current_channel('Not a valid value!')

            elif command == 'c' or command == 'clear':
                self.skipFlag = True
                self.subthread.url_list = deque([])
                self.subthread.song_queue = deque([])

            elif command == 'p' or command == 'pause':
                self.toggle_pause()

            elif command == 'q' or command == 'queue':
                self.send_msg_current_channel(self.printable_queue())

            elif command == 's' or command == 'skip':
                self.skipFlag = True

            elif command == 'v' or command == 'vol' or command == 'volume':
                self.send_msg_current_channel('Current volume: ' + '<b>'
                                              + str(self.volume) + '</b>')
            if command in self.registered_commands.keys():
                command_used = message[0]
                arguments = message[1:]
                self.registered_commands[command](self, str(command_used), str(arguments))


    def printable_queue(self):
        """Creates a printable queue suited for the Mumble chat. Associated with
        the queue command. Checks the processing and processed song lists of the
        subthread. Possible states: Paused, Playing, Ready, Downloading.
        """
        queue = []
        if len(self.subthread.song_queue) + len(self.subthread.url_list) == 0:
            return 'Queue is empty'
        else:
            for i in range(len(self.subthread.song_queue)):
                if i == 0:
                    if self.paused:
                        queue.append('%s <b>Paused - %i %%</b>' %
                                (self.subthread.song_queue[i].short_url,
                                 self.current_song_status()))
                    elif not self.paused:
                        queue.append('%s <b>Playing - %i %%</b>' %
                                (self.subthread.song_queue[i].short_url,
                                 self.current_song_status()))
                else:
                    queue.append(self.subthread.song_queue[i].short_url + ' <b>Ready</b>')
            for j in range(len(self.subthread.url_list)):
                queue.append(self.subthread.url_list[j] + ' <b>Downloading</b>')
            return ', '.join(queue)


    def toggle_pause(self):
        """Toggle the pause command"""
        if self.paused:
            self.paused = False
        else:
            self.paused = True

    def current_song_status(self):
        """Returns the completion of the song in %. Associated with the queue
        command.
        """
        return float(self.current_song_sample) / float(
                self.subthread.song_queue[0].samples['total_samples']) * 100


    def loop(self):
        """Main loop that sends audio samples to the server. Sends the first
        song in SubThread's song queue
        """
        while True:
            if len(self.subthread.song_queue) > 0:
                for i in range(self.subthread.song_queue[0].samples['total_samples']):
                    self.current_song_sample = i
                    while self.paused:
                        time.sleep(0.1)
                    while self.bot.sound_output.get_buffer_size() > 0.5:
                        time.sleep(0.01)
                    if not self.skipFlag:
                        self.bot.sound_output.add_sound(audioop.mul(
                                        self.subthread.song_queue[0].samples[i],
                                        2, self.volume))
                    elif self.skipFlag:
                        self.skipFlag = False
                        break
                try:
                    # Removes the first song from the queue
                    # Will fail if clear command is passed, not a problem though
                    self.subthread.song_queue.popleft()
                except:
                    pass
                finally:
                    time.sleep(1) # To allow time between songs
            else:
                time.sleep(0.5)


class SubThread(threading.Thread):
    """A subthread of the main thread, takes care of downloading, converting and
    splitting audio files, while the main thread is busy outputting sound to the
    server
    """
    def __init__(self):
        threading.Thread.__init__(self)
        self.url_list = deque([]) #Queue of URL to process
        self.song_queue = deque([]) #Queue of split songs ready to be sent by
                                    #the main loop to the server

    def run(self):
        while True:
            if len(self.url_list) > 0: #List gets populated when !a is invoked
                song = Song(self.url_list[0]) #Takes care of the first one
                if not os.path.exists(song.dl_folder + song.short_url):
                    song.download()
                song.convert_split()
                self.song_queue.append(song)
                self.url_list.popleft() #Done with processing the first URL
            else:
                time.sleep(0.1)


class Song:
    """Represents a song processed by SubThread and streamed by MumbleJukeBox"""
    def __init__(self, short_url):
        self.samples = dict() # Will contain each samples and total # of samples
        self.short_url = short_url # Youtube short URL
        self.dl_folder = get_dl_folder()
        self.pipe = None


    def download(self):
        """Downloads music using youtube-dl in the specified dl_folder"""
        if not os.path.exists(self.dl_folder):
            try:
                os.mkdir(self.dl_folder)
            except OSError:
                sys.exit('Could not create dl_folder, exiting!')
        command = ['youtube-dl', 'https://www.youtube.com/watch?v=' + self.short_url,
                   '-f', '140', '-o', self.dl_folder + self.short_url]
        try:
            sp.call(command)
        except OSError:
            sys.exit('Cannot download file, exiting!')


    def convert_split(self):
        """ Converts and splits the song into the suitable format to stream to
        mumble server (mono PCM 16 bit little-endian), using ffmpeg
        """
        command = ["ffmpeg", '-i', self.dl_folder + self.short_url, '-f',
                   's16le', '-acodec', 'pcm_s16le', '-ac', '1', '-ar',
                   '48000', '-']
        self.pipe = sp.Popen(command, stdout=sp.PIPE)
        counter = 0
        while True:
            self.samples[counter] = self.pipe.stdout.read(88200)
            if len(self.samples[counter]) == 0:
                self.samples['total_samples'] = counter
                return
            counter += 1


if __name__ == '__main__':
    musicbot = MumbleJukeBox()
