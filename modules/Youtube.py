from collections import deque
import threading
import time
import os
import subprocess as sp
import pafy



def register(bot):
    register.thread = YTThread(bot)
    register.thread.daemon = True
    register.thread.start()


register.commands = ['a', 'add']
register.enabled = True


def call(bot, command_used, arguments):
    short_url = get_short_url(arguments)
    if short_url == -1:
        bot.send_msg_current_channel('Could not retrieve URL')
        return
    # Subthread will process its newly populated songs list
    register.thread.new_songs.append(Song(short_url))
    

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
    return pafy.new(url).title.replace('/', '')


class YTThread(threading.Thread):
    """A subthread of the main thread, takes care of downloading, converting and
    splitting audio files, while the main thread is busy outputting sound to the
    server
    """
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.new_songs = deque([]) #Queue of URL to process
        self.parent = parent
        self.reload_count =  self.parent.reload_count


    def run(self):
        while self.reload_count == self.parent.reload_count:
            if len(self.new_songs) > 0: #List gets populated when !a is invoked
                song = self.new_songs[0]
                try:
                    self.parent.send_msg_current_channel('Adding <b>{0}</b> to the queue'.format(song.title))
                except UnicodeEncodeError:
                    song.title = song.short_url
                    self.parent.send_msg_current_channel('Adding <b>{0}</b> to the queue'.format(song.title))
                if not os.path.exists(song.dl_folder + song.title):
                    try:
                        song.download()
                        self.parent.append_audio(song.path, 'complete', song.title)
                        self.new_songs.popleft() #Done with processing the first URL
                    except:
                        print('Cannot download file, aborting!')
                        self.new_songs.popleft()
                        break
                else:
                    song.path = song.dl_folder + song.title
                    self.parent.append_audio(song.path, 'complete', song.title)
                    self.new_songs.popleft()
            else:
                time.sleep(0.5)


class Song:
    """Represents a song processed by SubThread and streamed by MumbleJumble"""
    def __init__(self, short_url):
        self.short_url = short_url # Youtube short URL
        self.title = get_audio_title(self.short_url)
        self.dl_folder = './.song_library/'


    def download(self):
        """Downloads music using youtube-dl in the specified dl_folder"""
        if not os.path.exists(self.dl_folder):
            try:
                os.mkdir(self.dl_folder)
            except OSError:
                print('Could not create dl_folder, aborting!')
        command = ['youtube-dl', 'https://www.youtube.com/watch?v=' + self.short_url,
                   '-f', '140', '-o', self.dl_folder + self.title]
        try:
            sp.call(command)
            self.path = self.dl_folder + self.title
        except OSError:
            print('Cannot download file, aborting!')
