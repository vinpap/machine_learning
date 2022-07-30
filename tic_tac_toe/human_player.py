"""This class is only used to find out if a player is a human or an AI"""
from interfaces import Player_interface

class Human_player(Player_interface):

    def __init__(self):


        self.is_AI = False


    def play(self, current_state):

        return

    def notify_game_result(self, result):

        return
