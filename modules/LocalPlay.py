import os
import re
import random

def register(bot):
    register.localplayer = LocalPlayer()
    print('Current local root: ' + register.localplayer.root[0])

register.commands = ['cd', 'ls', 'play', 'pwd', 'rplay']
register.enabled = True

def call(bot, command, arguments):
    if command == 'pwd' and arguments == '':
        bot.send_msg_current_channel(register.localplayer.root[1] + register.localplayer.working_dir)

    if command == 'cd':
        working_path = register.localplayer.working_path()
        if not arguments.endswith('/'): 
            arguments += '/'

        if arguments == '/../':
            bot.send_msg_current_channel('Directory change is not allowed.')

        elif arguments.startswith('/'):
            root = register.localplayer.root
            if os.path.exists(root[0] + arguments[1:]):
                if root[0] + arguments[1:] in register.localplayer.allowed_tree:
                    register.localplayer.working_dir = arguments[1:]
                    new_working_path = register.localplayer.working_path()
                    bot.send_msg_current_channel(new_working_path[1])
                else:
                    bot.send_msg_current_channel('Directory change is not allowed.')
            else:
                bot.send_msg_current_channel('Directory does not exist.')

        else:
            working_path = register.localplayer.working_path()
            if os.path.exists(working_path[0] + arguments):
                if working_path[0] + arguments in register.localplayer.allowed_tree:
                    register.localplayer.working_dir += arguments
                    new_working_path = register.localplayer.working_path()
                    bot.send_msg_current_channel(new_working_path[1])
                else:
                    bot.send_msg_current_channel('Directory change is not allowed.')
            else:
                bot.send_msg_current_channel('Directory does not exist.')


    if command == 'ls':
        l = register.localplayer.ls()
        for string in l:
            bot.send_msg_current_channel(string)

    if command == 'play':
        play_music(bot, arguments)


    if command == 'rplay':
        register.localplayer.ls()
        arguments = random.randint(1, len(register.localplayer.file_l)) 
        play_music(bot, arguments)






def play_music(bot, arguments):
        try:
            select = int(arguments)
            pattern = '<br />{0}. '.format(select)
        except ValueError:
            pattern = arguments.lower()
        try:
            l = register.localplayer.ls()
            whole_l = ''
            for string in l:
                whole_l += string
                
            start_indexes = [m.start() for m in re.finditer(pattern, whole_l.lower())]

            if len(start_indexes) == 0:
                bot.send_msg_current_channel("No audio files containing '{0}'".format(pattern.replace('<br />', '')))
                raise Exception
            elif len(start_indexes) > 1:
                bot.send_msg_current_channel("Multiple audio files containing '{0}'".format(pattern.replace('<br />', '')))
                raise Exception

            start = start_indexes[0]

            if '<br />' in pattern:
                start += 6
            else:
                start = whole_l.rfind('<br />', 0, start) + 6
            end = whole_l.find('<br />', start)
            if whole_l[end] == whole_l[-1]:
                audio_file = whole_l[start:].split(' ', 1)[1]
            else:
                audio_file = whole_l[start:end].split(' ', 1)[1]
            bot.send_msg_current_channel('Adding <b>{0}</b> to the queue'.format(audio_file))
            bot.append_audio(register.localplayer.root[0] + register.localplayer.working_dir + audio_file, 'complete', audio_file)
        except:
            pass


class LocalPlayer:
    def __init__(self):
        self.root = ('/home/olivier/Projects/MumbleJumble/.song_library/', '/')
        self.working_dir = ''
        #self.allowed_elsewhere = False

        self.allowed_tree = [self.root[0]]
        for root, dirs, files in os.walk(self.root[0] + self.working_dir):
            self.allowed_tree.append(root + '/')


    def working_path(self):
        return (self.root[0] + self.working_dir, self.root[1] + self.working_dir)


    def ls(self):
        l = os.listdir(self.root[0] + self.working_dir)
        self.dir_l = []
        self.file_l = []
        for element in l:
            if os.path.isdir(self.root[0] + self.working_dir + element):
                self.dir_l.append(element)
            else:
                self.file_l.append(element)
        dir_l_sorted = sorted(self.dir_l, key=str.lower)
        file_l_sorted = sorted(self.file_l, key=str.lower)
        l = dir_l_sorted + file_l_sorted
        
        clean_l = []
        for x in range(len(l) / 20):
            clean_l.append('')
        if len(l) % 20 != 0:
            clean_l.append('')
        counter = 1
        for i in range(len(l)):
            j = i / 20
            if os.path.isdir(self.root[0] + self.working_dir + l[i]):
                clean_l[j] += '<br /><b>{0}</b>'.format(l[i])
            else:
                clean_l[j] += '<br />{0}. {1}'.format(counter, l[i])
                counter += 1
        return clean_l
