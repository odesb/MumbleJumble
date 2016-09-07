import os
import re
import random

def register(bot):
    register.localplayer = LocalPlayer(bot)
    print('Current local root: ' + register.localplayer.root[0])

register.commands = ['cd', 'ls', 'play', 'pwd', 'rplay']
register.enabled = True

def call(bot, command, arguments):
    if command == 'pwd' and arguments == '':
        register.localplayer.pwd()
        
    if command == 'cd':
        register.localplayer.cd(arguments)
        
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
            bot.append_audio(os.path.join(register.localplayer.root[0], register.localplayer.working_dir, audio_file), 'complete', audio_file)
        except:
            pass


class LocalPlayer:
    def __init__(self, parent):
        self.parent = parent
        self.root = (os.path.abspath(self.parent.config['localplay']['local_folder']), '/')
        self.working_dir = '.'


    def working_path(self):
        return os.path.join(self.root[0], self.working_dir)

    def list_dir(self, path):
        l = os.listdir(os.path.abspath(path))
        dir_l = []
        for element in l:
            if os.path.isdir(os.path.join(os.path.abspath(path), element)):
                dir_l.append(element.encode('ascii', 'ignore'))
        return dir_l


    def ls(self):
        l = os.listdir(self.working_path())
        self.dir_l = []
        self.file_l = []
        for element in l:
            if os.path.isdir(os.path.join(self.working_path(), element)):
                self.dir_l.append(element.encode('ascii', 'ignore'))
            else:
                self.file_l.append(element.encode('ascii', 'ignore'))
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
            if os.path.islink(os.path.join(self.working_path(), l[i].decode('ascii'))):
                clean_l[j] += '<br /><b><font color=#5fa5e0>{0}</font></b>'.format(l[i].decode('ascii'))
            elif os.path.isdir(os.path.join(self.working_path(), l[i].decode('ascii'))):
                clean_l[j] += '<br /><b>{0}</b>'.format(l[i].decode('ascii'))
            else:
                clean_l[j] += '<br />{0}. {1}'.format(counter, l[i].decode('ascii'))
                counter += 1
        return clean_l


    def cd(self, arguments):
        if arguments == '':
            self.working_dir = '.'
            self.parent.send_msg_current_channel(os.path.join(self.root[1], self.working_dir))

        elif arguments.startswith('/'):
            if os.path.exists(os.path.join(self.root[0], arguments[1:])):
                self.working_dir = arguments[1:]
                self.parent.send_msg_current_channel(os.path.join(self.root[1], self.working_dir))
            else:
                try:
                    directory = self.find_dir(arguments)
                    self.cd('/' + directory)
                except:
                    self.parent.send_msg_current_channel('Directory does not exist')

        else:
            future_path = os.path.abspath(os.path.join(self.working_path(), arguments))
            if os.path.exists(future_path):
                if os.path.commonprefix([future_path, self.root[0]]) == self.root[0]:
                    self.working_dir = os.path.relpath(future_path, self.root[0])
                    self.parent.send_msg_current_channel(os.path.join(self.root[1], self.working_dir))
                else:

                    self.parent.send_msg_current_channel('Directory change is not allowed')
            else:
                try:
                    directory = self.find_dir(arguments)
                    self.cd(directory)
                except: 
                    pass


    def find_dir(self, arguments):
        l = self.list_dir(os.path.join(self.working_path(), os.path.split(arguments)[0]))
        keyword = os.path.split(arguments)[1]
        found_list = []
        for directory in l:
            if keyword in directory.lower():
                found_list.append(directory)
        if len(found_list) == 0:
            self.parent.send_msg_current_channel("No directory containing '{0}'".format(keyword))
            raise Exception
        
        elif len(found_list) == 1:
            return found_list[0]
        else:
            self.parent.send_msg_current_channel("Multiple directories containing '{0}'".format(keyword))
            raise Exception


    def pwd(self):
        self.parent.send_msg_current_channel(os.path.join(self.root[1], self.working_dir))
