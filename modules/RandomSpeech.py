import random 
# Since sleep is 0.5, this 2 interval = 1s
RANDOM_SPEECH_INTERVAL_MIN = 500
RANDOM_SPEECH_INTERVAL_MAX = 2000
SPEECH = ["I hate everyone", \
"Stop living", \
"Can we be friends", \
"How can mirrors be real", \
"Why are you listening to a bot", \
]

def call(bot, command_used, arguments):
    pass

def register(bot):
    print("Setting up spambot - loaded {0} speeches".format(len(SPEECH)))

def loop(bot):
    register.TOTAL_LOOPS += 1
    if register.TOTAL_LOOPS % register.NEXT_SPEECH == 0:
        bot.send_msg_current_channel(random.choice(SPEECH))
        register.TOTAL_LOOPS = 0
        register.NEXT_SPEECH = random.randrange(RANDOM_SPEECH_INTERVAL_MIN, RANDOM_SPEECH_INTERVAL_MAX)
        print("Next speech is in: {0}".format(register.NEXT_SPEECH))


register.TOTAL_LOOPS = 0
register.NEXT_SPEECH = random.randrange(RANDOM_SPEECH_INTERVAL_MIN, RANDOM_SPEECH_INTERVAL_MAX)
register.commands = [""]
register.call_in_loop = True
register.enabled = True
