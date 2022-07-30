""" This is the central module of the project. It oversees the game """


import random
import numpy as np

from interfaces import Game_system_interface

class Game_system(Game_system_interface):

    def __init__(self, player_1, player_2, graphics=0):

        if not graphics:
            self.no_display = True
        else:
            self.no_display = False
            self.graphics = graphics

        self.player_1 = player_1
        self.player_2 = player_2

        self.player_1_scores = {"WINS": 0, "LOSSES": 0, "DRAWS": 0}
        self.player_2_scores = {"WINS": 0, "LOSSES": 0, "DRAWS": 0}

        self.current_board = []
        self.turn = 0

    def play_a_game(self, board_dimensions=(3,3)):

        """ Start a new game """

        self.current_board = np.zeros(board_dimensions, dtype=np.int8)
        if not self.no_display: self.graphics.update_players_data(self.player_1.is_AI, self.player_1_scores, self.player_2.is_AI, self.player_2_scores)
        self.turn = random.randint(1, 2)

        running = True
        while running:
            # The condition below is triggered when the user closes the game window
            if self.play_one_move() == "EXIT":
                running = False
                return False
            result = self.check_for_endgame()
            if result == "DRAW": # i.e. if the game is a draw
                running = False

                self.player_1_scores["DRAWS"]+=1
                self.player_2_scores["DRAWS"]+=1
                if not self.no_display: self.graphics.update_players_data(self.player_1.is_AI, self.player_1_scores, self.player_2.is_AI, self.player_2_scores)
                self.player_1.notify_game_result(0.5)
                self.player_2.notify_game_result(0.5)

            elif result == 1: # i.e. if Player 1 won
                running = False

                self.player_1_scores["WINS"]+=1
                self.player_2_scores["LOSSES"]+=1
                if not self.no_display: self.graphics.update_players_data(self.player_1.is_AI, self.player_1_scores, self.player_2.is_AI, self.player_2_scores)
                self.player_1.notify_game_result(1)
                self.player_2.notify_game_result(0)

            elif result == 2: # i.e. if Player 2 won
                running = False

                self.player_1_scores["LOSSES"]+=1
                self.player_2_scores["WINS"]+=1
                if not self.no_display: self.graphics.update_players_data(self.player_1.is_AI, self.player_1_scores, self.player_2.is_AI, self.player_2_scores)
                self.player_1.notify_game_result(0)
                self.player_2.notify_game_result(1)

        return True




    def play_one_move(self):

        """ This method is called until someone wins the game """
        if self.turn == 1:

            if self.player_1.is_AI:
                # The board is converted so that the AI can understand it. see
                # convert_board_for_player for more details
                board = self.convert_board_for_player(1)
                new_board = self.player_1.play(board)
                # The board is then converted back to its central representation
                self.current_board = self.convert_back_board_from_ai(new_board, 1)
                if not self.no_display:
                    # Telling the graphics to update the display based on the AI move
                    if self.graphics.update_display(self.current_board) == "EXIT": return "EXIT"

            else:
                if not self.no_display: move = self.graphics.wait_for_move(self.current_board)
                if move == "EXIT": return "EXIT"
                self.current_board[move[0], move[1]] = 1
            self.turn = 2

        elif self.turn == 2:

            if self.player_2.is_AI:
                # The board is converted so that the AI can understand it. see
                # convert_board_for_player for more details
                board = self.convert_board_for_player(2)
                new_board = self.player_2.play(board)
                # The board is then converted back to its central representation
                self.current_board = self.convert_back_board_from_ai(new_board, 2)
                if not self.no_display:
                    # Telling the graphics to update the display based on the AI move
                    if self.graphics.update_display(self.current_board) == "EXIT": return "EXIT"

            else:

                if not self.no_display: move = self.graphics.wait_for_move(self.current_board)
                if move == "EXIT": return "EXIT"
                self.current_board[move[0], move[1]] = 2
            self.turn = 1

    def check_for_endgame(self):

        """Checks if the game is over, i.e. if a player aligned 3 symbols"""
        no_space_left = True
        testing_x = testing_y = range(-1, 2)

        for index, value in np.ndenumerate(self.current_board):
            if value == 0 :
                no_space_left = False

            elif (value == 1) or (value == 2):
                for i in testing_x:
                    for j in testing_y:
                        if i == 0 and j == 0: continue
                        try:
                            if (self.current_board[index[0]+i, index[1]+j] == value) and (self.current_board[index[0]+2*i, index[1]+2*j] == value):
                                if index[0]+i >= 0 and index[0]+2*i >= 0 and index[1]+j >= 0 and index[1]+2*j >= 0:
                                    return value
                        except IndexError:
                            continue

        if no_space_left: return "DRAW"
        return "CONTINUE"

    def convert_board_for_player(self, player_nbr):

        """ The board's state is stored as an array of numbers ranging from
        0 to 2:
        0 = no one played this space
        1 = Player 1 played here
        2 = Player 2 played here
        Meanwhile, the AI needs to get arrays with -1, 0 and 1 where -1 is a
        space played by the opponent, 0 a space that wasn't played, and 1 a space
        already played by the AI. This method takes care of converting the array
        from one format to the other """

        if player_nbr == 1:
            board_for_player_1 = self.current_board.copy()
            for index, value in np.ndenumerate(self.current_board):
                if value == 1:
                    board_for_player_1[index] = 1
                elif value == 2:
                    board_for_player_1[index] = -1
                else:
                    board_for_player_1[index] = 0
            return board_for_player_1

        elif player_nbr == 2:
            board_for_player_2 = self.current_board.copy()
            for index, value in np.ndenumerate(self.current_board):
                if value == 1:
                    board_for_player_2[index] = -1
                elif value == 2:
                    board_for_player_2[index] = 1
                else:
                    board_for_player_2[index] = 0
            return board_for_player_2

    def convert_back_board_from_ai(self, board, player_nbr):

        """This method does the opposit of convert_board_for_player. It converts
        back the array from a matrix of -1, 0 and 1 to a matrix of 0, 1 and 2 """

        if player_nbr == 1:
            actual_board = board.copy()
            for index, value in np.ndenumerate(board):
                if value == 1:
                    actual_board[index] = 1
                elif value == -1:
                    actual_board[index] = 2
                else:
                    actual_board[index] = 0
            return actual_board

        elif player_nbr == 2:
            actual_board = board.copy()
            for index, value in np.ndenumerate(board):
                if value == 1:
                    actual_board[index] = 2
                elif value == -1:
                    actual_board[index] = 1
                else:
                    actual_board[index] = 0
            return actual_board
