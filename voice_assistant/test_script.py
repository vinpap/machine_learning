import logging

from assistant import Assistant
from intent_classifier import Intent_classifier
from speech_recognizer import Speech_recognizer
from text_to_speech import Text_to_speech

import desktop
from wikipedia_search import Wikipedia
from news import News

logging.basicConfig(filename='voice_assistant.log',
level=logging.INFO,
format='%(asctime)s | %(message)s')

classifier = Intent_classifier()
speech_rec = Speech_recognizer()
tts = Text_to_speech()
voice_assistant = Assistant(classifier, speech_rec, tts)

"""Now loading all the intent slots objects"""

s_open_program = desktop.Open_program()
s_close_program = desktop.Close_program()
s_new_working_dir = desktop.New_working_dir()
s_copy = desktop.Copy()
s_paste = desktop.Paste()
s_copy_all = desktop.Copy_all()
s_cut = desktop.Cut()
s_cut_all = desktop.Cut_all()
s_trash = desktop.Trash()
s_trash_all = desktop.Trash_all()
s_previous = desktop.Previous()
s_open_file = desktop.Open_file()
s_rename = desktop.Rename()
s_go_to_parent_dir = desktop.Go_to_parent_dir()

s_wikipedia = Wikipedia()
s_news = News()

voice_assistant.add_intents([s_open_program,
                            s_close_program,
                            s_new_working_dir,
                            s_copy,
                            s_paste,
                            s_copy_all,
                            s_cut,
                            s_cut_all,
                            s_trash,
                            s_trash_all,
                            s_previous,
                            s_open_file,
                            s_rename,
                            s_go_to_parent_dir,
                            s_wikipedia,
                            s_news])

voice_assistant.run()
