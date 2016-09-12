class Leaf:
    """Represents a complete audio file sent to the server by MumbleJumble"""
    def __init__(self, audio_file, audio_title):
        self.file = audio_file
        self.title = audio_title
        self.duration = None
        self.total_samples = None
        self.samples = {}
        self.current_sample = 1

    def get_sample_len(self):
        """Get length of sample in seconds"""
        return duration2sec(self.duration) / float(self.total_samples)

    def printable_queue_format(self):
        return (self.title, '{0}/{1} ({2}%)'.format(self.get_current_time()[:-3],
                                                    self.duration[:-4],
                                                    int(self.current_song_status())))


    def get_current_time(self):
        """Associated with the queue command"""
        current_sec = self.current_sample * self.get_sample_len()
        return sec2duration(current_sec)
    

    def current_song_status(self):
        """Returns the completion of the song in %. Associated with the queue
        command.
        """
        return float(self.current_sample) / float(self.total_samples) * 100


    def seek(self, seconds):
        self.current_sample = int(seconds / self.get_sample_len()) + 1


class Branch:
    def __init__(self, title, initleaf):
        self.title = title
        self.leaves = [initleaf]
       
    def __str__(self):
        return self.title

    def add(self, leaf):
        self.leaves.append(leaf)

    def remove_leaf(self, index):
        del self.leaves[index]



def duration2sec(duration):
    seconds = float(duration[8:11])
    seconds += float(duration[6:8])
    seconds += float(duration[3:5]) * 60
    seconds += float(duration[0:2]) * 3600
    return seconds


def sec2duration(seconds):
    hours = str(int(seconds / 3600)).zfill(2)
    rem = seconds % 3600
    minutes = str(int(rem / 60)).zfill(2)
    seconds = str(int(rem % 60)).zfill(2)
    milli = str(float(rem % 60 / 10))[1:4]
    return '{0}:{1}:{2}{3}'.format(hours, minutes, seconds, milli)


