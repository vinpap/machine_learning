"""Inherits from Player_interface, defines the behaviour of the AI player"""

import random
import json

import numpy as np

from interfaces import Player_interface

class AI(Player_interface):


    def __init__(self):


        self.is_AI = True

        # If always_explore is set to True, the AI will always try new moves, even when it
        # already knows good moves given the current situation.
        # The exploration_rate is a measure of how often the AI will try new moves
        # vs picking moves it already knows. See should_explore() for more info

        self.always_explore = False
        self.exploration_rate = 1

        if self.always_explore: print("WARNING: AI is in pure learning mode (trying new moves whenever possible)")
        if self.exploration_rate == 0 and not self.always_explore: print("WARNING: AI's exploration rate is set to 0 (never trying new moves)")



        self.training_data = self.load_training_data()
        self.moves_history = []

    def play(self, current_state):


        """current_state: numpy array showing the current state of the board
        return value: numpy array of the board including the move the AI picked, i.e.
        new state of the board"""

        candidate_moves = []
        known_moves = []
        unknown_moves = []
        best_known_candidate = {}
        chosen_move = []

        # Appending arrays corresponding to every possible move in a list called
        # candidate_moves
        for index, value in np.ndenumerate(current_state):

            if value == 0:
                possible_move = current_state.copy()
                possible_move[index] = 1
                candidate_moves.append(possible_move)

        # Checking if every possible move is already known in the training data or not
        # The candidate moves are divided into two lists depending on whether or not
        # they are already known
        for c in candidate_moves:
            move_is_known = False
            for s in self.training_data:
                if np.array_equal(c, s["array"]):
                    # The value of a state represents how likely it is to make the
                    # AI win
                    known_moves.append({"array": s["array"], "value": s["value"]})
                    move_is_known = True
                    break
            #If the move is unknown, there is no known value
            if not move_is_known: unknown_moves.append(c)

        if not known_moves:
            # If there is no already known move given the current state, we pick a random unknown move
            r = random.randint(0, len(unknown_moves)-1)
            chosen_move = unknown_moves[r]
            self.moves_history.append(chosen_move)
            return chosen_move


        if self.always_explore:
            if unknown_moves != []:
                # If we want to explore, we will first try to pick an unknown move
                r = random.randint(0, len(unknown_moves)-1)
                chosen_move = unknown_moves[r]
            else:
                # If there is no unknown move, we randomly pick a move we already know
                chosen_move = known_moves[random.randint(0, len(known_moves)-1)]["array"]
            self.moves_history.append(chosen_move)
            return chosen_move

        # Here we look for the candidate move with the best value among the moves already known
        for m in known_moves:
            if best_known_candidate == {} or m["value"] > best_known_candidate["value"]: best_known_candidate = m

        # should_explore(value) finds out whether or not the AI should try new moves
        # or stick with the best one it already knows, based on the best known candidate
        # value. See implementation for should_explore for more details
        if self.should_explore(best_known_candidate["value"]):
            if unknown_moves != []:
                r = random.randint(0, len(unknown_moves)-1)
                chosen_move = unknown_moves[r]
            else: chosen_move = known_moves[random.randint(0, len(known_moves)-1)]["array"]
        else:
            chosen_move = best_known_candidate["array"]

        self.moves_history.append(chosen_move)
        return chosen_move



    def notify_game_result(self, result):


        self.update_training_scores(result)


    def update_training_scores(self, game_result):

        """ At the end of each game, the value for each state is updated
        depending on the game's result"""

        # We iterate over the list of all moves played in that game
        for state_index in range(len(self.moves_history)):
            # The value of a state is calculated in a way that gives more
            # weight to immediate results. Thus a move that makes the AI win
            # immediately will always have a value of 1. However, if the win only occurs after
            # several rounds, the move's value is decreased because of the discount_factor below

            reward_waiting_time = len(self.moves_history) - state_index - 1
            discount_factor = 1 - reward_waiting_time / len(self.moves_history)
            state_value = game_result * discount_factor
            self.update_training_data(self.moves_history[state_index], state_value)

        self.moves_history.clear()
        self.write_training_data()
        return

    def should_explore(self, state_value):

        """ Decides whether or not the AI should explore vs playing already known
        moves. The better the best known move is, the less likely is to try new moves.
        The exploration rate is a measure of how often the AI will explore. If it is
        set at 0, the AI will never try new things."""

        proba = (1-state_value) * self.exploration_rate
        random_threshold = random.uniform(0,1)

        if random_threshold < proba: return True

        return False

    def load_training_data(self):

        """ The training data is stored in a JSON file"""
        training_data = []

        with open('training.json', 'r+', newline='') as json_file:

            try:
                json_data = json.load(json_file)

            except json.decoder.JSONDecodeError:
                return training_data

        for state in json_data:

            converted_state = {}
            flat_array = np.array(state["array"])
            converted_state["array"] = np.reshape(flat_array, state["dim"])
            converted_state["value"] = state["value"]
            converted_state["occurences"] = state["occurences"]
            training_data.append(converted_state)

        return training_data

    def update_training_data(self, state, value):

        """ This method updates the current training data based on the result of
        the last game"""

        new_occurences_number = 0
        new_state_value = 0

        for state_index in range(len(self.training_data)):

            if np.array_equal(self.training_data[state_index]["array"], state):
                new_occurences_number = self.training_data[state_index]["occurences"]+1
                new_state_value = (self.training_data[state_index]["value"]*self.training_data[state_index]["occurences"]+value)/(self.training_data[state_index]["occurences"]+1)
                existing_data_index = state_index
                break

        if new_occurences_number == 0:
            new_occurences_number = 1
            new_state_value = value
            self.training_data.append({"array": state,
                                        "value": new_state_value,
                                        "occurences": new_occurences_number})
            return

        self.training_data[existing_data_index] = {"array": state,
                                                    "value": new_state_value,
                                                    "occurences": new_occurences_number}



    def write_training_data(self):

        """Writes the updated training data in the JSON file"""
        
        with open('training.json', 'w', newline='') as json_file:

            json_global_list = []

            for state in self.training_data:

                json_entry = {}

                flat_array = state["array"].flatten()
                #json_entry["array"] = np.array2string(flat_array)
                json_entry["array"] = flat_array.tolist()
                json_entry["dim"] = state["array"].shape
                json_entry["value"] = state["value"]
                json_entry["occurences"] = state["occurences"]

                json_global_list.append(json_entry)

            json.dump(json_global_list, json_file, indent=4)
