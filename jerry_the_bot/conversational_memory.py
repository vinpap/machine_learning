import logging
import csv

class Conversational_Memory:

    """This class is used to save the data related to the ongoing conversation,
    which is useful to allow Jerry to answer some questions (e.g. to know what
    the user is answering to when he is saying yes or no). It also logs
    conversation data for further use to train the model, provided save_conversations=True"""

    def __init__(self, save_conversations=False):

        self.logger = logging.getLogger("conversations_log")
        fh = logging.FileHandler("logs/conversations.log")
        fh.setFormatter(logging.Formatter(fmt='%(asctime)s - %(message)s'))
        self.logger.addHandler(fh)
        self.logger.setLevel(level=logging.INFO)

        # If save_conversations is set to True, all conversations will be fully saved in conversations.log.
        # Moreover, user sentences-intent pairs will be stored in a csv file for further use
        self.save_conversations = save_conversations
        self.user_name = None
        self.last_user_sentence = ""
        self.last_bot_sentence = ""

        self.said_bye = False
        self.said_hi = False

        self.asked_sth_to_user = False
        self.question_asked_to_user = ""




    def save_interaction(self, last_interaction):

        """Updates the conversational memory based on last interaction
        with the user. Also saves that last interaction, if save_conversations
        is set to True.
        Expects an Interaction object"""

        if self.save_conversations:

            self.logger.info("USER - " + last_interaction.user_sentence)
            self.logger.info("JERRY - " + last_interaction.jerrys_answer)

            with open("logs/conversations_data.csv", "a") as csv_storage:

                csv_writer = csv.writer(csv_storage)
                csv_writer.writerow([last_interaction.user_sentence, last_interaction.intent_picked])

        self.last_bot_sentence = last_interaction.jerrys_answer
        self.last_user_sentence = last_interaction.user_sentence




class Interaction:

    """Class used to pass information regarding a single interaction. It does
    not store anything related to previous sentences."""

    def __init__(self, user_sentence, jerrys_answer, intent_picked):

        self.user_sentence = user_sentence
        self.jerrys_answer = jerrys_answer
        self.intent_picked = intent_picked
