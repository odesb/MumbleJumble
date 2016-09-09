from collections import deque
import threading
import time
import os
import subprocess as sp
import pafy
import traceback



def register(bot):
    register.thread = YTThread(bot)
    register.thread.daemon = True
    register.thread.start()


register.commands = ['a', 'add']
register.enabled = True


def call(bot, command_used, arguments):
    url = arguments.replace('<a href="', '')
    end = url.find('">')
    url = url[:end]
    short_url = get_short_url(arguments)
    if short_url == -1:
        register.thread.new_audio.append(YTAudio(url))
    # Subthread will process its newly populated audio list
    else:
        register.thread.new_audio.append(YTAudio(url, short_url))
    

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
        self.new_audio = deque([]) #Queue of URL to process
        self.parent = parent
        self.reload_count =  self.parent.reload_count
        self.dl_folder =  os.path.abspath(self.parent.config['youtube']['download_folder'])
        if not os.path.exists(self.dl_folder):
            os.mkdir(self.dl_folder)


    def run(self):
        while self.reload_count == self.parent.reload_count:
            if len(self.new_audio) > 0: #List gets populated when !a is invoked
                ytaudio = self.new_audio[0]
                try:
                    self.parent.send_msg_current_channel('Adding <b>{0}</b> to the queue'.format(ytaudio.title))
                except UnicodeEncodeError:
                    ytaudio.title = ytaudio.short_url
                    self.parent.send_msg_current_channel('Adding <b>{0}</b> to the queue'.format(ytaudio.title))
                ytaudio.path = os.path.join(self.dl_folder, ytaudio.title)
                if not os.path.exists(ytaudio.path):
                    try:
                        self.download(ytaudio)
                        self.parent.append_audio(ytaudio.path, 'complete', ytaudio.title)
                        self.new_audio.popleft() #Done with processing the first URL
                    except:
                        print('Cannot download file, aborting!')
                        self.new_audio.popleft()
                        break
                else:
                    self.parent.append_audio(ytaudio.path, 'complete', ytaudio.title)
                    self.new_audio.popleft()
            else:
                time.sleep(0.5)


    def download(self, ytaudio):
        """Downloads music using youtube-dl in the specified dl_folder"""
        command = ['youtube-dl', ytaudio.url, '-o', ytaudio.path]
        try:
            sp.call(command)
        except OSError:
            print('Cannot download file, aborting!')


class YTAudio:
    """Represents an audio handle processed by YTThread and streamed by MumbleJumble"""
    def __init__(self, url, short_url=None):
        self.url = url
        self.short_url = short_url # Youtube short URL
        self.title = 'test'
        if self.short_url != None:
            self.title = get_audio_title(self.short_url)
