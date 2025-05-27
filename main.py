from typing import List

import pygame
import sys
from enum import Enum
import socket
import threading

from nltk.downloader import update
from pygame.rect import RectType
from pygame.time import Clock
from pygame import Surface

WINDOW_WIDTH  = 1000
WINDOW_HEIGHT = 600
# CHAT_AREA_X   = LEFT_MARGIN + BOARD_WIDTH + 20
# CHAT_AREA_WIDTH  = WINDOW_WIDTH - CHAT_AREA_X - 20
#
# RESTART_BTN_RECT = pygame.Rect(CHAT_AREA_X, TOP_MARGIN + BOARD_HEIGHT + 10, 160, 30)
# CANCEL_BTN_RECT  = pygame.Rect(CHAT_AREA_X + 170, TOP_MARGIN + BOARD_HEIGHT + 10, 100, 30)
# START_BTN_RECT   = pygame.Rect(CHAT_AREA_X + 280, TOP_MARGIN + BOARD_HEIGHT + 10, 60, 30)
# GIVE_UP_BTN_RECT = pygame.Rect(CHAT_AREA_X + 350, TOP_MARGIN + BOARD_HEIGHT + 10, 90, 30)
#
# POINTS_SIZE = WINDOW_HEIGHT - TOP_MARGIN - BOARD_HEIGHT - 10 - TOP_MARGIN
# PLAYER_POINTS_RECT   = pygame.Rect(LEFT_MARGIN, TOP_MARGIN + BOARD_HEIGHT + 10, POINTS_SIZE, POINTS_SIZE)
# OPPONENT_POINTS_RECT = pygame.Rect(LEFT_MARGIN + POINTS_SIZE + 140, TOP_MARGIN + BOARD_HEIGHT + 10, POINTS_SIZE, POINTS_SIZE)
#
# BOARD_BACKGROUD_RECT = pygame.Rect(LEFT_MARGIN, TOP_MARGIN, ROWS*SQUARE_SIZE, COLS*SQUARE_SIZE)

# Cores
WHITE = (230, 230, 230)
BLACK = (25, 25, 25)
BG_COLOR = (0x36, 0x38, 0x6B)
PLAYER_COLORS = [(0x50, 0x96, 0x32), (0xEB, 0x49, 0x00), WHITE]  # Azul e vermelho
BTN_COLORS = (0x7c, 0x7F, 0xEA)

# Janela
pygame.display.set_caption("Seega")

class Buttons:
    pass

class Chat:
    pass

class Player:
    def __init__(self):
        self.pieces :List[Pieces] = []

        self.points         :int = 0

        self.color :tuple[int,int,int] = (0x0, 0x0, 0x0)



class Board:
    def __init__(self, window: Surface):
        self.window = window

        self.board_size          :int = 5
        self.board_left_margin   :int = 20
        self.square_quant_pixels :int = 100

        self.selected_piece      :List[int] = [-1, -1]

        self.board: List[List[int]] = [[-1 for _ in range(self.board_size)] for _ in range(self.board_size)]

        board_pixels_size      :int = self.board_size*self.square_quant_pixels
        self.board_top_margin  :int = (self.window.get_height() - board_pixels_size) // 2 - 30

        self.board_background_rect :RectType = pygame.Rect(self.board_left_margin, self.board_top_margin,
                                                           self.board_size*self.square_quant_pixels,
                                                           self.board_size*self.square_quant_pixels)

    def draw_board(self, board_color: tuple[int, int, int], players: List[Player]):
        pygame.draw.rect(self.window, BLACK, self.board_background_rect)

        # Tabuleiro
        for row in range(self.board_size):
            for col in range(self.board_size):
                rect = pygame.Rect(
                    self.board_left_margin + col * self.square_quant_pixels,
                    self.board_top_margin + row * self.square_quant_pixels,
                    self.square_quant_pixels,
                    self.square_quant_pixels
                )
                pygame.draw.rect(self.window, board_color, rect, 1)

                if self.board[row][col] != -1:
                    color = players[self.board[row][col]].color
                    if self.selected_piece == [row, col]:
                        color = color[1] + 50
                    pygame.draw.circle(self.window, color, rect.center, self.square_quant_pixels // 3)

class Pieces:
    pass

class Window:
    def __init__(self):
        self.general_font = pygame.font.SysFont("Arial", 20)
        self.input_font   = pygame.font.SysFont("Arial", 18)

        self.window : Surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

        self.board  : Board   = Board(self.window)
        self.chat   : Chat    = Chat()



class Game:
    def __init__(self):
        pygame.init()

        self.run            :bool  = True

        self.game_state     :int = -1
        self.current_player :int = 0

        self.players :List[Player] = []

        self.clock:Clock = pygame.time.Clock()
        self.window: Window = Window()


    def run_game(self):
        while self.run:
            self.update_display()

    def update_display(self):
        if self.game_state == -1:
            board_color = BLACK
        else:
            board_color = self.players[self.current_player].color

        self.clock.tick(60)

        self.window.window.fill(BG_COLOR)

        self.window.board.draw_board(board_color, self.players)

        pygame.display.flip()


class PlayersTurnStatus(Enum):
    MOVED_WITH_REMOVE    = 1
    MOVED_WITHOUT_REMOVE = 2
    INVALID_MOVE         = 3
    OUT_OF_BOUNDS        = 4
    OPPONENTS_PIECE      = 5
    VOID_SPACE           = 6 
    WON                  = 7
    CANCEL               = 8
    NEXT_PLAYER          = 9



class BTNPressed(Enum):
    NO_BTN      = 0
    RESTART_BTN = 1
    CANCEL_BTN  = 2
    START_BTN   = 3
    GIVE_UP_BTN = 4

def main():
    game: Game = Game()

    game.run_game()



if __name__=='__main__':
    main()


