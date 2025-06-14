from __future__ import annotations
from typing import List, Callable

from enum import Enum
import threading

from pygame.rect import RectType
from pygame.time import Clock
from pygame.font import Font
from pygame import Surface
import pygame

from Pyro5.api import expose, Daemon, locate_ns, Proxy

import time


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
# BOARD_BACKGROUND_RECT = pygame.Rect(LEFT_MARGIN, TOP_MARGIN, ROWS*SQUARE_SIZE, COLS*SQUARE_SIZE)

# Cores
WHITE = (230, 230, 230)
BLACK = (25, 25, 25)
BG_COLOR = (0x36, 0x38, 0x6B)
PLAYER_COLORS = [(0x50, 0x96, 0x32), (0xEB, 0x49, 0x00), WHITE]  # Azul e vermelho
BTN_COLORS = (0x7c, 0x7F, 0xEA)
PLAYER_ID   = 0
OPPONENT_ID = 1

pygame.init()
game  : Game
server: Server



def fit_text_size(text, font, max_width, invert):
    tamanho: int = 0

    # enquanto o tamanho que cabe do texto não tiver chegado no último caractere e o tamanho do texto não tiver passado o max_width
    while tamanho < len(text) and font.size((text[-(tamanho + 1):]) if invert else (text[:tamanho + 1]))[
        0] <= max_width:
        # incrementa uma letra que ira ser mostrada
        tamanho += 1

    return tamanho



def split_text_to_fit(text, font, max_width):
    lines = []
    index = 0

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



def draw_any_rect_with_text(window: Surface, font: Font,color:tuple[int, int, int], rect: RectType, text: str):
    pygame.draw.rect(window, color, rect)
    pygame.draw.rect(window, BLACK, rect, 2)

    btn_text = font.render(text, True, BLACK)
    text_rect = btn_text.get_rect(center=rect.center)
    window.blit(btn_text, text_rect)



class Button:
    def __init__(self, window: Surface, font: Font ,text: str,
                 function: Callable, rect: RectType, color :tuple[int, int, int]):
        self.window   :Surface  = window
        self.font     :Font     = font
        self.rect     :RectType = rect
        self.text     :str      = text
        self.function :Callable = function
        self.color    :tuple[int, int, int] = color


    def draw(self):
        draw_any_rect_with_text(self.window, self.font, self.color, self.rect, self.text)


    def click(self):
        self.function()



class Buttons:
    def __init__(self, window: Surface, quant_buttons: int, text_list: List[str], function_list: List[Callable],
                 left_margin: int, top_margin: int, font: Font):
        self.window : Surface = window

        self.buttons :List[Button] = []
        self.color = (0x7c, 0x7F, 0xEA)

        left_margin_now = left_margin
        for index in range(quant_buttons):
            font_size = font.size(text_list[index])
            rect = pygame.Rect(left_margin_now, top_margin, font_size[0]+10, font_size[1]+10)
            self.buttons.append(Button(self.window, font, text_list[index], function_list[index], rect, self.color))
            left_margin_now += font_size[0]+15


    def verify_btn(self, position=pygame.mouse.get_pos()) -> int:
        for index in range(len(self.buttons)):
            if self.buttons[index].rect.collidepoint(position):
                self.buttons[index].click()
                return index

        return -1


    def draw_btns(self):
        for button in self.buttons:
            button.draw()



class Chat:
    def __init__(self, window: Surface, top_margin: int, left_margin: int, chat_height  :int, chat_width   :int):
        self.window :Surface = window

        self.top_margin  :int = top_margin
        self.left_margin :int = left_margin
        self.chat_height :int = chat_height
        self.chat_width  :int = chat_width

        self.input_chat_height :int = 35

        self.font :Font = pygame.font.SysFont("Arial", 18)

        self.max_messages :int = 17

        self.chat_messages :List[str] = []
        self.input_text :str = ""


    def draw_chat(self):
        chat_messages_height = self.chat_height - self.input_chat_height - self.top_margin

        # desenha um retângulo preto que seria a borda do char e um em cima dele do plano de fundo do chat
        pygame.draw.rect(self.window, WHITE, (self.left_margin, self.top_margin,
                                                   self.chat_width, chat_messages_height))
        pygame.draw.rect(self.window, BLACK, (self.left_margin, self.top_margin,
                                                   self.chat_width, chat_messages_height), 2)

        # pega o topo do chat e cria uma margem
        height = self.top_margin + 5
        for msg in self.chat_messages[-self.max_messages:]:
            # renderiza o texto, o coloca na tela e pega o tamanho da altura do texto,
            # cria uma margem para a proxima mensagem
            text_surface = self.font.render(msg, True, BLACK)
            self.window.blit(text_surface, (self.left_margin + 5,height))
            height += self.font.get_height() + 5  # adiciona altura da fonte + espaço entre linhas

        # faz o retângulo do input
        input_rect = pygame.Rect(self.left_margin, self.top_margin + self.chat_height - self.input_chat_height, self.chat_width, self.input_chat_height)
        pygame.draw.rect(self.window, WHITE, input_rect)
        pygame.draw.rect(self.window, BLACK, input_rect, 2)

        # renderiza o texto de input somente da parte final que caiba no texto e o coloca na tela
        input_surface = self.font.render(
            self.input_text[-fit_text_size(self.input_text, self.font, self.chat_width - 10, True):],
            True, BLACK)
        self.window.blit(input_surface, (input_rect.x + 5, input_rect.y + 5))


    def add_chat_messages(self,  texto:str, origin:str):
        # pega o texto para ser adicionado no chat e verifica e separa ele caso não caiba em somente uma linha
        message = split_text_to_fit(f"{origin}: {texto.strip()}", self.font, self.chat_width - 10)

        for text in message:
            # salva nas mensagens do chat o texto (ou a parte do texto que caiba)
            self.chat_messages.append(text)
            if len(self.chat_messages) > self.max_messages:
                # se a quantidade de texto for maior que o maximo de mensagens no chat, tira a primeira da fila
                self.chat_messages.pop(0)

    def get_chat_input(self, event) -> str:
        value: str

        # verifica se algo do teclado foi precionado
        if event.type == pygame.KEYDOWN:
            # se for um backspace apaga da ultima posição
            if event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]

            # return salva o texto
            elif event.key == pygame.K_RETURN:
                if self.input_text.strip():
                    value = self.input_text
                    self.input_text = ""
                    return value
            else:
                # empede do usuário escrever algo com mais de 200 chars
                if len(self.input_text) < 200:
                    self.input_text += event.unicode

        return ""



class Player:
    def __init__(self, color: tuple[int,int,int]):
        self.points :int = 0
        self.color  :tuple[int,int,int] = color



class Board:
    def __init__(self, window :Surface, board_size :int, left_margin :int, top_margin :int,square_quant_pixels :int):
        self.window :Surface = window

        self.board_size          :int = board_size
        self.top_margin          :int = top_margin
        self.left_margin         :int = left_margin
        self.square_quant_pixels :int = square_quant_pixels

        self.pieces_placed        :List[int] = [0, 0]
        self.selected_piece      :List[int] = [-1, -1]

        self.font: Font = pygame.font.SysFont("Arial", 18)

        self.board: List[List[int]] = [[-1 for _ in range(self.board_size)] for _ in range(self.board_size)]

        self.center :tuple[int, int] = (board_size // 2, board_size // 2)

        self.board_background_rect :RectType = pygame.Rect(self.left_margin, self.top_margin,
                                                           self.board_size*self.square_quant_pixels,
                                                           self.board_size*self.square_quant_pixels)

        points_size = self.window.get_height() - self.top_margin - self.board_size*self.square_quant_pixels - 10 - self.top_margin

        self.player_points_rect = pygame.Rect(self.left_margin,
                                              self.top_margin + self.board_size*self.square_quant_pixels + 10,
                                              points_size, points_size)

        self.opponent_points_rect = pygame.Rect(self.left_margin + points_size + 140,
                                                self.top_margin + self.board_size * self.square_quant_pixels + 10,
                                                points_size, points_size)



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
                    color = PLAYER_COLORS[self.board[row][col]]
                    if self.selected_piece == [row, col]:
                        color = color[1] + 50
                    pygame.draw.circle(self.window, color, rect.center, self.square_quant_pixels // 3)


                draw_any_rect_with_text(self.window, self.font, players[PLAYER_ID].color, self.player_points_rect,
                                        str(players[PLAYER_ID].points) )

                btn_text = self.font.render("player", True, BLACK)

                self.window.blit(btn_text, (self.player_points_rect.x + self.player_points_rect.width + 10,
                                 self.player_points_rect.centery - self.font.get_height() / 2))


                draw_any_rect_with_text(self.window, self.font, players[OPPONENT_ID].color, self.opponent_points_rect,
                                        str(players[OPPONENT_ID].points) )

                btn_text = self.font.render("oponente", True, BLACK)

                self.window.blit(btn_text, (self.opponent_points_rect.x + self.opponent_points_rect.width + 10,
                                 self.opponent_points_rect.centery - self.font.get_height() / 2))



class Window:
    def __init__(self, width: int, height: int, btn_text_list :List[str],btn_function_list: List[Callable]):
        pygame.display.set_caption("Seega")

        self.general_font = pygame.font.SysFont("Arial", 20)

        self.window : Surface = pygame.display.set_mode((width, height))

        board_size          :int = 5
        top_margin          :int = 20
        side_margin         :int = 20
        square_quant_pixels :int = 100

        btn_text_list     :List[str]      = btn_text_list
        btn_function_list :List[Callable] = btn_function_list

        chat_left_margin :int = side_margin + board_size*square_quant_pixels+side_margin
        chat_height      :int = board_size*square_quant_pixels
        chat_width       :int = self.window.get_width() - chat_left_margin - side_margin

        buttons_top_margin :int = top_margin + chat_height + top_margin

        self.board: Board = Board(self.window, board_size, side_margin, top_margin, square_quant_pixels)
        self.chat: Chat = Chat(self.window, top_margin, chat_left_margin, chat_height, chat_width)
        self.buttons : Buttons = Buttons(self.window, 4, btn_text_list, btn_function_list,
                                         chat_left_margin, buttons_top_margin, self.general_font)

    class BTNPressed(Enum):
        NO_BTN      = -1
        RESTART_BTN = 0
        CANCEL_BTN  = 1
        GIVE_UP_BTN = 2
        START_BTN   = 3

    def update_window(self, board_color: tuple[int, int, int], players: List[Player]):
        self.window.fill(BG_COLOR)
        self.board.draw_board(board_color, players)
        self.chat.draw_chat()
        self.buttons.draw_btns()



@expose
class Interface:
    @staticmethod
    def start(sistem_player: int = 0):
        global game
        game.start(sistem_player)


    @staticmethod
    def give_up(sistem_player:int = None):
        global game
        game.give_up(sistem_player)


    @staticmethod
    def add_chat_messages(texto:str, origin:str="player"):
        global game
        game.add_chat_messages(texto, origin)


    @staticmethod
    def reset(init:bool = False):
        global game
        game.reset(init)


    @staticmethod
    def put_peace(row: int, col: int, send: bool = True):
        global game
        game.put_peace(row, col, send)

    @staticmethod
    def pass_turn(send: bool = True):
        global game
        game.pass_turn(send)



class Game:
    def __init__(self):
        self.enemy_game            = None
        self.run            :bool  = True

        self.game_state     :int = -1
        self.current_player :int = 0
        self.sistem_player  :int = 0
        self.max_pieces     :int = 12

        self.players :List[Player] = [Player(WHITE), Player(WHITE)]

        self.window_width  :int = 1000
        self.window_height :int = 600
        self.btn_text_list     :List[str]      = ["Reiniciar partida", "Cancelar", "Desistir", "Start"]
        self.btn_function_list :List[Callable] = [self.reset,  self.cancel, self.give_up, self.start]

        self.clock:Clock = pygame.time.Clock()
        self.window: Window = Window(self.window_width, self.window_height,self.btn_text_list,self.btn_function_list)


    def set_enemy_game(self, enemy_game):
        self.enemy_game = enemy_game


    def start(self,  sistem_player: int = 0):
        print(f"start({sistem_player})")

        global server
        if sistem_player == 0:
            server.send_message(Server.MessagesEnum.startGame, (1, ))

        if self.game_state == -1:
            self.game_state += 1
            self.current_player = 0
            self.sistem_player  = sistem_player
            self.players[PLAYER_ID].color = PLAYER_COLORS[sistem_player]
            self.players[OPPONENT_ID].color = PLAYER_COLORS[1 - sistem_player]


    def give_up(self, sistem_player:int = PLAYER_ID):
        print(f"give_up({sistem_player})")

        global server
        if sistem_player == PLAYER_ID:
            server.send_message(Server.MessagesEnum.giveUp, (OPPONENT_ID, ))

        self.players[1 - sistem_player].points += 1
        self.reset(False)


    def add_chat_messages(self, texto:str, origin:str="player"):
        print("add_chat_messages")
        self.window.chat.add_chat_messages(texto, origin)

        if origin == "player":
            server.send_message(Server.MessagesEnum.playerMessages, (texto, "oponente"))


    def reset(self, init:bool = False):
        print("reset")
        # self.window: Window = Window(self.window_width, self.window_height,self.btn_text_list,self.btn_function_list)

        if init:
            for player in self.players:
                player.points = 0

        self.add_chat_messages(f"clique em start para começar.", "sistema")

    def put_peace(self, row: int, col: int, send: bool = True):
        print(f"put_peace({row}, {col}, {send})")
        self.window.board.board[row][col] = self.current_player
        self.window.board.pieces_placed[self.current_player] += 1

        if send:
            server.send_message(Server.MessagesEnum.putPeace, (row, col, False))


    def pass_turn(self, send: bool = True):
        print(f"pass_turn({send})")
        self.current_player = 1 - self.current_player

        if send:
            server.send_message(Server.MessagesEnum.passTurn, (False, ))


    def cancel(self):
        pass


    def handle_placement(self, pos) -> bool:
        x, y = pos
        col = (x - self.window.board.left_margin) // self.window.board.square_quant_pixels
        row = (y - self.window.board.top_margin) // self.window.board.square_quant_pixels

        if 0 <= row < self.window.board.board_size and 0 <= col < self.window.board.board_size:
            if (row, col) == self.window.board.center:
                return False

            if (self.window.board.board[row][col] == -1 and
                self.window.board.pieces_placed[self.current_player] < self.max_pieces):

                self.put_peace(row, col)
                return True

        return False


    def show_screen(self):
        if self.game_state == -1:
            board_color = BLACK
        else:
            board_color = PLAYER_COLORS[self.current_player]

        self.clock.tick(60)
        self.window.update_window(board_color, self.players)
        pygame.display.flip()


    def run_game(self):
        self.reset(True)

        while self.run:
            self.show_screen()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    position = pygame.mouse.get_pos()
                    if self.window.BTNPressed(self.window.buttons.verify_btn(position=position)) == self.window.BTNPressed.NO_BTN:
                        if self.game_state == 0:
                            if (self.current_player == self.sistem_player and self.handle_placement(position) and
                                self.window.board.pieces_placed[self.current_player] % 2 == 0):
                                time.sleep(0.1)
                                self.pass_turn()

                            if sum(self.window.board.pieces_placed) >= self.max_pieces * 2:
                                print("aqui 2")
                                self.game_state = 1
                else:
                    chat_text = self.window.chat.get_chat_input(event)
                    if chat_text != "":
                        self.add_chat_messages(chat_text, "player")



class Server:
    class MessagesEnum(Enum):
        noMessage      = -1
        playerMessages = 0
        putPeace       = 1
        movePeace      = 2
        startGame      = 3
        passTurn       = 4
        restartGame    = 5
        giveUp         = 6
        notOccupied    = 7

    def __init__(self):
        self.messageCommand : Server.MessagesEnum = Server.MessagesEnum.noMessage
        self.messageArgs    : tuple = ()
        self.messageKargs   : dict = {}

        self.semaforo = threading.Semaphore(0)
        self.semaforo1 = threading.Semaphore(1)


    def send_message(self, msg_command: Server.MessagesEnum, msg_args: tuple = (), msg_kargs = None):
        self.semaforo1.acquire()
        self.messageCommand = msg_command
        self.messageArgs    = msg_args
        self.messageKargs   = msg_kargs if msg_kargs is not None else {}
        self.semaforo1.release()
        self.semaforo.release()


    def run(self):
        while True:
            time.sleep(1)
            try:
                ns = locate_ns(port=9090)
                uri_remoto = ns.lookup("1")
                break
            except Exception as e:
                print(f"name server connect:  {e}")

        while True:
            self.semaforo.acquire()
            self.semaforo1.acquire()
            if self.messageCommand != Server.MessagesEnum.noMessage:
                # try:
                    if self.messageCommand == Server.MessagesEnum.playerMessages:
                        Proxy(uri_remoto).add_chat_messages(*self.messageArgs, **self.messageKargs)

                    elif self.messageCommand == Server.MessagesEnum.putPeace:
                        Proxy(uri_remoto).put_peace(*self.messageArgs, **self.messageKargs)

                    elif self.messageCommand == Server.MessagesEnum.movePeace:
                        pass

                    elif self.messageCommand == Server.MessagesEnum.startGame:
                        Proxy(uri_remoto).start(*self.messageArgs, **self.messageKargs)

                    elif self.messageCommand == Server.MessagesEnum.passTurn:
                        Proxy(uri_remoto).pass_turn(*self.messageArgs, **self.messageKargs)

                    elif self.messageCommand == Server.MessagesEnum.restartGame:
                        Proxy(uri_remoto).reset(*self.messageArgs, **self.messageKargs)

                    elif self.messageCommand == Server.MessagesEnum.giveUp:
                        Proxy(uri_remoto).give_up(*self.messageArgs, **self.messageKargs)

                    elif self.messageCommand == Server.MessagesEnum.notOccupied:
                        Proxy(uri_remoto).not_occupied(*self.messageArgs, **self.messageKargs)

                # except Exception as e:
                #     print(e)

                    self.messageCommand = Server.MessagesEnum.noMessage
                    self.messageArgs    = ()
                    self.messageKargs   = {}

                    self.semaforo1.release()


def iniciar_servidor():
    interface: Interface = Interface()

    daemon = Daemon()
    ns = locate_ns(port=9090)

    objeto = interface
    uri = daemon.register(objeto)
    ns.register("2", uri)

    print("[Servidor] Registrado como '2'")
    daemon.requestLoop()



def main():
    global game
    global server

    game   = Game()
    server = Server()

    thread_servidor = threading.Thread(target=iniciar_servidor, daemon=True)
    thread_servidor.start()

    thread_client = threading.Thread(target=server.run, daemon=True)
    thread_client.start()

    time.sleep(2)

    game.run_game()



if __name__=='__main__':
    main()