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



WHITE = (230, 230, 230)
BLACK = (25, 25, 25)
BG_COLOR = (0x36, 0x38, 0x6B)
PLAYER_COLORS = [(0x50, 0x96, 0x32), (0xEB, 0x49, 0x00), WHITE]  # Azul e vermelho
BTN_COLORS = (0x7c, 0x7F, 0xEA)
PLAYER_ID   = 0
OPPONENT_ID = 1



pygame.init()
game  : Game



def fit_text_size(text, font, max_width, invert):
    tamanho: int = 0

    # enquanto o tamanho que cabe do texto não tiver chegado no último caractere e o tamanho do texto não
    # tiver passado o max_width
    while (tamanho < len(text) and
           font.size((text[-(tamanho + 1):]) if invert else (text[:tamanho + 1]))[0] <= max_width):
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


    def click(self) -> Window.BTNPressed:
        return self.function()



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


    def verify_btn(self, position=pygame.mouse.get_pos()) -> Window.BTNPressed:
        for index in range(len(self.buttons)):
            if self.buttons[index].rect.collidepoint(position):
                return self.buttons[index].click()

        return Window.BTNPressed.NO_BTN


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


    def get_board_position(self, pos):
        x, y = pos
        col_init = (x - self.left_margin) // self.square_quant_pixels
        row_init = (y - self.top_margin) // self.square_quant_pixels

        return col_init, row_init


    def remove_piece(self, row, col, current_player) -> bool:
        removed = False
        test = [-1, 1]

        for i in test:
            if (0 <= row+i < self.board_size and 0 <= row+i*2 < self.board_size and
                not (row+i == self.center[0] and col == self.center[1]) and self.board[row+i][col] != -1 and
                self.board[row+i][col] != current_player and self.board[row+i*2][col] == current_player):

                self.board[row+i][col] = -1
                self.pieces_placed[current_player] -= 1
                removed = True

            if (0 <= col+i < self.board_size and 0 <= col+i*2 < self.board_size and
                not (row == self.center[0] and col+i == self.center[1]) and self.board[row][col+i] != -1 and
                self.board[row][col+i] != current_player and self.board[row][col+i*2] == current_player):

                self.board[row][col+i] = -1
                self.pieces_placed[current_player] -= 1
                removed = True

        return removed



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
    def reset(init:bool = False, send: bool = True):
        global game
        game.reset(init, send)


    @staticmethod
    def put_peace(row: int, col: int, send: bool = True):
        global game
        game.put_peace(row, col, send)


    @staticmethod
    def pass_turn(send: bool = True):
        global game
        game.pass_turn(send)


    @staticmethod
    def move_peace(row_init: int, col_init: int, row_end: int, col_end: int, send: bool = True):
        global game
        game.move_peace(row_init, col_init, row_end, col_end, send)



class Game:
    class PlayersTurnStatus(Enum):
        ERROR                = 0
        MOVED_WITH_REMOVE    = 1
        MOVED_WITHOUT_REMOVE = 2
        INVALID_MOVE         = 3
        OUT_OF_BOUNDS        = 4
        OPPONENTS_PIECE      = 5
        VOID_SPACE           = 6
        WON                  = 7
        CANCEL               = 8
        NEXT_PLAYER          = 9


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

        while True:
            time.sleep(1)
            try:
                ns = locate_ns(port=9090)
                uri_remoto = ns.lookup("1")
                self.enemy_game: Interface = Proxy(uri_remoto)
                break
            except Exception as e:
                print(f"name server connect:  {e}")


    def start(self,  sistem_player: int = 0) -> Window.BTNPressed:
        print(f"start({sistem_player})")

        global server
        if sistem_player == 0:
            self.enemy_game.start(1)

        if self.game_state == -1:
            self.game_state += 1
            self.current_player = 0
            self.sistem_player  = sistem_player
            self.players[PLAYER_ID].color = PLAYER_COLORS[sistem_player]
            self.players[OPPONENT_ID].color = PLAYER_COLORS[1 - sistem_player]

        return Window.BTNPressed.START_BTN


    def give_up(self, sistem_player:int = PLAYER_ID) -> Window.BTNPressed:
        print(f"give_up({sistem_player})")

        global server
        if sistem_player == PLAYER_ID:
            self.enemy_game.give_up(OPPONENT_ID)

        self.players[1 - sistem_player].points += 1
        self.reset(False, False)

        return Window.BTNPressed.GIVE_UP_BTN


    def add_chat_messages(self, texto:str, origin:str="player"):
        print("add_chat_messages")
        self.window.chat.add_chat_messages(texto, origin)

        if origin == "player":
            self.enemy_game.add_chat_messages(texto, "oponente")


    def reset(self, init:bool = False, send: bool = True) -> Window.BTNPressed:
        print(f"reset({init}, {send})")

        self.window.board.board = [[-1 for _ in range(self.window.board.board_size)] for _ in range(self.window.board.board_size)]

        self.current_player = 0
        self.sistem_player = -1
        self.game_state = -1
        self.window.board.pieces_placed = [0, 0]
        self.window.chat.chat_messages = []
        self.window.chat.input_text = ""
        self.window.board.selected_piece = [-1, -1]

        for player in self.players:
            if init:
                player.points = 0
            player.color = PLAYER_COLORS[-1]

        self.add_chat_messages(f"clique em start para começar.", "sistema")

        if send:
            self.enemy_game.reset(init,  False)

        return Window.BTNPressed.RESTART_BTN


    def put_peace(self, row: int, col: int, send: bool = True):
        print(f"put_peace({row}, {col}, {send})")
        self.window.board.board[row][col] = self.current_player
        self.window.board.pieces_placed[self.current_player] += 1

        if send:
            self.enemy_game.put_peace(row, col, False)


    def check_victory(self) -> bool:
        if self.game_state == 1 and (self.window.board.pieces_placed[0] == 0 or self.window.board.pieces_placed[1] == 0):
            self.add_chat_messages(f"vitoria do {"player" if self.sistem_player == self.current_player else "opponent"}", "sistema")
            self.players[PLAYER_ID if self.current_player == self.sistem_player else OPPONENT_ID].points += 1
            return True
        return False


    def pass_turn(self, send: bool = True):
        print(f"pass_turn({send})")

        if send:
            self.enemy_game.pass_turn(False, )
        else:
            self.check_victory()

        self.current_player = 1 - self.current_player

        if sum(self.window.board.pieces_placed) >= self.max_pieces * 2:
            self.game_state = 1


    def move_peace(self, row_init: int, col_init: int, row_end: int, col_end: int, send: bool = True) -> bool:
        self.window.board.board[row_init][col_init] = -1
        self.window.board.board[row_end][col_end] = self.current_player

        if send:
            self.enemy_game.move_peace(row_init, col_init, row_end, col_end, False)

        return self.window.board.remove_piece(row_end, col_end, self.current_player)


    def cancel(self) -> Window.BTNPressed:
        print("cancel->canceled")
        self.window.board.selected_piece = [-1, -1]

        return Window.BTNPressed.CANCEL_BTN


    def handle_placement(self, pos) -> bool:
        col, row = self.window.board.get_board_position(pos)

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


    def players_turn(self, pos) -> Game.PlayersTurnStatus:
        first_play = True

        col_init, row_init = self.window.board.get_board_position(pos)

        if 0 <= row_init < self.window.board.board_size and 0 <= col_init < self.window.board.board_size:
            if self.window.board.board[row_init][col_init] == self.current_player:
                self.window.board.selected_piece = [row_init, col_init]
                while self.run:
                    self.show_screen()

                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.run = False

                        if event.type == pygame.MOUSEBUTTONDOWN:
                            position = pygame.mouse.get_pos()

                            if self.window.buttons.verify_btn(position=position) == self.window.BTNPressed.CANCEL_BTN:
                                if first_play:
                                    return Game.PlayersTurnStatus.CANCEL
                                return Game.PlayersTurnStatus.NEXT_PLAYER

                            else:
                                col_end, row_end = self.window.board.get_board_position((position[0], position[1]))

                                if (0 <= row_end < self.window.board.board_size and
                                    0 <= col_end < self.window.board.board_size):
                                    if (self.window.board.board[row_end][col_end] == -1 and
                                        (abs(row_init - row_end) + abs(col_init - col_end) == 1)):

                                        self.window.board.board[row_end][col_end]  , self.window.board.board[row_init][col_init] =\
                                        self.window.board.board[row_init][col_init], self.window.board.board[row_end][col_end]

                                        self.window.board.selected_piece = [row_end, col_end]

                                        if self.move_peace(row_init, col_init, row_end, col_end):
                                            if self.check_victory():
                                                return Game.PlayersTurnStatus.WON

                                            row_end, row_init = row_init, row_end
                                            col_end, col_init = col_init, col_end
                                            first_play = False
                                            continue

                                        self.window.board.selected_piece = [-1, -1]
                                        return Game.PlayersTurnStatus.MOVED_WITHOUT_REMOVE

                return Game.PlayersTurnStatus.ERROR

            elif self.window.board.board[row_init][col_init] == -1:
                self.add_chat_messages("nenhuma peça selecionada", "sistema")
                return Game.PlayersTurnStatus.VOID_SPACE

            else:
                self.add_chat_messages("peça do openente selecionada", "sistema")
                return Game.PlayersTurnStatus.OPPONENTS_PIECE

        else:
            self.add_chat_messages("fora de area", "sistema")
            return Game.PlayersTurnStatus.OUT_OF_BOUNDS


    def run_game(self):
        self.reset(True, False)

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
                                
                        elif self.game_state == 1  and self.current_player == self.sistem_player:
                                player_turn = self.players_turn(position)
                                if player_turn in (Game.PlayersTurnStatus.MOVED_WITHOUT_REMOVE, Game.PlayersTurnStatus.WON, Game.PlayersTurnStatus.NEXT_PLAYER):
                                    self.pass_turn()
    
                                elif player_turn == Game.PlayersTurnStatus.CANCEL:
                                    self.add_chat_messages("peça selecionada cancelada", "sistema")

                else:
                    chat_text = self.window.chat.get_chat_input(event)
                    if chat_text != "":
                        self.add_chat_messages(chat_text, "player")



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

    thread_servidor = threading.Thread(target=iniciar_servidor, daemon=True)
    thread_servidor.start()

    game   = Game()
    game.run_game()



if __name__=='__main__':
    main()