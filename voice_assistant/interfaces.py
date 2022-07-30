"""Contains the interfaces for the different components used by the assistant. These
are meant to give blueprints of each class, as well as showing how it should
be used. As a general rule, it is better to avoid calling from outside these
classes methods that are not referenced here"""

from abc import ABC, abstractmethod

class IAssistant(ABC):


    """The central module that contains the execution loop. it receives input,
    calls an intent classifier to predict an intent based on this input, and call
    the intent slot matching the predicted intent."""

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def add_intent(self, intent):
        """Takes a single intent slot as parameter"""
        pass

    @abstractmethod
    def add_intents(self, intents):
        """A simple conveniency function.
        Takes a list of slots as parameter"""
        pass

class IIntent_classifier(ABC):

    """The classifier responsible for converting user sentences into
    intents.
    Example: input: "please open the text editor"
    intent: open_program"""

    @abstractmethod
    def give_prediction(self, input):
        """input is the string containing the user input
        The return value is the intent recognized by the classifier"""
        pass


class IIntent_slot(ABC):

    """An intent slot represents a possible intent, and defines what actions should
    be taken when the intent is detected.
    Every intent slot is identified with a unique attribute named intent_id"""

    @property
    def task_is_ongoing(self):

        if hasattr(self, "_task_is_ongoing"): return self._task_is_ongoing
        else:
            self._task_is_ongoing = False
            return self._task_is_ongoing

    @task_is_ongoing.setter
    def task_is_ongoing(self, new_value):
        self._task_is_ongoing = new_value


    def cancel_action(self):
        self._task_is_ongoing = False


    @abstractmethod
    def run(self, input):
        """Call this when the intent associated with the slot has been
        recognized by the classifier. input is a string containing the original
        sentence.
        The return value must be a tuple(str, bool), where the string is a message
        to give to the user(return a blank string if there is nothing to say). If
        the boolean is True, it means that the task is done and the program can
        resume normally. If it is False, it means that the intent's task is not
        done yet. In that case, subsequent inputs from the user will be transmitted
        directly to this intent slot instead of going through the classifier."""
        pass

class ISpeech_recognizer(ABC):

    """The component that takes inputs from the microphone and perform speech
    recognition on it"""

    @abstractmethod
    def wait_input(self):
        """To be called in the main execution loop. The function waits until the
        microphone picks up a voice input, then converts it to text and returns it"""
        pass

class IText_to_speech(ABC):

    """Says the sentences it is given using a text-to-speech API"""

    @abstractmethod
    def say(self, sentence):
        """Pretty self-explanatory"""
        pass

    @abstractmethod
    def stop(self):
        """Interrupts what the TTS API is currently saying"""
        pass
