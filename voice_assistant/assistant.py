"""The voice assistant's central module. It contains the main execution loop."""

import logging
import random

from interfaces import IAssistant
from environment import Environment

def pick_random_sentence(options):
    """Randomly picks and returns a sentence among the options list. Enables to
    randomize a bit what the AI says"""
    return random.choice(options)


class Assistant(IAssistant):

    """Check the info string for each method"""

    def __init__(self, classifier, speech_recognizer, text_to_speech):

        """Instantiates the intent classifier and the different intent_slots,
        as well as the speech recognizer and the speech synthesis.
        Check interfaces.py to see a blueprint of the different components"""

        self._env = Environment.get_instance()

        # If an intent is currently performing a task that requires more than one
        # input/output pair (e.g. if the intent slot is asking the user for more
        # information or a confirmation), then all new inputs from the user are
        # going directly to that intent, bypassing the classifier. This lasts
        # until the intent slot is done with its task or the task is cancelled.
        # The string below stores the intent id of the slot currently performing
        # a task, if any.
        self._current_intent = None
        self.classifier = classifier
        self.speech_rec = speech_recognizer
        self.tts = text_to_speech

        # keys for the intent_slots dictionary are the intents id. Values are the
        # intent slots objects they're associated with.
        self.intent_slots = {}


    def run(self):

        """The method that contains the main execution loop."""

        logging.info("Entering main loop")
        logging.info("The following intents are recognized: " + str(list(self.intent_slots.keys())))

        if self._env.config['DEFAULT']['speech_recognition'].lower() == "true": text_input_only = False
        else: text_input_only = True

        if self._env.config['DEFAULT']['text_to_speech'].lower() == "true": text_output_only = False
        else: text_output_only = True

        if text_input_only:
            print("Speech recognition is off")
            logging.info("Speech recognition is off")

        if text_output_only:
            print("Speech synthesis is off")
            logging.info("Speech synthesis is off")

        if self._env.language == "en": potential_lines = ["Hello!", "Hi!", "How are you doing?"]
        elif self._env.language == "fr": potential_lines = ["Bonjour !", "Salut !", "Salut, comment allez-vous ?"]

        if text_output_only: print(pick_random_sentence(potential_lines))
        else: self.tts.say(pick_random_sentence(potential_lines))


        keep_running = True
        standby_mode = False


        while keep_running:

            try:

                if text_input_only:
                    sentence = input(self._env.working_dir + " > ")
                    logging.info("User said: '" + sentence + "'")

                else:
                    print(self._env.working_dir + " > ")
                    sentence = self.speech_rec.wait_input()
                    logging.info("User said: '" + sentence + "'")

                if standby_mode:
                    if self._env.language == "en" and sentence.lower() == "wake up":
                        standby_mode = False
                        potential_lines = ["I'm back!", "Hello again!", "Do you need something?"]
                        if text_output_only: print(pick_random_sentence(potential_lines))
                        else: self.tts.say(pick_random_sentence(potential_lines))

                    if self._env.language == "fr" and sentence.lower() == "réveille-toi":
                        standby_mode = False
                        potential_lines = ["Me revoilà !", "Oui ?", "De quoi avez-vous besoin ?"]
                        if text_output_only: print(pick_random_sentence(potential_lines))
                        else: self.tts.say(pick_random_sentence(potential_lines))

                    continue


                # First we check self._current_intent to see if an intent is
                # currently performing a task. If so, the classifier is not called,
                # and the input is sent directly to the corresponding intent slot
                # instead
                if not self._current_intent: intent = self.classifier.give_prediction(sentence.lower())
                else:
                    # The stop intent has two consequences. First it cancels the
                    # ongoing action, if any. Then it also interrupts anything
                    # the AI is currently saying (if text_output_only is set to False)
                    if self.classifier.give_prediction(sentence.lower()) == "stop":
                        logging.debug("Intent '" + self._current_intent + "' was cancelled")
                        self.intent_slots[self._current_intent].cancel_action()
                        self.tts.stop()
                        if self._env.language == "en" :
                            potential_lines = ["Okay!", "Gotcha!", "Understood!"]
                        elif self._env.language == "fr" :
                            potential_lines = ["OK !", "Compris !", "D'accord !"]
                        selected_sentence = pick_random_sentence(potential_lines)
                        if text_output_only : print(selected_sentence)
                        else: self.tts.say(selected_sentence)
                        logging.info("AI said: '" + selected_sentence + "'")
                        self._current_intent = None
                        continue
                    response = self.intent_slots[self._current_intent].run(sentence)
                    if (not (type(response[0]) is str)) or (not (type(response[1]) is bool)) :
                        raise TypeError("Wrong response format. The expected format is tuple(str, bool)")
                    if text_output_only:
                        if response[0] != "":
                            print(response[0])
                            logging.info("AI said: '" + response[0] + "'")
                    else:
                        if response[0] != "":
                            self.tts.say(response[0])
                            logging.info("AI said: '" + response[0] + "'")

                    # If the boolean value response[1] is False, it means that
                    # this intent slot is not done with its task and further
                    # input will be redirected directly to it.
                    if response[1]: self._current_intent = None
                    else: self._current_intent = slot
                    continue

                logging.debug("Classifier predicted the intent '" + intent + "'")

                if intent == "MESSAGE_NOT_VALID":
                    logging.info("MESSAGE_NOT_VALID")
                    if text_output_only:
                        if self._env.language == "en":
                            print("Please input a valid message")
                            logging.info("AI said: 'Please input a valid message'")
                        elif self._env.language == "fr":
                            print("Ce message n'est pas valide")
                            logging.info("AI said: 'Ce message n'est pas valide'")
                        else: raise ValueError("Wrong language code used")
                    else:
                        if self._env.language == "en":
                            self.tts.say("This message is not valid")
                            logging.info("AI said: 'This message is not valid'")
                        elif self._env.language == "fr":
                            self.tts.say("Ce message n'est pas valide")
                            logging.info("AI said: 'Ce message n'est pas valide'")
                        else: raise ValueError("Wrong language code used")
                    continue

                elif intent == "UNSURE":
                    logging.info("INTENT UNSURE")
                    if self._env.language == "en":
                        potential_lines = ["Sorry, I don't understand what you want",
                                        "Sorry, I don't get it",
                                        "I don't understand what you need"]
                    elif self._env.language == "fr":
                        potential_lines = ["Désolé, je ne comprends pas ce que vous voulez",
                                        "Je n'ai pas compris",
                                        "Je ne comprends pas ce qu'il vous faut"]
                    else: raise ValueError("Wrong language code used")

                    selected_sentence = pick_random_sentence(potential_lines)

                    if text_output_only: print(selected_sentence)
                    else: self.tts.say(selected_sentence)
                    logging.info("AI said: '" + selected_sentence + "'" )

                    continue

                elif intent == "standby":
                    if self._current_intent:
                        self.intent_slots[self._current_intent].cancel_action()
                        logging.debug("Intent '" + self._current_intent + "' was cancelled")
                    self.tts.stop()
                    self._current_intent = None
                    standby_mode = True

                    if self._env.language == "en":
                        potential_lines = ["Bye!",
                                        "See you later!",
                                        "I will see you later!"]
                    elif self._env.language == "fr":
                        potential_lines = ["À plus tard !",
                                        "Au revoir !",
                                        "On se voit plus tard !"]
                    else: raise ValueError("Wrong language code used")

                    selected_sentence = pick_random_sentence(potential_lines)

                    if text_output_only: print(selected_sentence)
                    else: self.tts.say(selected_sentence)
                    logging.info("AI said: '" + selected_sentence + "'" )



                elif intent == "stop": self.tts.stop()

                for slot in self.intent_slots:
                    if slot == intent:
                        response = self.intent_slots[slot].run(sentence)

                        if (not (type(response[0]) is str)) or (not (type(response[1]) is bool)) :
                            raise TypeError("Wrong response format. The expected format is tuple(str, bool)")
                        if text_output_only:
                            if response[0] != "":
                                print(response[0])
                                logging.info("AI said: '" + response[0] +"'")
                        else:
                            if response[0] != "":
                                self.tts.say(response[0])
                                logging.info("AI said: '" + response[0] +"'")

                        # If the boolean value response[1] is False, it means that
                        # this intent slot is not done with its task and further
                        # input will be redirected directly to it.
                        if response[1]: self._current_intent = None
                        else: self._current_intent = slot
                        break

            except KeyboardInterrupt:

                self.tts.stop()
                if self._env.language == "en":
                    potential_lines = ["Bye!",
                                    "See you later!",
                                    "I will see you later!"]
                elif self._env.language == "fr":
                    potential_lines = ["À plus tard !",
                                    "Au revoir !",
                                    "On se voit plus tard !"]
                else: raise ValueError("Wrong language code used")
                selected_sentence = pick_random_sentence(potential_lines)

                if text_output_only: print(selected_sentence)
                else: self.tts.say(selected_sentence)
                logging.info("AI said: '" + selected_sentence + "'" )

                keep_running = False
                for slot in self.intent_slots:
                    # Calling the exit method of each intent slot right before exiting.
                    # It enables them to quit cleanly by joining threads, freeing up
                    # resources, etc
                    self.intent_slots[slot].exit()

        for slot in self.intent_slots:
            # Calling the exit method of each intent slot right before exiting.
            # It enables them to quit cleanly by joining threads, freeing up
            # resources, etc
            self.intent_slots[slot].exit()

    def add_intent(self, intent):

        """Each intent slot needs to be registered so that we know what object
        to call to handle each intent."""

        intent_id = intent.intent_id
        self.intent_slots[intent_id] = intent
        logging.debug(f"Adding intent slot '{intent_id}' to the voice assistant")

    def add_intents(self, intents):

        """A convenience funtion that adds all the intent slots in the iterable intents."""

        for i in intents:
            intent_id = i.intent_id
            self.intent_slots[intent_id] = i
            logging.debug(f"Adding intent slot '{intent_id}' to the voice assistant")
