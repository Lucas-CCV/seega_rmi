from typing import List

import sys
from enum import Enum
import socket
import threading

from nltk.downloader import update

from pygame.rect import RectType
from pygame.time import Clock
from pygame.font import Font
from pygame import Surface
import pygame

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


def fit_text_size(text, font, max_width, invert):
    tamanho: int = 0

    # enquanto o tamanho que cabe do texto não tiver chegado no ultimo caractere e o tamanho do texto não tiver passado o max_width
    while tamanho < len(text) and font.size((text[-(tamanho + 1):]) if invert else (text[:tamanho + 1]))[
        0] <= max_width:
        # incrementa uma letra que ira ser mostrada
        tamanho += 1

    return tamanho


def split_text_to_fit(text, font, max_width):
    lines = []
    index = 0
    tamanho = 0

    while True:
        # pega a quantidade de caracteres que cabem no max_width
        tamanho = fit_text_size(text[index:], font, max_width, False)
        # salva essa parte do texto em uma lista
        lines.append(text[index:index + tamanho])
        # salva a posição inicial do novo texto
        index = index + tamanho

        # se tiver chegado ou passado do final do texto
        if index >= len(text):
            break

    return lines

class Buttons:
    pass

class Chat:
    def __init__(self, window: Surface, top_margin: int, left_margin: int, chat_height  :int, chat_width   :int):
        self.window :Surface = window

        self.top_margin  :int = top_margin
        self.left_margin :int = left_margin
        self.chat_height :int = chat_height
        self.chat_width  :int = chat_width

        self.font :Font = pygame.font.SysFont("Arial", 18)

        self.max_messages :int = 17

        self.chat_messages :List[str] = []
        self.input_text :str = ""


    def draw_chat(self):
        # desenha um retângulo preto que seria a borda do char e um em cima dele do plano de fundo do chat
        pygame.draw.rect(self.window, WHITE, (self.left_margin, self.top_margin,
                                                   self.chat_width, self.chat_height))
        pygame.draw.rect(self.window, BLACK, (self.left_margin, self.top_margin,
                                                   self.chat_width, self.chat_height), 2)

        # pega o topo do chat e cria uma margem
        height = self.top_margin + 5
        for msg in self.chat_messages[-self.max_messages:]:
            # renderiza o texto, o coloca na tela e pega o tamanho da altura do texto,
            # cria uma margem para a proxima mensagem
            text_surface = self.font.render(msg, True, BLACK)
            self.window.blit(text_surface, (self.left_margin + 5,height))
            height += self.font.get_height() + 5  # adiciona altura da fonte + espaço entre linhas

        # faz o retângulo do input
        input_rect = pygame.Rect(self.left_margin, self.top_margin + self.chat_height + 5, self.chat_width, 30)
        pygame.draw.rect(self.window, WHITE, input_rect)
        pygame.draw.rect(self.window, BLACK, input_rect, 2)

        # renderiza o texto de input somente da parte final que caiba no texto e o coloca na tela
        input_surface = self.font.render(
            self.input_text[-fit_text_size(self.input_text, self.font, self.chat_width - 10, True):],
            True, BLACK)
        self.window.blit(input_surface, (input_rect.x + 5, input_rect.y + 5))


    def add_chat_messages(self, origin:str, texto:str):
        # pega o texto para ser adicionado no chat e verifica e separa ele caso não caiba em somente uma linha
        message = split_text_to_fit(f"{origin}: {texto.strip()}", self.font, self.chat_width - 10)

        for text in message:
            # salva nas mensagens do chat o texto (ou a parte do texto que caiba)
            self.chat_messages.append(text)
            if len(self.chat_messages) > self.max_messages:
                # se a quantidade de texto for maior que o maximo de mensagens no chat, tira a primeira da fila
                self.chat_messages.pop(0)



class Player:
    def __init__(self):
        self.points :int = 0
        self.color  :tuple[int,int,int] = (0x0, 0x0, 0x0)



class Board:
    def __init__(self, window :Surface, board_size :int, left_margin :int, top_margin :int,square_quant_pixels :int):
        self.window :Surface = window

        self.board_size          :int = board_size
        self.top_margin          :int = top_margin
        self.left_margin         :int = left_margin
        self.square_quant_pixels :int = square_quant_pixels

        self.selected_piece      :List[int] = [-1, -1]

        self.board: List[List[int]] = [[-1 for _ in range(self.board_size)] for _ in range(self.board_size)]



        self.board_background_rect :RectType = pygame.Rect(self.left_margin, self.top_margin,
                                                           self.board_size*self.square_quant_pixels,
                                                           self.board_size*self.square_quant_pixels)

    def draw_board(self, board_color: tuple[int, int, int], players: List[Player]):
        pygame.draw.rect(self.window, BLACK, self.board_background_rect)

        # Tabuleiro
        for row in range(self.board_size):
            for col in range(self.board_size):
                rect = pygame.Rect(
                    self.left_margin + col * self.square_quant_pixels,
                    self.top_margin + row * self.square_quant_pixels,
                    self.square_quant_pixels,
                    self.square_quant_pixels
                )
                pygame.draw.rect(self.window, board_color, rect, 1)

                if self.board[row][col] != -1:
                    color = players[self.board[row][col]].color
                    if self.selected_piece == [row, col]:
                        color = color[1] + 50
                    pygame.draw.circle(self.window, color, rect.center, self.square_quant_pixels // 3)



class Window:
    def __init__(self, width: int, height: int):
        self.general_font = pygame.font.SysFont("Arial", 20)

        self.window : Surface = pygame.display.set_mode((width, height))

        board_size          :int = 5
        top_margin          :int = 20
        side_margin         :int = 20
        square_quant_pixels :int = 100

        chat_left_margin :int = side_margin + board_size*square_quant_pixels+side_margin
        chat_height      :int = board_size*square_quant_pixels
        chat_width       :int = self.window.get_width() - chat_left_margin - side_margin

        self.board  : Board   = Board(self.window, board_size, side_margin, top_margin, square_quant_pixels)
        self.chat   : Chat    = Chat(self.window, top_margin, chat_left_margin, chat_height, chat_width)


    def update_window(self, board_color:tuple[int, int, int], players: List[Player]):
        self.window.fill(BG_COLOR)
        self.board.draw_board(board_color, players)
        self.chat.draw_chat()



class Game:
    def __init__(self):
        pygame.init()

        self.run            :bool  = True

        self.game_state     :int = -1
        self.current_player :int = 0

        self.players :List[Player] = []

        self.clock:Clock = pygame.time.Clock()
        self.window: Window = Window(1000, 600)

    def show_screen(self):
        if self.game_state == -1:
            board_color = BLACK
        else:
            board_color = self.players[self.current_player].color

        self.clock.tick(60)
        self.window.update_window(board_color, self.players)
        pygame.display.flip()

    def run_game(self):
        while self.run:
            self.show_screen()



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


