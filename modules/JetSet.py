from __future__ import unicode_literals

import urllib2
import random
import threading
import time

MP3LISTS = {'default': 'http://jetsetradio.live/audioplayer/audio/~list.js',
            'poisonjam': 'http://jetsetradio.live/audioplayer/audio/poisonjam/~list.js',
            'noisetanks': 'http://jetsetradio.live/audioplayer/audio/noisetanks/~list.js',
            'loveshockers': 'http://jetsetradio.live/audioplayer/audio/loveshockers/~list.js',
            'rapid99': 'http://jetsetradio.live/audioplayer/audio/rapid99/~list.js',
            'immortals': 'http://jetsetradio.live/audioplayer/audio/immortals/~list.js',
            'goldenrhinos': 'http://jetsetradio.live/audioplayer/audio/goldenrhinos/~list.js'}


def register(bot):
    register.JetSetRadio = JetSetRadioPlayer(bot, MP3LISTS['default'])

register.commands = ['jetset']
register.enabled = True


def call(bot, command, arguments):
    if arguments == '':
        for station in MP3LISTS.keys():
            arguments += '<b>{}</b>, '.format(station)
        bot.send_msg_current_channel('You must specify the radio station: {}'.format(arguments))
    elif register.JetSetRadio.isAlive():
        pass
    else:
        try:
            register.JetSetRadio = JetSetRadioPlayer(bot, MP3LISTS[arguments])
            register.JetSetRadio.start()
            bot.send_msg_current_channel('Starting <b>Jet Set Radio Live - {}</b>'.format(arguments))
        except KeyError:
            bot.send_msg_current_channel('Invalid radio station')
        

class JetSetRadioPlayer(threading.Thread):
    def __init__(self, parent, station_url):
        threading.Thread.__init__(self)
        self.parent = parent
        self.station_url = station_url
        self.reloadcount = self.parent.reload_count
        self.daemon = True
        self.mp3list = retrieve_mp3list(station_url)
        self.branchname = 'Jet Set Radio Live <b>- STREAM</b>'

    def run(self):
        while self.reloadcount == self.parent.reload_count:
            self.play_song()
            time.sleep(0.5)
            try:
                mirror = self.parent.build_mirror()
                while len(mirror[self.branchname]) >= 3:
                    time.sleep(2)
                    mirror = self.parent.build_mirror()
            except KeyError:
                return

    def play_song(self):
        song_title = random.choice(self.mp3list)
        f = urllib2.urlopen('{0}{1}.mp3'.format(self.station_url[:-8], song_title.replace(' ', '%20')))
        self.parent.append_audio(f.read(), song_title, self.branchname, pipe=True)


def retrieve_mp3list(url):
    l = urllib2.urlopen(url)
    lines = l.readlines()
    mp3_list = []
    for line in lines:
        start = line.find('= "') + 3
        end = line.find('";')
        mp3_list.append(line[start:end])
    return mp3_list
