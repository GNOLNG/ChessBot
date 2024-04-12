from enum import Enum


class Game_play_mode(Enum):
    computer_mode = "COMPUTER_MODE"
    online_mode = "ONLINE_MODE"


class Input_mode(Enum):
    command_mode = "COMMAND_MODE"
    arrow_mode = "ARROW_MDOE"


class Bot_flow_status(Enum):
    setting_status = "SETTING_STATUS"
    board_init_status = "BOARD_INIT_STATUS"
    game_play_status = "GAME_PLAY_STATUS"


class Game_flow_status(Enum):
    # sub-routine of game play status
    not_start = "NOT_START"
    user_turn = "USER_TURN"
    opponent_turn = "OPPONENT_TURN"
    game_end = "GAME_END"


class Speak_template(Enum):
    ###setting
    welcome_sentense = "Welcome to chess bot!! "
    game_intro_sentense = "you can press control O to find the options. <> press control R to repeat last sentence"
    setting_state_help_message = (
        "tab and choose play with computer engine or other online player"
    )

    ###initialization
    initialize_game_sentense = "Initializing game for you"
    init_state_help_message = "please wait the initializing process"

    ###game play
    game_state_help_message = (
        "You can press control F for command mode or press control J for arrow mode"
    )
    command_panel_help_message = (
        "tab to find other functions <> or press control J for arrow mode"
    )

    arrow_mode_help_message = "use arrow key to travel the chess board <> use space bar to select the piece to move <> and the square to place <>"

    opponent_move_sentense = "{0} {1} moved to {2} "

    ask_for_promote_type = "please indicate promote type by first letter"
    confirm_move = "Confirm move {0} to {1} "
    user_resign = "Resigned"
    check_time_sentense = "you remain {0}, opponent remain {1}"

    user_black_side_sentense = (
        "You are playing as black. Please wait for your opponent's move."
    )
    user_white_side_sentense = "You are playing as white. Please make your first move."
