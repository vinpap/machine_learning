"""The interfaces for the classes used in this project are defined here.
See each class' implementation for more info about each method"""

from abc import ABC, abstractmethod

class Player_interface(ABC):

    @abstractmethod
    def play(self, current_state):
        """Asks a player object to play a move given the current state of the
        board"""
        return

    @abstractmethod
    def notify_game_result(self, result):
        """When it's over, gives the player the result of the game. result is an
        integer taking the values 0(loss), 0.5(draw), or 1(win)"""
        return


class Game_system_interface(ABC):

    @abstractmethod
    def play_a_game(self, board_dimensions=(3,3)):
        """Asks the game system to start playing a new game"""
        return

class Graphics_interface(ABC):

    @abstractmethod
    def wait_for_move(self, current_board):
        """Waits for the user's input (i.e. their move)"""
        return

    @abstractmethod
    def update_players_data(self, player_1_is_AI, player_1_scores, player_2_is_AI, player_2_scores):
        """Updates the player data displayed"""
        return

    @abstractmethod
    def update_display(self, current_board):
        """Called when the AI made a move and the display needs to be updated"""
        return
