"""The class responsible for converting text to synthetic speech."""

from gtts import gTTS
from io import BytesIO
import pygame

from interfaces import IText_to_speech
from environment import Environment

class Text_to_speech(IText_to_speech):

    def __init__(self):

        self._env = Environment.get_instance()
        self.lang = self._env.language
        pygame.mixer.init()

    def say(self, sentence):

        audio = BytesIO()
        speech = gTTS(text=sentence, lang=self.lang, slow=False)
        speech.write_to_fp(audio)
        pygame.mixer.music.stop()
        pygame.mixer.music.load(audio, "mp3")
        pygame.mixer.music.play()

    def stop(self):

        pygame.mixer.music.stop()
