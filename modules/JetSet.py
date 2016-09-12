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
        bot.send_msg_current_channel('Starting the Jet Set Radio Live stream')
        register.JetSetRadio.start()
        

class JetSetRadioPlayer(threading.Thread):
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.parent = parent
        self.reloadcount = self.parent.reload_count
        self.daemon = True
        self.exit = False

        jetsetlist =  urllib2.urlopen(MP3LIST)
        raw_string = jetsetlist.read()
        raw_string = raw_string.replace('filesListArray[filesListArray.length] = "', '')
        raw_string = raw_string.replace('\r\n', '')
        self.mp3_list = raw_string.split('";')
        del self.mp3_list[-1]

    def run(self):
        self.play_song()
        while self.reloadcount == self.parent.reload_count and not self.exit:
            if len(self.parent.audio_queue) > 0 and isinstance(self.parent.audio_queue[0], list):
                if self.parent.audio_queue[0][0] == 'Jet Set Radio Live <b>- STREAM</b>' and len(self.parent.audio_queue[0]) < 3:
                    self.play_song()
            time.sleep(15)

    def play_song(self):
        song_title = random.choice(self.mp3_list)
        f = urllib2.urlopen('http://jetsetradio.live/audioplayer/audio/{0}.mp3'.format(song_title.replace(' ', '%20')))
        self.parent.append_audio(f.read(), song_title, 'Jet Set Radio Live <b>- STREAM</b>', pipe=True)
