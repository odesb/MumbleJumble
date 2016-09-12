from __future__ import unicode_literals

import threading
import os
import youtube_dl
import time
import subprocess as sp
import random


def register(bot):
    register.thread = YTThread(bot)


register.commands = ['a', 'add', 'shuffle']
register.enabled = True


def call(bot, command, arguments):
    if command == 'a' or command == 'add':
        url = arguments.replace('<a href="', '')
        end = url.find('">')
        url = url[:end]
        info = extract_info(url)
        title = info['title']
        try:
            if info['_type'] == 'playlist':
                bot.send_msg_current_channel('Adding <b>{0} - PLAYLIST</b> to the queue'.format(title))
                package = (url, info, 'playlist')
        except KeyError:
            bot.send_msg_current_channel('Adding <b>{0}</b> to the queue'.format(title))
            package = (url, info, 'single')
        # Subthread will process its newly populated audio list
        if register.thread.isAlive():
            register.thread.new_audio.append(package)
        else:
            register.thread = YTThread(bot)
            register.thread.new_audio.append(package)
            register.thread.start()

    elif command == 'shuffle':
        register.thread.shuffle = True
        

def extract_info(url):
    with youtube_dl.YoutubeDL({}) as ydl:
        return ydl.extract_info(url, download=False, process=False)
    

class YTThread(threading.Thread):
    """A subthread of the main thread, takes care of downloading, converting and
    splitting audio files, while the main thread is busy outputting sound to the
    server
    """
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.new_audio = [] #Queue of URL to process
        self.parent = parent
        self.reload_count = self.parent.reload_count
        self.dl_folder = os.path.abspath(self.parent.config['youtube-dl']['download_folder'])
        self.dl_playlist = self.parent.config['youtube-dl']['download_playlist']
        self.exit = False
        self.daemon = True
        self.shuffle = False
        if not os.path.exists(self.dl_folder):
            try:
                os.mkdir(self.dl_folder)
            except OSError:
                self.exit = True
                print('Could not create download folder, aborting!')


    def run(self):
        while self.reload_count == self.parent.reload_count and self.new_audio:
            url = self.new_audio[0][0]
            info = self.new_audio[0][1]
            if self.new_audio[0][2] == 'playlist':
                audio_q_format = info['title'] + '<b> - PLAYLIST</b>'
                self.new_audio[0] = [('https://www.youtube.com/watch?v=' + x['url'], x['title']) for x in info['entries']]
                playlist_added = False
                exit_playlist = False
                while self.new_audio[0] and not exit_playlist:
                    if not self.shuffle:
                        current = self.new_audio[0][0]
                    else:
                        current = random.choice(self.new_audio[0])
                    if self.dl_playlist:
                        file_path = os.path.join(self.dl_folder, current[1])
                        ydl_opts = {'format': 'bestaudio','outtmpl': file_path}
                        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                            try:
                                ydl.download([current[0]])
                            except Exception as e:
                                print(e)
                        self.parent.append_audio(file_path, current[1].encode('ascii', 'ignore'), audio_q_format)
                    else:
                        command = ['youtube-dl', current[0], '-f', 'bestaudio', '-o', '-']
                        p = sp.Popen(command, stdout=sp.PIPE, stderr=sp.PIPE)
                        stdout, stderr = p.communicate()
                        print(stderr)
                        self.parent.append_audio(stdout, current[1].encode('ascii', 'ignore'), audio_q_format, pipe=True)
                    self.new_audio[0].remove(current)
                    time.sleep(8)
                    while not playlist_added:
                        if audio_q_format in self.parent.branches:
                                playlist_added = True
                        time.sleep(1)
                    while audio_q_format in self.parent.branches and len(self.parent.branches[audio_q_format]) >= 2:
                        time.sleep(3)
                    if audio_q_format not in self.parent.branches:
                        exit_playlist = True


            elif self.new_audio[0][2] == 'single':
                title = info['title']
                file_path = os.path.join(self.dl_folder, title)
                if os.path.exists(file_path):
                    self.parent.append_audio(file_path, title.encode('ascii', 'ignore'))
                    del self.new_audio[0]
                else:
                    ydl_opts = {'format': 'bestaudio', 'outtmpl': file_path}
                    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                        try:
                            ydl.download([url])
                        except Exception as e:
                            print(e)
                    self.parent.append_audio(file_path, title.encode('ascii', 'ignore'))
                    del self.new_audio[0]
