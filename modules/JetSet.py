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
        bot.send_msg_current_channel('You must specify the radio station: {}'.format(MP3LISTS.keys()))
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
    def __init__(self, parent, station_list):
        threading.Thread.__init__(self)
        self.parent = parent
        self.reloadcount = self.parent.reload_count
        self.daemon = True
        self.station_list = station_list
        self.branchname = 'Jet Set Radio Live <b>- STREAM</b>'

        jetsetlist = urllib2.urlopen(self.station_list)
        raw_string = jetsetlist.read()
        raw_string = raw_string.replace('filesListArray[filesListArray.length] = "', '')
        raw_string.find('length] = "')
        raw_string = raw_string.replace('\r\n', '')
        self.mp3_list = raw_string.split('";')
        del self.mp3_list[-1]
        print(self.mp3_list)

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
        song_title = random.choice(self.mp3_list)
        f = urllib2.urlopen('{0}{1}.mp3'.format(self.station_list[:-8], song_title.replace(' ', '%20')))
        self.parent.append_audio(f.read(), song_title, self.branchname, pipe=True)
