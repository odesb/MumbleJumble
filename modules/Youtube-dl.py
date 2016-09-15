from __future__ import unicode_literals

import threading
import os
import youtube_dl
import time
import subprocess as sp
import random


def register(bot):
    register.singlethread = SingleThread(bot)
    register.plthread = PlaylistThread(bot)


register.commands = ['a', 'add', 'shuffle']
register.enabled = True
register.shuffle = False


def call(bot, command, arguments):
    if command == 'a' or command == 'add':
        url = arguments.replace('<a href="', '')
        end = url.find('">')
        url = url[:end]
        try:
            info = extract_info(url)
        except youtube_dl.DownloadError:
            bot.send_msg_current_channel('Cannot retrieve URL')
            return
        title = info['title']
        try:
            if info['_type'] == 'playlist':
                bot.send_msg_current_channel('Adding <b>{0} - PLAYLIST</b> to the queue'.format(title))
                if register.plthread.isAlive():
                    register.plthread + (url, info)
                else:
                    register.plthread = PlaylistThread(bot)
                    register.plthread + (url, info)
                    register.plthread.start()
        except KeyError:
            bot.send_msg_current_channel('Adding <b>{0}</b> to the queue'.format(title))
            if register.singlethread.isAlive():
                register.singlethread + (url, info)
            else:
                register.singlethread = SingleThread(bot)
                register.singlethread + (url, info)
                register.singlethread.start()

    elif command == 'shuffle':
        if arguments == 'on':
            register.shuffle = True
        elif arguments == 'off':
            register.shuffle = False


def extract_info(url):
    with youtube_dl.YoutubeDL({}) as ydl:
        return ydl.extract_info(url, download=False, process=False)
    

class SingleThread(threading.Thread):
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.new_audio = []
        self.parent = parent
        self.reload_count = self.parent.reload_count
        self.exit = False
        self.daemon = True
        self.current_title = None
        self.download = self.parent.config['youtube-dl']['single']['download']
        if self.download:
            self.dl_folder = os.path.abspath(self.parent.config['youtube-dl']['single']['download_folder'])
            if not os.path.exists(self.dl_folder):
                try:
                    os.mkdir(self.dl_folder)
                except OSError:
                    self.exit = True
                    print('Could not create download folder, aborting!')

    def __add__(self, data):
        self.new_audio.append(data)

    def run(self):
        while self.reload_count == self.parent.reload_count and self.new_audio and not self.exit:
            url = self.new_audio[0][0]
            info = self.new_audio[0][1]
            self.current_title = info['title']
            if self.download:
                file_path = os.path.join(self.dl_folder, self.current_title)
                self.dl_and_append(url, file_path, self.current_title)
            else:
                self.pipe_and_append(url, self.current_title)
            self.current_title = None
            del self.new_audio[0]

    def dl_and_append(self, url, file_path, title, branchname=None):
        try:
            ydl_opts = {'format': 'bestaudio', 'outtmpl': file_path}
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.parent.append_audio(file_path, title, branchname)
        except youtube_dl.DownloadError:
            pass

    def pipe_and_append(self, url, title, branchname=None):
        try:
            command = ['youtube-dl', url, '-f', 'bestaudio', '-o', '-']
            p = sp.Popen(command, stdout=sp.PIPE, stderr=sp.PIPE)
            stdout, stderr = p.communicate()
            print(stderr)
            self.parent.append_audio(stdout, title, branchname, pipe=True)
        except youtube_dl.DownloadError:
            pass


class PlaylistThread(SingleThread):
    def __init__(self, bot):
        SingleThread.__init__(self, bot)
        self.buffer_size = self.parent.config['youtube-dl']['playlist']['buffer_size']
        self.download = self.parent.config['youtube-dl']['playlist']['download']
        if self.download:
            self.dl_folder = os.path.abspath(self.parent.config['youtube-dl']['playlist']['download_folder'])
            if not os.path.exists(self.dl_folder):
                try:
                    os.mkdir(self.dl_folder)
                except OSError:
                    self.exit = True
                    print('Could not create download folder, aborting!')

    def run(self):
        while self.reload_count == self.parent.reload_count and self.new_audio and not self.exit:
            info = self.new_audio[0][1]
            branchname = info['title'] + '<b> - PLAYLIST</b>'
            self.new_audio[0] = [('https://www.youtube.com/watch?v=' + x['url'], x['title']) for x in info['entries']]

            while self.new_audio[0]:
                if register.shuffle:
                    current = random.choice(self.new_audio[0])
                else:
                    current = self.new_audio[0][0]
                self.current_title = current[1]
                if self.download:
                    playlist_path = os.path.join(self.dl_folder, info['title'])
                    try:
                        os.mkdir(playlist_path)
                    except OSError:
                        print('Cannot create download folder for current playlist, aborting!')
                        return
                    file_path = os.path.join(playlist_path, self.current_title)
                    self.dl_and_append(current[0], file_path, self.current_title, branchname)
                else:
                    self.pipe_and_append(current[0], self.current_title, branchname)
                self.new_audio[0].remove(current)
                self.current_title = None
                time.sleep(0.5)
                try:
                    mirror = self.parent.queue.build_mirror()
                    while len(mirror[branchname]) >= self.buffer_size:
                        time.sleep(2)
                        mirror = self.parent.queue.build_mirror()
                except KeyError:
                    break
            del self.new_audio[0]


def queue_append():
    q = ''
    if register.singlethread.isAlive() and register.singlethread.current_title is not None:
        q += '<br />{0}<b> - Downloading</b>'.format(register.singlethread.current_title)
    if register.plthread.isAlive() and register.plthread.current_title is not None:
        q += '<br />{0}<b> - Downloading</b>'.format(register.plthread.current_title)
    return q
