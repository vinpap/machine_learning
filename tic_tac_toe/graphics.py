""" This class handles the display. See pygame doc for more
details about how everything works """

import time
import pygame
import numpy as np

from interfaces import Graphics_interface

class Graphics(Graphics_interface):

    def __init__(self):

        self.window_size = [850, 850]
        self.current_board = []
        self.grid = []

        self.p1_is_ai = False
        self.p2_is_ai = False
        self.p1_scores = {"WINS": 0, "LOSSES": 0, "DRAWS": 0}
        self.p2_scores = {"WINS": 0, "LOSSES": 0, "DRAWS": 0}
        self.setup_window()

    def setup_window(self):

        pygame.init()
        self.screen = pygame.display.set_mode(self.window_size)
        self.title_font = pygame.font.SysFont('Comic Sans MS', 40)
        self.info_font = pygame.font.SysFont('Comic Sans MS', 30)
        self.title_surface = self.title_font.render('Tic-tac-toe - Reinforcment Learning', False, (0, 0, 0))

    def update_players_data(self, p1_is_ai, p1_scores, p2_is_ai, p2_scores):

        self.p1_is_ai = p1_is_ai
        self.p1_scores = p1_scores

        self.p2_is_ai = p2_is_ai
        self.p2_scores = p2_scores


    def wait_for_move(self, current_board):

        user_move = []
        self.screen.fill((255, 255, 255))

        self.screen.blit(self.title_surface, (self.window_size[0]*0.5 - (self.title_surface.get_width()/2), self.window_size[1]*0.05))
        self.draw_grid(current_board)
        self.display_scores()

        running = True
        while running:

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "EXIT"
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    area_clicked = self.process_click(event.pos[0], event.pos[1])
                    if area_clicked:
                        self.current_board[area_clicked[0], area_clicked[1]] = 1
                        return area_clicked



            pygame.display.flip()

    def update_display(self, current_board):

        self.screen.fill((255, 255, 255))
        self.draw_grid(current_board)
        self.display_scores()

        running = True
        time_per_ai_move = 0
        starting_time = time.time()
        while running:

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "EXIT"

            if time.time() - starting_time >= time_per_ai_move: running = False

            pygame.display.flip()


    def draw_grid(self, current_board):

        self.current_board = current_board
        space_width = round((self.window_size[0]*0.85 - self.window_size[0]*0.15) / self.current_board.shape[1])
        space_height = round((self.window_size[1]*0.85 - self.window_size[1]*0.15) / self.current_board.shape[0])
        x_index = 0
        y_index = 0
        for x in range(round(self.window_size[0]*0.15), round(self.window_size[0]*0.85), space_width):
            for y in range(round(self.window_size[1]*0.15), round(self.window_size[1]*0.85), space_height):
                rect = pygame.Rect(x, y, space_width, space_height)
                self.grid.append([rect, (y_index, x_index)])
                pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)
                y_index += 1
            y_index = 0
            x_index += 1


        for index, value in np.ndenumerate(current_board):
            if value == 1:
                x = round(self.window_size[0]*0.15 + space_width * index[1])
                y = round(self.window_size[1]*0.15 + space_height * index[0])
                pos = (round(x + space_width/2), round(y + space_height/2))
                pygame.draw.circle(self.screen, (0, 0, 255), pos, 0.45*space_height, 5)
            elif value == 2:
                x = round(self.window_size[0]*0.15 + space_width * index[1])
                y = round(self.window_size[1]*0.15 + space_height * index[0])
                pos = (round(x + space_width/2), round(y + space_height/2))
                pygame.draw.circle(self.screen, (255, 0, 0), pos, 0.45*space_height, 5)

    def display_scores(self):

        p1_title = "Player 1"
        p2_title = "Player 2"
        if self.p1_is_ai: p1_title += " (AI)"
        if self.p2_is_ai: p2_title += " (AI)"

        p1_wins = str(self.p1_scores["WINS"])
        p1_losses = str(self.p1_scores["LOSSES"])
        p1_draws = str(self.p1_scores["DRAWS"])

        p2_wins = str(self.p2_scores["WINS"])
        p2_losses = str(self.p2_scores["LOSSES"])
        p2_draws = str(self.p2_scores["DRAWS"])

        p1_lines = [p1_title, "Wins: " + p1_wins, "Losses: " + p1_losses, "Draws: " + p1_draws]
        p2_lines = [p2_title, "Wins: " + p2_wins, "Losses: " + p2_losses, "Draws: " + p2_draws]

        starting_height_ratio = 0.75
        for l in p1_lines:
            surface = self.info_font.render(l, False, (0, 0, 255))
            self.screen.blit(surface, (0, self.window_size[1]*starting_height_ratio))
            starting_height_ratio += 0.05

        starting_height_ratio = 0.75
        for l in p2_lines:
            surface = self.info_font.render(l, False, (255, 0, 0))
            self.screen.blit(surface, (self.window_size[0] * 0.85, self.window_size[1]*starting_height_ratio))
            starting_height_ratio += 0.05


    def process_click(self, click_position_x, click_position_y):

        space_width = round((self.window_size[0]*0.85 - self.window_size[0]*0.15) / self.current_board.shape[1])
        space_height = round((self.window_size[1]*0.86 - self.window_size[1]*0.15) / self.current_board.shape[0])
        for s in self.grid:
            if s[0].collidepoint(click_position_x, click_position_y):
                array_index = s[1]

                if self.current_board[array_index[0], array_index[1]] != 0:
                    return False
                else:
                    return array_index
