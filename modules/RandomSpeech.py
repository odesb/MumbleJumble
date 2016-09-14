import random 
SPEECH = ["I hate everyone",
"Stop living",
"Can we be friends",
"How can mirrors be real",
"Why are you listening to a bot",
"That was really disgusting of you",
"What about.......",
"Sir",
"Esir", 
"Wow.......", 
"Sir what about", 
"Les CORRUPTOR",  
"Be happy!", 
"Smoke Weed Everyday", 
"BEC", 
"You have to spend money to make money!", 
"Half Life 3 soon"]


def register(bot):
    print("Setting up spambot - loaded {0} speeches".format(len(SPEECH)))

register.commands = None
register.enabled = True


def call(bot, command, arguments):
    pass


def loop(bot):
    trigger = random.random() * 100
    if 0 <= trigger <= loop.chance:
        bot.send_msg_current_channel(random.choice(SPEECH))

loop.time = 60
loop.chance = 3  #3% chance to trigger the speech
