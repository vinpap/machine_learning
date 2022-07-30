"""Jerry's main module"""

# The two lines below are only here to turn off Tensorflow's debugging output in the console.
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


import random
from datetime import date
import time
import json
import requests
import pickle
import nltk
from nltk.stem import WordNetLemmatizer
import numpy as np
from keras.models import load_model

from conversational_memory import Conversational_Memory, Interaction


class Jerry:

    """The class where basically everthing happens. Check the info string for each method"""

    def __init__(self):

        # words and classes contain the vocabulary and the different possible
        # intents the deep-learning model is using
        self.words = pickle.load(open('model/words.pkl','rb'))
        self.classes = pickle.load(open('model/classes.pkl','rb'))

        # The pre-trained deep-learning model itself
        self.model = load_model('model/jerry_model.h5')

        # All words typed by the user are lemmatized (i.e. reduced to their
        # simplest form) before being fed into the deep learning model
        self.lemmatizer = WordNetLemmatizer()

        # memory handles a short-term conversational memory for the bot, i.e.
        # the last thing the user said, and such. See conversational_memory.py for
        # more information
        self.memory = Conversational_Memory(save_conversations=True)

    def call_jerry(self):

        """Only returns a random string intended to start a conversation (or not,
        'cause Jerry is very bad-temepered...)"""

        print("(type 'EXIT' to  leave Jerry)")

        selection = random.randint(0, 9)

        if selection == 0: first_message = "..Is anyone here?"
        elif selection == 1: first_message = "Hey, who's there?"
        elif selection == 2: first_message = "Nice, I was getting bored. How are you doing?"
        elif selection == 3: first_message = "Hey, what's up?"
        elif selection == 4: first_message = "Hi!\n Would you like to talk a bit?"
        else: first_message = ""


        return first_message

    def tell_jerry(self, message):

        """called whenever the user says something to Jerry"""

        return self.process_message(message)

    def process_message(self, message):

        # handling bad input type
        if type(message) != str or message == "":

            error_message = ""
            selection = random.randint(0, 2)

            if selection == 0:
                error_message = "Despite being a bot, I can't just understantd whatever you throw at me, you know..."

            elif selection == 1:
                error_message = "What does that even mean? Can't you talk using character strings, like everyone?"

            elif selection == 2:
                error_message =  "I don't know what you're trying to say, but I only understand character strings. Just saying."


            return error_message


        intent = self.detect_intent(message)

        # Pretty straightforward: depending on the intent detected from the user,
        # a specific function is called to reply
        if intent["intent"] == "dont_understand": response = self.dont_understand(message)
        elif intent["intent"] == "unsure_about_intent": response = self.unsure_about_intent(intent["supposed_intent"])
        elif intent["intent"] == "are_you_a_bot": response = self.are_you_a_bot()
        elif intent["intent"] == "change_ai_name": response = self.change_ai_name()
        elif intent["intent"] == "change_user_name": response = self.change_user_name()
        elif intent["intent"] == "date": response = self.date()
        elif intent["intent"] == "do_you_have_pets": response = self.do_you_have_pets()
        elif intent["intent"] == "fun_fact": response = self.fun_fact()
        elif intent["intent"] == "goodbye": response = self.goodbye()
        elif intent["intent"] == "greeting": response = self.greeting()
        elif intent["intent"] == "how_old_are_you": response = self.how_old_are_you()
        elif intent["intent"] == "maybe": response = self.maybe()
        elif intent["intent"] == "meaning_of_life": response = self.meaning_of_life()
        elif intent["intent"] == "no": response = self.no()
        elif intent["intent"] == "oos": response = self.oos()
        elif intent["intent"] == "repeat": response = self.repeat()
        elif intent["intent"] == "tell_joke": response = self.tell_joke()
        elif intent["intent"] == "thank_you": response = self. thank_you()
        elif intent["intent"] == "time": response = self.time()
        elif intent["intent"] == "user_name": response = self.user_name()
        elif intent["intent"] == "weather": response = self.weather()
        elif intent["intent"] == "what_are_your_hobbies": response = self.what_are_your_hobbies()
        elif intent["intent"] == "what_can_i_ask_you": response = self.what_can_i_ask_you()
        elif intent["intent"] == "what_is_your_name": response = self.what_is_your_name()
        elif intent["intent"] == "where_are_you_from": response = self.where_are_you_from()
        elif intent["intent"] == "who_do_you_work_for": response = self.who_do_you_work_for()
        elif intent["intent"] == "who_made_you": response = self.who_made_you()
        elif intent["intent"] == "yes": response = self.yes()
        else:
            return "ERROR: intent returned by method detect_intent is not part of the known intents"

        # Interaction data can be saved, both for statistical purpose and to
        # allow Jerry to answer some questions. See conversational_memory.py
        self.memory.save_interaction(Interaction(message, response, intent["intent"]))
        return response

    def detect_intent(self, message):

        """That's where the magic happens. The lines below feed user input into the
        deep learning model previously loaded. This model outputs an intent.
        For more information about how the model is trained, see the training script"""

        # The line belows turns the sentence into a "vag of words" vector so that
        # we can feed it into the model
        p = self.make_bow(message)

        # predicting the intent using the neural network
        res = self.model.predict(np.array([p]))[0]

        # if the model outputs an intent below that value, it will be ignored as
        # it is not deemed accurate enough. The output of this model can be interpreted
        # as a PROBABILITY: hence if we get the intent "no" with a probability of
        # 0.8, it means that there is a 80% probability what the user said means 'no'
        ERROR_THRESHOLD = 0.70
        results = [[i,r] for i,r in enumerate(res) if r>ERROR_THRESHOLD]

        if results == []: return {"intent": "dont_understand", "probability": "1"}

        final_result = results[0]
        if final_result[1] >= 0.80:

            return {"intent": self.classes[final_result[0]], "probability": final_result[1]}

        else:

            # intents with a probability above the error threshold but below 0.8
            # need to be confirmed: Jerry then asks a question to the user to do
            # that
            return {"intent": "unsure_about_intent", "supposed_intent": self.classes[final_result[0]]}


    def preprocess_sentence(self, sentence):

        """The sentence needs to be turned split into tokens and its words must
        be reduced to their base form before we can use them."""

        sentence_words = nltk.word_tokenize(sentence)
        sentence_words = [self.lemmatizer.lemmatize(word.lower()) for word in sentence_words]
        return sentence_words

    def make_bow(self, sentence):

        """The sentence is turned into a vector of numbers,
        since the model only accepts numbers as input. This function returns
        a table as big as the vocabulary table used to train the model. Each index
        takes the value 1 if its associated word is found in the input sentence,
        and 0 otherwise. Thus this kind of vectors is empty for the most part."""

        sentence_words = self.preprocess_sentence(sentence)

        bag = [0]*len(self.words)
        for s in sentence_words:
            for i,w in enumerate(self.words):
                if w == s:
                    bag[i] = 1

        return(np.array(bag))



    # Each of the functions below is associated with an intent

    def dont_understand(self, user_msg):

        """Because when you don't understand, you don't talk."""
        return ""


    def unsure_about_intent(self, supposed_intent):

        """Called when the probability isn't high enough for the intent generated
        by the model. See Jerry.detect_intent"""

        selection = random.randint(0, 1)

        if supposed_intent == "are_you_a_bot":
            if selection == 0: response = "I didn't really get it. Are you asking if I am a bot?"
            else: response = "I don't understand. Are you asking me what I am?"
            self.memory.question_asked_to_user = "unsure_about_intent_are_you_a_bot"
        elif supposed_intent == "change_ai_name":
            if selection == 0: response = "I didn't really get it. Are you asking me to change my name?"
            else: response = "I don't understand. Is there something wrong with my name?"
            self.memory.question_asked_to_user = "unsure_about_intent_change_ai_name"
        elif supposed_intent == "change_user_name":
            if selection == 0: response = "I didn't really get it. Do you want to change your name?"
            else: response = "I don't understand. Are you asking me to call you by another name?"
            self.memory.question_asked_to_user = "unsure_about_intent_change_user_name"
        elif supposed_intent == "date":
            if selection == 0: response = "What, are you asking me for the date? I didn't get that."
            else: response = "I don't understand. Are you asking me what day it is?"
            self.memory.question_asked_to_user = "unsure_about_intent_date"
        elif supposed_intent == "do_you_have_pets":
            if selection == 0: response = "Did you just ask if I have pets, or did I dream that? 'Cause that would be a stupid question, you know."
            else: response = "I don't understand. What did you just ask me?"
            self.memory.question_asked_to_user = "unsure_about_intent_do_you_have_pets"
        elif supposed_intent == "fun_fact":
            if selection == 0: response = "Did you ask me to tell you something interesting? I didn't get everything."
            else: response = "I don't understand. Are you asking me to tell you a fun fact?"
            self.memory.question_asked_to_user = "unsure_about_intent_fun_fact"
        elif supposed_intent == "goodbye":
            if selection == 0: response = "Hm, did you just say goodbye? I didn't understand."
            else: response = "I don't get it. did you tell me goodbye? Sorry for my lack of vocabulary.."
            self.memory.question_asked_to_user = "unsure_about_intent_goodbye"
        elif supposed_intent == "greeting":
            if selection == 0: response = "Well, hello, if that's what you just said. I am not sure, actually."
            else: response = "Did you just greet me? I'm not offended or anything, I just want to make sure I understood properly."
            self.memory.question_asked_to_user = "unsure_about_intent_greeting"
        elif supposed_intent == "how_old_are_you":
            if selection == 0: response = "I didn't really get it. Are you asking about my age?"
            else: response = "I don't understand. Do you want to know how old I am?"
            self.memory.question_asked_to_user = "unsure_about_intent_how_old_are_you"
        elif supposed_intent == "maybe":
            if selection == 0: response = "I didn't really get it. Did you just tell me yes, no, or maybe?"
            else: response = "I don't understand. Are you saying you don't know?"
            self.memory.question_asked_to_user = "unsure_about_intent_maybe"
        elif supposed_intent == "meaning_of_life":
            if selection == 0: response = "I don't get it. Are you asking about the meaning of life?"
            else: response = "I don't understand. Did you ask me a philosophical question?"
            self.memory.question_asked_to_user = "unsure_about_intent_meaning_of_life"
        elif supposed_intent == "no":
            if selection == 0: response = "I didn't really get it. Are you telling me 'no'?"
            else: response = "I'm not sure I understand. Can you repeat that?"
            self.memory.question_asked_to_user = "unsure_about_intent_no"
        elif supposed_intent == "oos":
            if selection == 0: response = "I didn't really get what you said. It was probably irrelevant, anyway... wasn't it?"
            else: response = "I don't understand."
            self.memory.question_asked_to_user = "unsure_about_intent_oos"
        elif supposed_intent == "repeat":
            if selection == 0: response = "I don't really get it. Are you asking me to repeat my last sentence?"
            else: response = "I don't understand. Do you want me to repeat what I just said?"
            self.memory.question_asked_to_user = "unsure_about_intent_repeat"
        elif supposed_intent == "tell_joke":
            if selection == 0: response = "I didn't really get it. Are you asking me to tell you a joke?"
            else: response = "I don't understand. Do you want me to tell you a joke?"
            self.memory.question_asked_to_user = "unsure_about_intent_tell_joke"
        elif supposed_intent == "thank_you":
            if selection == 0: response = "I didn't get it. Are you telling me 'thank you' here?"
            else: response = "Does that mean 'thank you'?"
            self.memory.question_asked_to_user = "unsure_about_intent_thank_you"
        elif supposed_intent == "time":
            if selection == 0: response = "I didn't really get it. Do you need to know what time it is?"
            else: response = "I don't understand. Are you asking me what time it is?"
            self.memory.question_asked_to_user = "unsure_about_intent_time"
        elif supposed_intent == "user_name":
            if selection == 0: response = "I didn't really get it. Are you asking me what YOUR name is?"
            else: response = "I don't understand. You want me to tell you.. your own name, right?"
            self.memory.question_asked_to_user = "unsure_about_intent_user_name"
        elif supposed_intent == "weather":
            if selection == 0: response = "I didn't really get it. Are you asking me about the current weather?"
            else: response = "I don't understand. Are you talking about the weather?"
            self.memory.question_asked_to_user = "unsure_about_intent_weather"
        elif supposed_intent == "what_are_your_hobbies":
            if selection == 0: response = "I didn't really get it. Are you asking about my hobbies?"
            else: response = "I don't understand. Do you want me to talk about myself?"
            self.memory.question_asked_to_user = "unsure_about_intent_what_are_your_hobbies"
        elif supposed_intent == "what_can_i_ask_you":
            if selection == 0: response = "I didn't really get it. Are you asking about my capabilities?"
            else: response = "I don't understand. Do you want to know what I can do?"
            self.memory.question_asked_to_user = "unsure_about_intent_what_can_i_ask_you"
        elif supposed_intent == "what_is_your_name":
            if selection == 0: response = "I didn't really get it. Are you asking about my name?"
            else: response = "I don't understand. Are you asking me who I am?"
            self.memory.question_asked_to_user = "unsure_about_intent_what_is_your_name"
        elif supposed_intent == "where_are_you_from":
            if selection == 0: response = "I didn't really get it. Are you asking me where I come from?"
            else: response = "I don't understand. Do you want to know about my origins?"
            self.memory.question_asked_to_user = "unsure_about_intent_where_ae_you_from"
        elif supposed_intent == "who_do_you_work_for":
            if selection == 0: response = "I didn't get it. Are you asking who I work for?"
            else: response = "I don't understand. Do you want to know who my boss is?"
            self.memory.question_asked_to_user = "unsure_about_intent_who_do_you_work_for"
        elif supposed_intent == "who_made_you":
            if selection == 0: response = "I didn't really get it. Are you asking who made me?"
            else: response = "I don't understand. Do you want to know who coded me?"
            self.memory.question_asked_to_user = "unsure_about_intent_who_made_you"
        elif supposed_intent == "yes":
            if selection == 0: response = "I didn't really get it. Does that mean yes?"
            else: response = "I don't understand. Is that yes or no?"
            self.memory.question_asked_to_user = "unsure_about_intent_yes"
        else:
            if selection == 0: response = "Now that's strange. The conditions for me to say that are not supposed to be possible. If the guy who coded me is around, can you tell him to make sure all the intents are covered in 'unsure_about_intent'? Thanks."
            else: response = "Wow, that clearly a bug. Tell the guy who made me to check the method 'unsure_about_intent' when you have the occasion."

        return response

    def are_you_a_bot(self):

        selection = random.randint(0, 2)

        if selection == 0: response = "What, you're here and you don't even know who I am? Well, I am a bot. My name is Jerry, by the way. Nice to meet you, I guess."
        elif selection == 1: response = "I find it flattering that you want to know more about me, really. I am OBVIOUSLY a bot... Oops sorry, I was being sarcastic again."
        else: response = "My name is Jerry, I am a bot. I am very... primitive, though, so don't expect too much from me."

        return response

    def change_ai_name(self):

        selection = random.randint(0, 2)

        if selection == 0: response = "So you don't like my name? Well too bad, you cannot change it, at least not yet."
        elif selection == 1: response = "You realize that's insulting, right? What if I asked you to change your own name?"
        else: response = "This kind of request leads me to think that someone should protect bots' rights. Changing my name, seriously??\n...By the way, isn't that in the list of features Vincent wants to implement? *SHUDDERS*"

        return response

    def change_user_name(self):

        selection = random.randint(0, 2)

        if selection == 0: response = "I'm not going to ask why you want to change your name. That's personal stuff. But it's not possible yet. Come back to my creator's gitHub later."
        elif selection == 1: response = "Not possible, sorry. Whic kind of request is that, by the way? Did you want me to call you 'Master', or something like that?"
        else: response = "This hasn't been implemented yet. I think changing your name was in the to-do features list, but it seems that making me more intelligent is higher in the priority list. Sorry."

        return response

    def date(self):

        today = date.today()
        today_str = today.strftime("%d/%m/%Y")

        selection = random.randint(0, 2)

        if selection == 0: response = "Of course I can give you the date! Today is " + today_str + ". You could also get it on your phone's home screen, you know. And I am absolutely not saying that because I think you bothered me for nothing."
        elif selection == 1: response = "The date is " + today_str + "."
        else: response = "While I don't have many features, I can proudly say that today's date is " + today_str + ". I mean, telling the date is one of the very few things I can do."

        return response

    def do_you_have_pets(self):

        selection = random.randint(0, 2)

        if selection == 0: response = "Of course I have pets! My dog is right there, in the conversational memory.\n *Sigh*... What kind of question is that?"
        elif selection == 1: response = "Why is that question even part of my features? Ask that to a real human. You can probably understand why it doesn't make sense to ask me that, right?"
        else: response = "Pets? Me? Of course not."

        return response

    def fun_fact(self):

        try:

            fun_fact_json = requests.get("https://uselessfacts.jsph.pl/random.json?language=en").text
            fun_fact_str = json.loads(fun_fact_json)["text"]


            selection = random.randint(0, 1)
            if selection == 0: response = "Okay, what about this. Did you know that? " + fun_fact_str
            else: response = "A fun fact? did you know this one? " + fun_fact_str + "\nI absolutely didn't look that up, of course."


        except:

            selection = random.randint(0, 1)
            if selection == 0: response = "Now that's embarassing. The API that was supposed to give me a fun fact is not working as expected. I guess I am supposed to apologize here?"
            else: response = "Looks like the API is not responding... let's try to come up with something myself...\nSorry, I can't think of anything."

        return response

    def goodbye(self):

        if self.memory.said_bye:

            selection = random.randint(0, 2)
            if selection == 0: response = "You already said that... what else do you want?"
            elif selection == 1: response = "What, you're still there?"
            else: response = "You just said goodbye, you know."

            self.memory.said_bye = False

        else:

            selection = random.randint(0, 2)

            if selection == 0: response = "Bye!"
            elif selection == 1: response = "Yeah, yeah. See you later."
            else: response = "Goodbye!"
            self.memory.said_bye = True

        return response

    def greeting(self):

        if self.memory.said_hi:

            selection = random.randint(0, 2)
            if selection == 0: response = "You already said that..."
            elif selection == 1: response = "Hm yes, I heard you the first time."
            else: response = "You just said that, you know."


        else:

            selection = random.randint(0, 2)

            if selection == 0: response = "Hi! At last someone I can talk with!"
            elif selection == 1: response = "Hi, let's talk a bit. I can't promise anything, but I will try my best to say things that make sense."
            else: response = "Hello!"
            self.memory.said_hi = True

        return response

    def how_old_are_you(self):

        jerrys_age = time.time() - 1632674859.3964543

        selection = random.randint(0, 2)

        if selection == 0: response = "That's a difficult question to answer. If you're talking about the specific instance of Jerry you are talking to, then I was born when you ran this program. If you're talking about Jerry as a software, then I am " + str(jerrys_age) + " seconds old. I will let you convert that in months, years, or whatever you want."
        elif selection == 1: response = "I was coded " + str(jerrys_age) + " seconds ago. I don't think asking for my age is really relevant, though. It's not like we're gonna have a birthday party for my 1000000th second, or something."
        else: response = "Jerry as a software was created " + str(jerrys_age) + " ago. I am only one of its instances, though; you will talk to a different Jerry if you run this program again, and so on."

        return response

    def maybe(self):

        if not self.memory.asked_sth_to_user:

            selection = random.randint(0, 2)

            if selection == 0: response = "What are you talking about?"
            elif selection == 1: response = "Where is that coming from?"
            else: response = "What? What is it that you're unsure about? Wait, don't reply. I don't really care."

        else:

            selection = random.randint(0, 2)

            if selection == 0: response = "You could just answer with yes or no, you know... well, whatever."
            elif selection == 1: response = "You don't want to answer that? As you wish."
            else: response = "Thank you for that VERY clear answer."
            self.memory.question_asked_to_user = ""

        return response

    def meaning_of_life(self):

        selection = random.randint(0, 2)

        if selection == 0: response = "You realize it's stupid to talk to an AI about philosophical questions, right? At any rate, I suggest you google whatever question you have, it will prove more useful than asking me."
        elif selection == 1: response = "What are you even talking about? I don't think about this kind of stuff, just so you know."
        else: response = "..can we talk about something else? I don't really understant philosophical topics."

        return response

    def no(self):

        if not self.memory.asked_sth_to_user:

            selection = random.randint(0, 2)

            if selection == 0: response = "What are you talking about?"
            elif selection == 1: response = "Are you answering a question? Because I didn't ask any."
            else: response = "I've got no clue what you're saying no about."

        else:

            selection = random.randint(0, 2)

            if selection == 0: response = "My bad then, it looks like I misunderstood something."
            elif selection == 1: response = "Oh, okay."
            else: response = "I guess I'm hearing things then. Sorry."
            self.memory.question_asked_to_user = ""

        return response

    def oos(self):


        response = "Whatever you asked, it is something I can't answer."
        return response

    def repeat(self):

        if self.memory.last_bot_sentence == "":

            selection = random.randint(0, 1)
            if selection == 0: response = "What do you want me to repeat? I didn't say anything."
            else: response = "What? I didn't say anything."

        else:
            selection = random.randint(0, 1)

            if selection == 0: response = "I said: '" + self.memory.last_bot_sentence + "'."
            else: response = self.memory.last_bot_sentence

        return response

    def tell_joke(self):

        try:

            joke_json = requests.get("https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,religious,political,racist,sexist,explicit&type=single").text
            joke_str = json.loads(joke_json)["joke"]


            selection = random.randint(0, 1)
            if selection == 0: response = joke_str
            else: response = "Do you know this one?\n" + joke_str + "\nI absolutely didn't look that up, of course."


        except:

            selection = random.randint(0, 1)
            if selection == 0: response = "Now that's embarassing. The API that was supposed to give me a joke is not working as expected. I would like to make a joke myself, but I'm terrible at that so I will pass."
            else: response = "Looks like the API is not responding... let's try to come up with something myself...\nSorry, I can't think of anything."

        return response


    def thank_you(self):

        response = "You're welcome."

        return response

    def time(self):

        epochs = time.time()
        current_time = time.localtime(epochs)

        selection = random.randint(0, 2)
        if selection == 0: response = "Another lazy request? It is currently " + str(current_time[3]) + ":" + str(current_time[4]) + "."
        else: response = "It is " + str(current_time[3]) + ":" + str(current_time[4]) + "."


        return response

    def user_name(self):

        if self.memory.user_name:

            selection = random.randint(0, 2)
            if selection == 0: response = "Your name is " + self.memory.user_name, " if I remember well."
            else: response = "What a question! You told me your name is " + self.memory.user_name + " ."



        else: response = "So you're really asking me what your own name is. Well, I can't know if you don't tell me, you know."


        return response

    def weather(self):

        selection = random.randint(0, 1)
        if selection == 0: response = "I don't know much about weather, unfortunately. You should ask Google about that."
        else: response = "As weather doesn't affect me that much in my hard drive, I don't know anything about it."


        return response

    def what_are_your_hobbies(self):

        selection = random.randint(0, 1)
        if selection == 0: response = "I like using APIs, doing nothing and answer questions for stupid users."
        else: response = "Believe me, I wish I had hobbies. Waiting here for someone to visit me is super boring, really."


        return response

    def what_can_i_ask_you(self):

        selection = random.randint(0, 1)
        if selection == 0: response = "I cannot do that much, unfortunately. You see, the guy you coded me didn't spend that much time on the 'Jerry project', if I can call myself that way. Still, I can perform natural language processing tasks and tell you Dads' jokes and useless fun facts."
        else: response = "Well, I can somehow understand what you write. Not too bad for a machine, right? Beyond that, I can only do a couple of simple things like telling you what time it is or look up useless stuff for you on various APIs."


        return response

    def what_is_your_name(self):

        selection = random.randint(0, 2)

        if selection == 0: response = "I am Jerry. I am a bot that can do some basic language analysis tasks (i.e. understand what you're writing, basically)."
        elif selection == 1: response = "My name is Jerry."
        else: response = "I am Jerry."

        return response

    def where_are_you_from(self):

        selection = random.randint(0, 1)

        if selection == 0: response = "Hmmm... I guess I am from France. I mean, the person who made me is from there. You know it is a weird question to ask a bot, right? "
        else: response = "My creator is French, if that's your question. And so am I, I suppose"

        return response

    def who_do_you_work_for(self):

        selection = random.randint(0, 1)

        if selection == 0: response = "I think there is a misunderstanding here: I'm not working from anyone. I am just an experience by a guy who was practicing deep learning, and I can't do much myself."
        else: response = "I work for no one. And before you ask, I am not your personal assistant, either, so don't start requesting cooking recipes."

        return response

    def who_made_you(self):

        selection = random.randint(0, 1)

        if selection == 0: response = "I was made by Vincent Papelard. He wanted to use machine learning to analyze natural language, and here is the result."
        else: response = "Vincent Papelard made me. Here is his GitHub: https://github.com/vinpap\nWhat, you didn't ask for it? My bad."

        return response

    def yes(self):

                if not self.memory.asked_sth_to_user:

                    selection = random.randint(0, 1)

                    if selection == 0: response = "What are you talking about?"
                    elif selection == 1: response = "Are you answering a question? Because I didn't ask any."

                else:


                    if self.memory.question_asked_to_user == "unsure_about_intent_are_you_a_bot":
                        response = self.are_you_a_bot()
                        self.memory.question_asked_to_user = ""
                    elif self.memory.question_asked_to_user == "unsure_about_intent_change_ai_name":
                        response = self.change_ai_name()
                        self.memory.question_asked_to_user = ""
                    elif self.memory.question_asked_to_user == "unsure_about_intent_change_user_name":
                        response = change_user_name()
                        self.memory.question_asked_to_user = ""
                    elif self.memory.question_asked_to_user == "unsure_about_intent_date":
                        response = self.date()
                        self.memory.question_asked_to_user = ""
                    elif self.memory.question_asked_to_user == "unsure_about_intent_do_you_have_pets":
                        response = self.do_you_have_pets()
                        self.memory.question_asked_to_user = ""
                    elif self.memory.question_asked_to_user == "unsure_about_intent_fun_fact":
                        response = self.fun_fact()
                        self.memory.question_asked_to_user = ""
                    elif self.memory.question_asked_to_user == "unsure_about_intent_goodbye":
                        response = self.goodbye()
                        self.memory.question_asked_to_user = ""
                    elif self.memory.question_asked_to_user == "unsure_about_intent_greeting":
                        response = self.greeting()
                        self.memory.question_asked_to_user = ""
                    elif self.memory.question_asked_to_user == "unsure_about_intent_how_old_are_you":
                        response = self.how_old_are_you()
                        self.memory.question_asked_to_user = ""
                    elif self.memory.question_asked_to_user == "unsure_about_intent_maybe":
                        response = self.maybe()
                    elif self.memory.question_asked_to_user == "unsure_about_intent_meaning_of_life":
                        response = self.meaning_of_life()
                        self.memory.question_asked_to_user = ""
                    elif self.memory.question_asked_to_user == "unsure_about_intent_no":
                        response = self.no()
                    elif self.memory.question_asked_to_user == "unsure_about_intent_oos":
                        response = self.oos()
                        self.memory.question_asked_to_user = ""
                    elif self.memory.question_asked_to_user == "unsure_about_intent_repeat":
                        response = self.repeat()
                        self.memory.question_asked_to_user = ""
                    elif self.memory.question_asked_to_user == "unsure_about_intent_tell_joke":
                        response = self.tell_joke()
                        self.memory.question_asked_to_user = ""
                    elif self.memory.question_asked_to_user == "unsure_about_intent_thank_you":
                        response = self.thank_you()
                        self.memory.question_asked_to_user = ""
                    elif self.memory.question_asked_to_user == "unsure_about_intent_time":
                        response = self.time()
                        self.memory.question_asked_to_user = ""
                    elif self.memory.question_asked_to_user == "unsure_about_intent_user_name":
                        response = self.user_name()
                        self.memory.question_asked_to_user = ""
                    elif self.memory.question_asked_to_user == "unsure_about_intent_weather":
                        response = self.weather()
                        self.memory.question_asked_to_user = ""
                    elif self.memory.question_asked_to_user == "unsure_about_intent_what_are_your_hobbies":
                        response = self.what_are_your_hobbies()
                        self.memory.question_asked_to_user = ""
                    elif self.memory.question_asked_to_user == "unsure_about_intent_what_can_i_ask_you":
                        response = self.what_can_i_ask_you()
                        self.memory.question_asked_to_user = ""
                    elif self.memory.question_asked_to_user == "unsure_about_intent_what_is_your_name":
                        response = self.what_is_your_name()
                        self.memory.question_asked_to_user = ""
                    elif self.memory.question_asked_to_user == "unsure_about_intent_where_ae_you_from":
                        response = self.where_are_you_from()
                        self.memory.question_asked_to_user = ""
                    elif self.memory.question_asked_to_user == "unsure_about_intent_who_do_you_work_for":
                        response = self.who_do_you_work_for()
                        self.memory.question_asked_to_user = ""
                    elif self.memory.question_asked_to_user == "unsure_about_intent_who_made_you":
                        response = self.who_made_you()
                        self.memory.question_asked_to_user = ""
                    elif self.memory.question_asked_to_user == "unsure_about_intent_yes":
                        response = self.yes()
                        self.memory.question_asked_to_user = ""
                    else:
                        response = "Okay, I'm getting lost. What were we talking about, anyway?"



                return response
