"""This intent classifier takes a string as an input and predicts an intent based
on it."""

# The two lines below are only here to turn off Tensorflow's debugging output in the console.
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import logging
import pickle
import nltk
from nltk.stem import WordNetLemmatizer
import numpy as np
from keras.models import load_model

from interfaces import IIntent_classifier
from environment import Environment

class Intent_classifier(IIntent_classifier):

    def __init__(self):

        self._env = Environment.get_instance()
        self.language = self._env.language

        # words and classes contain the vocabulary and the different possible
        # intents the deep-learning model is using
        # The pre-trained deep-learning model itself
        self._classes = pickle.load(open('models/intent_classifier/classifier_intents.pkl','rb'))

        if self.language == "en":
            self._lemmatizer = WordNetLemmatizer()

            self._words = pickle.load(open('models/intent_classifier/words_en.pkl','rb'))
            self._model = load_model('models/intent_classifier/classifier_model_en.h5')

        elif self.language == "fr":

            self._nlp = self._env.language_model

            self._words = pickle.load(open('models/intent_classifier/words_fr.pkl','rb'))
            self._model = load_model('models/intent_classifier/classifier_model_fr.h5')

        else: raise ValueError("Language code not recognized")


    def give_prediction(self, message):

        # handling bad input type
        if type(message) != str: raise TypeError("Classifier input must be a string")
        if message == "": return "MESSAGE_NOT_VALID"

        logging.debug("The classifier is processing user message: '" + message + "'")


        intent = self._detect_intent(message)
        return intent

    def _detect_intent(self, message):

        """The lines below feed user input into the deep learning model previously
        loaded. This model outputs an intent.
        For more information about how the model is trained, see the training script
        train_classifier.py"""

        # The line belows turns the sentence into a "vag of words" vector so that
        # we can feed it into the model
        p = self._make_bow(message)

        # predicting the intent using the neural network
        res = self._model.predict(np.array([p]), verbose=0)[0]

        # if the model outputs an intent below that value, it will be ignored as
        # it is not deemed accurate enough. The output of this model can be interpreted
        # as a PROBABILITY: hence if we get the intent "no" with a probability of
        # 0.8, it means that there is a 80% probability what the user said means 'no'
        ERROR_THRESHOLD = 0.5
        results = [[i,r] for i,r in enumerate(res) if r>ERROR_THRESHOLD]
        logging.debug("Prediction results: ")
        logging.debug(results)

        if results == []:
            logging.info("No intent could be found with enough certainty")
            return "UNSURE"

        final_result = results[0]
        if final_result[1] >= 0.55:

            logging.info("Intent: " + self._classes[final_result[0]])
            logging.debug("Certainty: " + str(final_result[1]))
            return self._classes[final_result[0]]

        else:

            # intents with a probability above the error threshold but below 0.8
            # need to be confirmed
            logging.info("No intent could be found with enough certainty")
            logging.debug("Best candidate: " + self._classes[final_result[0]])
            logging.debug("Certainty: " + str(final_result[1]))
            return "UNSURE"

    def _preprocess_sentence(self, sentence):

        """The sentence needs to be turned split into tokens and its words must
        be reduced to their base form before we can use them."""
        if self.language == "en":
            sentence_words = nltk.word_tokenize(sentence)
            sentence_words = [self._lemmatizer.lemmatize(word.lower()) for word in sentence_words]
        elif self.language == "fr":
            doc = self._nlp(sentence)
            sentence_words = [token.lemma_ for token in doc]
        else: raise ValueError("Language code not recognized")
        return sentence_words

    def _make_bow(self, sentence):

        """The sentence is turned into a vector of numbers,
        since the model only accepts numbers as input. This function returns
        a table as big as the vocabulary table used to train the model. Each index
        takes the value 1 if its associated word is found in the input sentence,
        and 0 otherwise. Thus this kind of vectors is empty for the most part."""

        sentence_words = self._preprocess_sentence(sentence)

        bag = [0]*len(self._words)
        for s in sentence_words:
            for i,w in enumerate(self._words):
                if w == s:
                    bag[i] = 1

        return(np.array(bag))
