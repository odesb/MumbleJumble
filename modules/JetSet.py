import urllib2
import random
import threading
import time

MP3LIST = 'http://jetsetradio.live/audioplayer/audio/~list.js'

def register(bot):
    register.JetSetRadio = JetSetRadioPlayer(bot)

register.commands = ['jetset']
register.enabled = True


def call(bot, command, arguments):
    if register.JetSetRadio.isAlive():
        pass
    else:
        register.JetSetRadio.run()
        

class JetSetRadioPlayer(threading.Thread):
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.parent = parent
        self.reloadcount = self.parent.reload_count
        self.exit = False

        jetsetlist =  urllib2.urlopen(MP3LIST)
        raw_string = jetsetlist.read()
        raw_string = raw_string.replace('filesListArray[filesListArray.length] = "', '')
        raw_string = raw_string.replace('\r\n', '')
        self.mp3_list = raw_string.split('";')
        del self.mp3_list[-1]

    def run(self):
        if self.parent.startStream == True:
            self.exit = True
        while self.reloadcount == self.parent.reload_count and not self.exit:
            self.parent.startStream = True 
            if len(self.parent.audio_queue) == 0:
                song = random.choice(self.mp3_list)
                f = urllib2.urlopen('http://jetsetradio.live/audioplayer/audio/{0}.mp3'.format(song.replace(' ', '%20')))
                fragment = f.read(88200 * 10)
                while len(fragment) > 0:
                    self.parent.append_audio(fragment, 'stream', song)
                    fragment = f.read(88200 * 10)
            time.sleep(1)
