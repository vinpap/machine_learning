"""Launcher script to use Jerry quickly."""

from jerry import Jerry

bot = Jerry()
print(bot.call_jerry())

keep_running = True

while keep_running:

    sentence = input()

    if sentence == "EXIT":

        keep_running = False

    else:

        print(bot.tell_jerry(sentence))
