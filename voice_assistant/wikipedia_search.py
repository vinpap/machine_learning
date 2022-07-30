"""This intent slot looks for the topic requested by the user in the sentence,
look it up on Wikipedia and displays the first line of the Wikipedia page's
summary if it founds something.
NOTE: despite the fact that this file is named wikipedia_search.py, the intent
id is still 'wikipedia'. The filename had to be changed due to naming conflicts
with the module 'wikipedia'"""


import logging
import random

from spacy.symbols import dobj, pobj, nsubj
import wikipedia

from interfaces import IIntent_slot
from environment import Environment


def pick_random_sentence(options):
    """Randomly picks and returns a sentence among the options list. Enables to
    randomize a bit what the AI says"""
    return random.choice(options)

class Wikipedia(IIntent_slot):

    def __init__(self):

        self._env = Environment.get_instance()

        self.intent_id = "wikipedia"
        logging.debug("Creating intent slot '" + self.intent_id + "'")
        self.lang = self._env.language

        self._nlp = self._env.language_model
        if self.lang == "en": wikipedia.set_lang("en")
        elif self.lang == "fr" : wikipedia.set_lang("fr")
        else: raise ValueError("Unvalid language code")



    def run(self, input):

        logging.debug("Running intent slot '" + self.intent_id + "' with input '" + input + "'")

        target = self._find_target(input)

        if not target:
            if self._env.language == "en":
                potential_lines = ["Sorry, I don't understand what you want to look up on Wikipedia",
                                "I don't get it, what are you looking for exactly?"]

            elif self._env.language == "fr":
                potential_lines = ["Désolé, je ne comprends pas ce que vous voulez chercher sur Wikipédia",
                                "Je ne comprends pas bien, que cherchez-vous exactement ?"]

            else: raise ValueError("Wrong language code")
            msg = pick_random_sentence(potential_lines)
            return (msg, True)
        else:
            logging.debug("Target for wikipedia search: " + target)
            info = self._search_on_wiki(target)
            if not info:
                if self._env.language == "en":
                    potential_lines = ["Sorry, I couldn't find a matching article on Wikipédia",
                                    "I wasn't able to find something about that on Wikipédia"]

                elif self._env.language == "fr":
                    potential_lines = ["Désolé, je n'ai pas trouvé d'article correspondant sur Wikipédia",
                                    "Je n'ai rien trouvé là-dessus sur Wikipédia"]

                else: raise ValueError("Wrong language code")
                msg = pick_random_sentence(potential_lines)
                return (msg, True)
            else: return (info, True)



    def _find_target(self, sentence):

        if self.lang == "en": return self._find_target_en(sentence)
        elif self.lang == "fr": return self._find_target_fr(sentence)
        else: raise ValueError("Unvalid language code")

    def _find_target_en(self, sentence):

        """Attempts to find the topic requested by the user in a sentence in
        English.
        NOTE: As of now, there is no foolproof method to find the topic requested
        by the user in the sentence. This method performs grammatical analysis on
        the sentence to find the topic, but keep in mind that the topic might
        not always be found, especially if the sentence is very long or has an
        unusual structure."""

        target = ""

        doc = self._nlp(sentence)

        # Plan A: ff the sentence contains a name of person, place, organisation...
        # then we assume it is the topic
        if doc.ents:
            for ent in doc.ents:
                if ent.text != "wikipedia" and ent.label_ not in ("CARDINAL", "MONEY", "TIME", "PERCENT", "QUANTITY", "ORDINAL", "NORP"):
                    target = ent.text
                    return target

        # Plan B: we look for a group of words right after 'on', 'about', or 'regarding'
        if not target:
            for t in doc:
                if t.text.lower() in ["on", "about", "regarding"]:
                    for child in t.children:
                        if child.dep_ == "pobj":
                            for subc in child.subtree:
                                target = target + subc.text + " "
                            target = target.rstrip()
                            return target

        # Plan C: we take the subject of the sentence
        if not target:
            for t in doc:
                if t.dep_ == "ROOT":
                    for c in t.children:
                        if c.dep_ == "nsubj":
                            for subc in c.subtree:
                                target = target + subc.text + " "
                            target = target.rstrip()
                            return target

        # Plan D: we take what is written right after 'check' or 'find'
        if not target:
            for t in doc:
                if t.text.lower() in ["find", "check"]:
                    for child in t.children:
                        if child.dep_ == "dobj":
                            for subc in child.subtree:
                                target = target + subc.text + " "
                            target = target.rstrip()
                            return target

        # Plan E: we look for the subject associated with an interrogative such
        # as 'who', 'when', etc...
        if not target:
            for t in doc:
                if t.text.lower() in ["who", "what", "where", "when"]:
                    for child in t.children:
                        if child.dep_ == "nsubj":
                            for subc in child.subtree:
                                target = target + subc.text + " "
                            target = target.rstrip()
                            return target

        if target == "" : return False

    def _find_target_fr(self, sentence):

        """Attempts to find the topic requested by the user in a sentence in
        French.
        NOTE: As of now, there is no foolproof method to find the topic requested
        by the user in the sentence. This method performs grammatical analysis on
        the sentence to find the topic, but keep in mind that the topic might
        not always be found, especially if the sentence is very long or has an
        unusual structure."""

        target = ""
        doc = self._nlp(sentence)

        # Plan 1: we look for a group of words right after 'sur' or 'concernant'
        if not target:
            for t in doc:
                if t.text.lower() in ["sur", "de", "d'", "du", "concernant"] and t.dep_ == "case":
                    for subc in t.head.subtree:
                        if subc != t: target = target + subc.text + " "
                    target = target.rstrip()
                    return target

        # Plan B: ff the sentence contains a name of person, place, organisation...
        # then we assume it is the topic

        if (not target) and doc.ents:
            for ent in doc.ents:
                if ent.text not in ("wikipedia", "wikipédia") and ent.label_ not in ("CARDINAL", "MONEY", "TIME", "PERCENT", "QUANTITY", "ORDINAL", "NORP"):
                    target = ent.text
                    return target


        # Plan C: we take the words following où, quand, quoi, qui
        if not target:
            for t in doc:
                if t.text in ["où", "quoi", "quand", "qui"]:
                    target = ""
                    for i in range(1, 20):
                        try:
                            target = target + t.nbor(i).text
                            target = target + " "
                        except:
                            if target != "":
                                target = target.rstrip()
                                return target
                    target = target.rstrip()
                    return target


        if target == "": return False

    def _search_on_wiki(self, sentence):

        """Since wikipedia's API autosuggest feature behaves somewhat oddly,
        we try not using it in the first place.
        If that seach doesn't yield any result then we turn it on, hence the many
        try/except blocks here"""

        info = False

        try:
            info = wikipedia.summary(sentence, sentences=5, auto_suggest=False)

        except wikipedia.exceptions.DisambiguationError as potential_pages:
            try:
                if wikipedia.search(sentence):
                    info = wikipedia.summary(wikipedia.search(sentence)[0], sentences=5, auto_suggest=False)
            except wikipedia.exceptions.DisambiguationError:
                return False


        except wikipedia.exceptions.PageError:
            try:
                if wikipedia.search(sentence):
                    info = wikipedia.summary(wikipedia.search(sentence)[0], sentences=5, auto_suggest=False)
            except wikipedia.exceptions.DisambiguationError as potential_pages:
                if potential_pages.options:
                    try:
                        if wikipedia.search(sentence):
                            info = wikipedia.summary(wikipedia.search(sentence)[0], sentences=5, auto_suggest=False)
                    except wikipedia.exceptions.DisambiguationError:
                        return False
                else: False

            except wikipedia.exceptions.PageError:
                return False

        return info
