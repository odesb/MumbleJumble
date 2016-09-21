class Leaf:
    """Represents an audio file sent to the server by MumbleJumble"""
    def __init__(self, audio_file, audio_title, pipe):
        self.file = audio_file
        self.title = audio_title
        self.branch = None
        self.pipe = pipe
        self.duration = None
        self.total_samples = None
        self.samples = {}
        self.current_sample = 1


    def get_sample_length(self):
        """Get length of sample in seconds"""
        return duration2sec(self.duration) / float(self.total_samples)

    def get_time_elapsed(self):
        """Associated with the queue command"""
        current_sec = self.current_sample * self.get_sample_length()
        return sec2duration(current_sec)
 
    def get_percent_elapsed(self):
        """Returns the completion of the song in %. Associated with the queue
        command.
        """
        return float(self.current_sample) / float(self.total_samples) * 100

    def leaf_status(self):
        return '{0}/{1} ({2}%)'.format(self.get_time_elapsed()[:-3],
                                       self.duration[:-4],
                                       int(self.get_percent_elapsed()))

    def seek(self, seconds):
        self.current_sample = int(seconds / self.get_sample_length()) + 1


class Branch:
    def __init__(self, title, initleaf):
        self.title = title
        initleaf.branch = self
        self.leaves = [initleaf]
       
    def __iter__(self):
        for leaf in self.leaves:
            yield leaf

    def __len__(self):
        return len(self.leaves)

    def __contains__(self, leaf):
        if leaf in self.leaves:
            return True

    def append(self, leaf):
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
