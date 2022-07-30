"""The input class for our project. Please note that the assistant can also run in
terminal mode, where speech recognition is disabled and the user must type
the input. See assistant.py for more info about that"""

import speech_recognition as sr

from interfaces import ISpeech_recognizer
from environment import Environment

class Speech_recognizer(ISpeech_recognizer):

    def __init__(self):

        self._env = Environment.get_instance()
        self._recognizer = sr.Recognizer()
        self._mic = sr.Microphone()
        self._recognizer.pause_threshold = 0.5
        self._recognizer.energy_threshold = 4000

        self.lang = self._env.language

    def wait_input(self):

        while True:

            with self._mic as source:
                self._recognizer.adjust_for_ambient_noise(self._mic)
                audio = self._recognizer.listen(source)

                try:
                    if self.lang == "en": return self._recognizer.recognize_google(audio, language="en-US")
                    elif self.lang == "fr": return self._recognizer.recognize_google(audio, language="fr-FR")
                    else: raise ValueError("Wrong language code")
                except sr.UnknownValueError: # Raised when sr can't identify a sentence from the recorded data
                    pass
