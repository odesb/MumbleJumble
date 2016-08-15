from collections import deque
import threading
import time
import os
import subprocess as sp


def call(bot, command_used, arguments):

    yt_thread = YTThread(bot)
    bot.threads.append(yt_thread)
    t_index = bot.threads.index(yt_thread)
    bot.threads[t_index].daemon = True
    bot.threads[t_index].start()
    
    if arguments:
        if command_used == 'a' or command_used == 'add':
            try:
                short_url = get_short_url(arguments)
            except:
                bot.send_msg_current_channel('Could not retrieve URL')
                return
            bot.send_msg_current_channel('Adding ' + '<b>' + short_url
                                         + '</b>' + ' to queue.')
            # Subthread will process its newly populated url_list
            bot.threads[t_index].url_list.append(short_url)


def get_short_url(message):
    """Gives a shorter version of URL, useful to store files"""
    patterns = ['watch?v=', 'youtu.be/']
    for i in patterns:
        if i in message:
            start = message.find(i) + len(i)
            return message[start:start + 11]
    


    
class YTThread(threading.Thread):
    """A subthread of the main thread, takes care of downloading, converting and
    splitting audio files, while the main thread is busy outputting sound to the
    server
    """
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.url_list = deque([]) #Queue of URL to process
        self.parent = parent
        self.dl_folder = parent.dl_folder


    def run(self):
        while True:
            if len(self.url_list) > 0: #List gets populated when !a is invoked
                song = Song(self.url_list[0]) #Takes care of the first one
                song.dl_folder = self.dl_folder
                if not os.path.exists(self.dl_folder + song.short_url):
                    song.download()
                song.convert_split()
                self.parent.audio_queue.append(song)
                self.url_list.popleft() #Done with processing the first URL
            else:
                time.sleep(0.1)


class Song:
    """Represents a song processed by SubThread and streamed by MumbleJukeBox"""
    def __init__(self, short_url):
        self.samples = dict() # Will contain each samples and total # of samples
        self.short_url = short_url # Youtube short URL
        self.dl_folder = None
        self.pipe = None


    def download(self):
        """Downloads music using youtube-dl in the specified dl_folder"""
        if not os.path.exists(self.dl_folder):
            try:
                os.mkdir(self.dl_folder)
            except OSError:
                print('Could not create dl_folder, exiting!')
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

def register(bot):
    print('Registering bot')


register.commands=['a', 'add']
