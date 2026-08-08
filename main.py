import pygame, json
from sys import exit
from random import randint, choice

# INITIAL SETUP ------------------------------------------------------------------------------------------------------------------------

pygame.init()  # initalises pygame
screen_size = 700
screen = pygame.display.set_mode(
    (screen_size, screen_size)
)  # Creates window with width of 800px and height of 400px
pygame.display.set_caption("Rota Game")  # changes window title
clock = pygame.time.Clock()  # creates clock object to control framerate
page = "menu"  # Controls what page is visible from ['menu', 'info', 'single_player', 'multiplayer']
info_page = 0  # Controls the viewed page in the info section
game_won = False  # State so that score increments only on state change, not perpetually during won state
placing_phase = True  # placing phase when the player and computer take turns to place pins before moving them, at which point placing_phase == False
last_move = None  # Keeps track of who made the last move

scores = {"red": 0, "blue": 0}

colours = {
    "dark_purple": "#594765",
    "light_purple": "#D1B2E6",
    "very_dark_purple": "#2A252D",
    "red": "#D74B4B",
    "light_blue": "#B0D5EC",
    "gold": "#D7C04B",
}

winning_conditions = [
    # radial winning conditions (includes centre circle)
    (1, 0, 5),
    (2, 0, 6),
    (3, 0, 7),
    (4, 0, 8),
    # orbital winning conditions (3 in a row round outer circle)
    (1, 2, 3),
    (2, 3, 4),
    (3, 4, 5),
    (4, 5, 6),
    (5, 6, 7),
    (6, 7, 8),
    (7, 8, 1),
    (8, 1, 2),
]

# CLASSES ------------------------------------------------------------------------------------------------------------------------------


class Circle(pygame.sprite.Sprite):
    id = 0
    selected_circle = None
    all = []

    def __init__(self, type, coordinates):
        super().__init__()

        self.id = Circle.id
        Circle.id += 1
        self.selected = False
        self.type = type
        self.show_type()
        self.rect = self.image.get_rect(center=coordinates)
        Circle.all.append(self)

    def show_type(self):
        filepath = "assets/graphics/"
        if self.type == "empty":
            self.image = pygame.image.load(filepath + "unselected.png").convert_alpha()
        elif self.type == "blue":
            self.image = pygame.image.load(filepath + "blue.png").convert_alpha()
        elif self.type == "red":
            self.image = pygame.image.load(filepath + "red.png").convert_alpha()
        self.image = pygame.transform.rotozoom(
            self.image, 0, screen_size / 1000
        ).convert_alpha()

    def deselect_selected_circle(self, move=True):
        selected_circle = [
            circle for circle in Circle.all if circle.id == Circle.selected_circle
        ][0]
        if move:
            selected_circle.type = "empty"
            selected_circle.show_type()
        selected_circle.selected = False
        Circle.selected_circle = None

    def toggle_type(self, click_type):
        global last_move

        move_pin_condition = (
            (self.type == "empty") and (Circle.selected_circle != None)
        )  # to move a pin, user must select an empty space and a selected circle/pin must exist

        if (placing_phase or move_pin_condition) and self.type == "empty":
            # Logic used to place pins (in placing_phase) or move them (move_pin_condiiton)
            if last_move in ["red", None]:
                self.type = "blue"
                last_move = "blue"
            elif last_move == "blue":
                self.type = "red"
                last_move = "red"
            if move_pin_condition:
                self.deselect_selected_circle()  # Removes gold ring from previously selected pin and moves it
        elif self.selected:
            # Deselects a pin if user changes their mind
            self.selected = False
            Circle.selected_circle = None
        elif (self.type == "blue" and last_move == "red") or (
            self.type == "red" and last_move == "blue"
        ):
            # Shows user selecting a pin, but only when it is the appropriate side's turn
            self.selected = True
            if Circle.selected_circle != None:
                self.deselect_selected_circle(
                    False
                )  # Removes previously selection without moving pin
            Circle.selected_circle = self.id

        self.show_type()


class Button:  # new Button class
    def __init__(self, text, id, width, height, pos, elevation=6):
        # Core attributes
        self.id = id
        self.pressed = False
        self.elevation = elevation
        self.dynamic_elevation = elevation
        self.original_y_pos = pos[1]
        self.height = height

        # rect
        self.rect = pygame.Rect((pos), (width, height))
        self.colour = colours["light_purple"]

        # text
        font = pygame.font.Font(None, 30)
        self.text_surf = font.render(text, True, colours["dark_purple"])
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)

    def draw(self):
        # elevation logic
        self.rect.y = self.original_y_pos - self.dynamic_elevation
        self.text_rect.center = self.rect.center
        pygame.draw.rect(screen, self.colour, self.rect, border_radius=12)
        screen.blit(self.text_surf, self.text_rect)

    def check_click(self):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            self.colour = colours["light_blue"]
            if pygame.mouse.get_pressed()[0]:
                self.pressed = True
                self.dynamic_elevation = 0
            elif self.pressed:
                self.dynamic_elevation = self.elevation
                self.pressed = False
                return True
        else:
            self.dynamic_elevation = self.elevation
            self.colour = colours["light_purple"]


# FUNCTIONS -----------------------------------------------------------------------------------------------------------------------------


def find_winner():
    """Returns winner if one is found"""
    for condition in winning_conditions:
        circles = [circle.type for circle in board if circle.id in condition]
        if circles == ["blue"] * 3:
            return "blue"
        elif circles == ["red"] * 3:
            return "red"
    return None


def best_move():
    from operator import itemgetter

    """Finds the best move the computer can make. Blocks user from winning."""

    for condition in winning_conditions:
        # Checks each potential winning condition and creates data for the 3 spaces in the condition
        circles = {circle.id: circle.type for circle in board if circle.id in condition}
        # Reformats the states of the spaces so that if 2 of them are blue, it's easier to find
        circle_states = [item[1] for item in sorted(circles.items(), key=itemgetter(1))]
        # If two of the spaces are blue and the third is empty, the id of the empty space is returned
        if circle_states == ["blue", "blue", "empty"]:
            return [k for k, v in circles.items() if v == "empty"][0]

    return None


def check_illegal_condition():
    red_count = len([circle.type for circle in board if circle.type == "red"])
    blue_count = len([circle.type for circle in board if circle.type == "blue"])

    if red_count > 3 or blue_count > 3:
        return True
    else:
        return False


def get_board_coordinates(centre, x_modifier=0, y_modifier=0):
    a = round(centre)
    b = round(centre * (1 / 3))
    c = round(centre * (8 / 15))
    d = round(centre * (22 / 15))
    e = round(centre * (5 / 3))

    # for legibility
    x, y = x_modifier, y_modifier

    return {
        "centre": (a + x, a + y),
        "north": (a + x, b + y),
        "northeast": (d + x, c + y),
        "east": (e + x, a + y),
        "southeast": (d + x, d + y),
        "south": (a + x, e + y),
        "southwest": (c + x, d + y),
        "west": (b + x, a + y),
        "northwest": (c + x, c + y),
    }


def write(text, coordinates, size=50, colour="#ffffff", pixel_font=False):
    if pixel_font:
        font = pygame.font.Font("assets/font/Pixeltype.ttf", size)
    else:
        font = pygame.font.Font(None, 30)
    text_surf = font.render(text, False, colour)
    text_rect = text_surf.get_rect(center=coordinates)
    screen.blit(text_surf, text_rect)


def write_lines(textlist, coordinates, size=50, colour="#ffffff", pixel_font=False):

    def split_line(line, max_words):
        count = 0
        output = ""
        for char in line:
            if char == " ":
                if count == max_words:
                    output += "\n"
                    count = 0
                else:
                    output += char
                    count += 1
            else:
                output += char
        return output.split("\n")

    def flatten(xss):
        return [x for xs in xss for x in xs]

    textlist = flatten([split_line(line.strip(), 9) for line in textlist])

    for line in textlist:
        line_height = coordinates[1] + (textlist.index(line) + 1) * (size / 2)
        write(line, (coordinates[0], line_height), size, colour, pixel_font)


def computers_turn():
    """Checks if it is the computer's turn to go"""
    global placing_phase

    blues = len([circle for circle in board if circle.type == "blue"])
    reds = len([circle for circle in board if circle.type == "red"])
    if placing_phase == True and (blues > reds):
        computer_place_pin()
    elif not placing_phase:
        computer_move_pin()


def computer_place_pin():
    optimal_choice = [circle for circle in board if circle.id == best_move()]

    if len(optimal_choice) > 0:
        chosen_pin = optimal_choice[0].id
    else:
        chosen_pin = choice([circle.id for circle in board if circle.type == "empty"])

    for circle in board:
        if circle.id == chosen_pin:
            circle.type = "red"
            circle.show_type()


def computer_move_pin():
    """Actual functionality of the computer's moving a pin"""

    # function to find neighbours of a particular space
    def find_empty_neighbours(x):
        all_spaces = list(range(1, 9))
        empty_spaces = [circle.id for circle in board if circle.type == "empty"]
        if x == 0:
            return [space for space in all_spaces if space in empty_spaces]
        elif x == 8:
            x = 0
        options = [all_spaces[x - 2], all_spaces[x], 0]
        return [option for option in options if option in empty_spaces]

    # computer finds the red pins
    computer_pins = [circle.id for circle in board if circle.type == "red"]
    # assigns empty neighbours to its red pins, discards blocked pins
    possible_destinations = {
        id: find_empty_neighbours(id)
        for id in computer_pins
        if len(find_empty_neighbours(id)) > 0
    }

    optimal_choice_found = False

    # checks if optimal move is possible
    for k, v in possible_destinations.items():
        if best_move() in v:
            pin_to_move = k
            destination = best_move()
            optimal_choice_found = True
            break

    # if optimal choice isn't available, pin_to_move is chosen at random
    if not optimal_choice_found:
        pin_to_move = choice(list(possible_destinations.keys()))
        destination = choice(possible_destinations[pin_to_move])

    for circle in board:
        if circle.id == pin_to_move:  # type: ignore
            circle.type = "empty"
            circle.show_type()
        elif circle.id == destination:  # type: ignore
            circle.type = "red"
            circle.show_type()


def clear_game():
    global game_won, placing_phase, last_move
    game_won = False
    placing_phase = True
    last_move = None
    for circle in board:
        circle.type = "empty"
        circle.show_type()
        circle.selected = False


def end_placing_phase():
    global placing_phase
    blues = len([circle for circle in board if circle.type == "blue"])
    reds = len([circle for circle in board if circle.type == "red"])
    if blues == 3 and reds == 3:
        placing_phase = False


# CREATING BOARD AND BUTTONS ----------------------------------------------------------------------------------------------------

board = pygame.sprite.Group()
board_coordinates = get_board_coordinates(screen_size / 2, y_modifier=50)

for coordinates in board_coordinates.values():
    board.add(Circle("empty", coordinates))

buttons = {
    "top": {
        # Buttons that appear at the top of the screen during the game or on the info screen
        "clear": Button("Clear", "clear", 175, 40, (500, 25)),
        "menu": Button("Menu", "menu", 175, 40, (25, 25)),
        "back": Button("Back", "back", 175, 40, (25, 25)),
    },
    "menu": [
        # Buttons that appear in the main menu
        Button("How to play", "info", 175, 40, (260, 240)),
        Button("Single Player", "single_player", 175, 40, (260, 300)),
        Button("Multiplayer", "multiplayer", 175, 40, (260, 360)),
        Button("Quit Game", "quit_game", 175, 40, (260, 420)),
    ],
    "info_page": [
        Button("The Game", "info_0", 175, 40, (60, 600)),
        Button("Single Player", "info_1", 175, 40, (260, 600)),
        Button("Multiplayer", "info_2", 175, 40, (460, 600)),
    ],
}

# GAME LOOP ------------------------------------------------------------------------------------------------------------------------

while True:  # infinite loop to stop screen from immediately closing
    for event in pygame.event.get():
        # INPUTS
        if (
            event.type == pygame.QUIT
        ):  # all quit actions (e.g. closing the window) will stop the program
            pygame.quit()  # un-initalises pygame
            exit()  # sys.exit() stops the rest of the code from running

        if event.type == pygame.MOUSEBUTTONUP and game_won == False:
            pos = pygame.mouse.get_pos()
            for circle in board:
                if circle.rect.collidepoint(pos):
                    circle.toggle_type(event.button)

    screen.fill(colours["dark_purple"])
    write("ROTA", (screen_size / 2, 60), size=100, pixel_font=True)

    if (
        page == "menu"
    ):  # MENU PAGE ------------------------------------------------------------------------------------------------------
        for btn in buttons["menu"]:
            btn.draw()
            if btn.check_click():
                page = btn.id
                info_page = 0
                clear_game()

    elif (
        page == "info"
    ):  # INFO PAGE -----------------------------------------------------------------------------------------------------
        with open("assets/info.json") as file:
            info_text = json.load(file)

        back_button = buttons["top"]["back"]
        back_button.draw()
        if back_button.check_click():
            page = "menu"

        button_background = pygame.Rect((0, 550), (700, 150))
        pygame.draw.rect(screen, colours["very_dark_purple"], rect=button_background)
        for btn in buttons["info_page"]:
            btn.draw()
            if btn.check_click():
                info_page = int(btn.id[-1])

        page_text = info_text[str(info_page)]
        write_lines(page_text, (350, 150))
    else:  # GAME PAGE ---------------------------------------------------------------------------------------------------------------------
        # Drawing Board
        line_details = "#D1B2E6", 10
        for line in [
            ("north", "south"),
            ("east", "west"),
            ("northeast", "southwest"),
            ("northwest", "southeast"),
        ]:
            pygame.draw.line(
                screen,
                line_details[0],
                board_coordinates[line[0]],
                board_coordinates[line[1]],
                width=line_details[1],
            )
        pygame.draw.circle(
            screen,
            line_details[0],
            board_coordinates["centre"],
            screen_size * (2 / 6),
            width=line_details[1],
        )
        board.draw(screen)
        for circle in [circle for circle in board if circle.selected == True]:
            pygame.draw.circle(
                screen,
                colours["gold"],
                circle.rect.center,
                circle.rect.size[0] / 2,
                width=10,
            )

        # Checking Illegal / Winning Condition
        if check_illegal_condition():
            write(f"Illegal move!", (screen_size / 2, 90), pixel_font=True)  # type: ignore
        elif find_winner():
            if game_won == False:
                scores[find_winner()] += 1  # type: ignore
            game_won = True
            write(
                f"{find_winner().capitalize()} Wins!",
                (screen_size / 2, 100),
                size=65,
                pixel_font=True,
            )  # type: ignore
        elif page == "single_player":
            if last_move == "blue":
                computers_turn()
                last_move = "red"

        # If both players have placed 3 pins, placing phase ends
        end_placing_phase()

        # Buttons
        clear_button, menu_button = buttons["top"]["clear"], buttons["top"]["menu"]

        clear_button.draw()
        if clear_button.check_click():
            clear_game()

        menu_button.draw()
        if menu_button.check_click():
            page = "menu"
            scores["red"] = 0
            scores["blue"] = 0

        # Showing scores
        write(f"Blue: {scores['blue']}", coordinates=(75, 650))
        write(f"Red: {scores['red']}", coordinates=(600, 650))

        if page == "single_player":
            write("Human", coordinates=(75, 670))
            write("Computer", coordinates=(600, 670))
        elif page == "multiplayer":
            if last_move == None:
                last_move = "red"
            whose_turn_display = {"blue": (600, 670), "red": (75, 670)}
            write("==========", coordinates=whose_turn_display[last_move])

    pygame.display.update()
    clock.tick(60)  # max frame rate = 60fpsbo
