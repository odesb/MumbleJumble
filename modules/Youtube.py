from collections import deque
import threading
import time
import os
import subprocess as sp
import pafy



def register(bot):
    bot.threads['yt_thread'] = YTThread(bot)
    bot.threads['yt_thread'].daemon = True
    bot.threads['yt_thread'].start()


register.commands = ['a', 'add']


def call(bot, command_used, arguments):
    if arguments:
        if command_used == 'a' or command_used == 'add':
            short_url = get_short_url(arguments)
            if short_url == -1:
                bot.send_msg_current_channel('Could not retrieve URL')
                return
            # Subthread will process its newly populated new songs list
            bot.threads['yt_thread'].new_songs.append(Song(short_url))


def get_short_url(message):
    """Gives a shorter version of URL, useful to store files"""
    patterns = ['watch?v=', 'youtu.be/']
    for i in patterns:
        if i in message:
            start = message.find(i) + len(i)
            return message[start:start + 11]
    return -1
    

def get_audio_title(short_url):
    url = 'https://www.youtube.com/watch?v=' + short_url
    return pafy.new(url).title


class YTThread(threading.Thread):
    """A subthread of the main thread, takes care of downloading, converting and
    splitting audio files, while the main thread is busy outputting sound to the
    server
    """
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.new_songs = deque([]) #Queue of URL to process
        self.parent = parent
        self.index = None


    def run(self):
        while True:
            if len(self.new_songs) > 0: #List gets populated when !a is invoked
                song = self.new_songs[0]
                self.parent.send_msg_current_channel('Adding ' + '<b>' 
                                                     + song.title
                                                     + '</b>' + ' to the queue.')
                if not os.path.exists(song.dl_folder + song.title):
                    song.download()
                song.convert_split()
                self.parent.audio_queue.append(song)
                self.new_songs.popleft() #Done with processing the first URL
            else:
                time.sleep(0.1)


class Song:
    """Represents a song processed by SubThread and streamed by MumbleJukeBox"""
    def __init__(self, short_url):
        self.samples = dict() # Will contain each samples and total # of samples
        self.short_url = short_url # Youtube short URL
        self.title = get_audio_title(self.short_url)
        self.dl_folder = './.song_library/'
        self.pipe = None


    def download(self):
        """Downloads music using youtube-dl in the specified dl_folder"""
        if not os.path.exists(self.dl_folder):
            try:
                os.mkdir(self.dl_folder)
            except OSError:
                print('Could not create dl_folder, exiting!')
        command = ['youtube-dl', 'https://www.youtube.com/watch?v=' + self.short_url,
                   '-f', '140', '-o', self.dl_folder + self.title]
        try:
            sp.call(command)
        except OSError:
            sys.exit('Cannot download file, exiting!')


    def convert_split(self):
        """ Converts and splits the song into the suitable format to stream to
        mumble server (mono PCM 16 bit little-endian), using ffmpeg
        """
        command = ["ffmpeg", '-i', self.dl_folder + self.title, '-f',
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

