import sys
import os
from functools import partial
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QDialogButtonBox,
    QDialog,
    QMainWindow,
    QApplication,
    QHBoxLayout,
    QMessageBox,
    QCheckBox,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PyQt6.QtCore import QUrl, Qt, QTimer, QRect
from PyQt6.QtGui import QFont, QShortcut, QKeySequence, QIcon


from Components.board_detection_component import detectChessboard, userColor
from Components.piece_move_component import widgetDragDrop, widgetClick
from Components.chess_validation_component import ChessBoard
from Components.speak_component import TTSThread
from Utils.enum_helper import (
    Input_mode,
    Bot_flow_status,
    Game_flow_status,
    Speak_template,
    Game_play_mode,
)

PIECE_TYPE_CONVERSION = {
    "q": "queen",
    "n": "knight",
    "r": "rook",
    "b": "bishop",
    "p": "pawn",
    "k": "king",
    "none": "empty",
}


class LeftWidget(QWidget):
    """
    This class respresent the left widget.\n
    It contains chess.com web view and invisible grids that assigned after board detection
    """

    def __init__(self):
        super().__init__()

        self.chessWebView = QWebEngineView()

        # profile to store the user account detail
        self.profile = QWebEngineProfile("storage", self.chessWebView)
        self.profile.setPersistentStoragePath(
            os.path.join(current_dir, "Tmp", "chess_com_account")
        )

        web_page = QWebEnginePage(self.profile, self.chessWebView)
        self.chessWebView.setPage(web_page)
        self.chessWebView.load(QUrl("https://www.chess.com"))

        self.chessWebView.setMinimumSize(1000, 550)

        vlayout = QVBoxLayout()
        vlayout.addWidget(self.chessWebView)
        vlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(vlayout)

        self.userLoginName = ""
        self.grids = dict()

    # check whether user logined
    def checkLogined(self):
        def callback(x):
            self.userLoginName = x

        jsCode = """
            function checkLogin() {{
                return document.querySelector(".home-user-info")?.outerText
            }}
            checkLogin();
            """
        self.chessWebView.page().runJavaScript(jsCode, callback)

    # crawl remaining time
    def checkTime(self, callBack):
        jsCode = """
            function checkTime() {{
                clocks = document.querySelectorAll(".clock-time-monospace")
                return [clocks[0].outerText, clocks[1].outerText]
            }}
            checkTime();
            """

        return self.chessWebView.page().runJavaScript(jsCode, callBack)


class CheckBox(QCheckBox):
    """
    CheckBox class that allowd check by enter
    """

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.nextCheckState()
        super(CheckBox, self).keyPressEvent(event)


class RightWidget(QWidget):
    """
    This class respresent the right widget.\n
    It contains command panel to make move, query place.
    """

    def checkBoxStateChanged(self, state):
        global internal_speak_engine
        print(state)
        if state == 2:
            internal_speak_engine = True
        else:
            internal_speak_engine = False

    def __init__(self):
        super().__init__()
        global internal_speak_engine

        self.screen_reader_checkBox = CheckBox("Use internal speak engine")
        self.screen_reader_checkBox.setChecked(True)
        self.screen_reader_checkBox.stateChanged.connect(self.checkBoxStateChanged)
        self.screen_reader_checkBox.setAccessibleName("Use internal speak engine")
        self.screen_reader_checkBox.setAccessibleDescription(
            "tick to use internal speak engine"
        )

        self.playWithComputerButton = QPushButton("Play with computer")
        self.playWithComputerButton.setAccessibleName("Play with computer")
        self.playWithComputerButton.setAccessibleDescription(
            "press enter to play with computer engine"
        )

        self.playWithOtherButton = QPushButton("Play with other online player ")
        self.playWithOtherButton.setAccessibleName("Play with other online player")
        self.playWithOtherButton.setAccessibleDescription(
            "press enter to play with other online player"
        )
        self.playWithComputerButton.setAutoDefault(True)
        self.playWithOtherButton.setAutoDefault(True)

        self.colorBox = QLabel()
        self.colorBox.setText("Assigned Color: ")

        self.opponentBox = QLabel()
        self.opponentBox.setText("Opponent last move: \n")

        self.check_time = QPushButton("Check remaining time")
        self.check_time.setAutoDefault(True)

        self.resign = QPushButton("Resign")
        self.resign.setAutoDefault(True)

        self.check_position = QLineEdit()
        self.check_position.setPlaceholderText("Check position")
        self.check_position.setAccessibleName("Check position input field")
        self.check_position.setAccessibleDescription(
            "you can query a piece or square here"
        )

        self.commandPanel = QLineEdit()
        self.commandPanel.setPlaceholderText("Move Input")
        self.commandPanel.setAccessibleName("Command Panel")
        self.commandPanel.setAccessibleDescription("You can type your move here")
        self.movePair = ("", "")

        font = QFont()
        font.setPointSize(18)
        self.commandPanel.setFont(font)
        self.check_position.setFont(font)

        self.setting_menu = []
        self.setting_menu.append(self.playWithComputerButton)
        self.setting_menu.append(self.playWithOtherButton)

        self.play_menu = []
        self.play_menu.append(self.colorBox)
        self.play_menu.append(self.opponentBox)
        self.play_menu.append(self.resign)
        self.play_menu.append(self.check_time)
        self.play_menu.append(self.check_position)
        self.play_menu.append(self.commandPanel)

        self.setting_layout = QVBoxLayout()
        # self.setting_layout.addWidget(self.screen_reader_checkBox)
        for w in self.setting_menu:
            self.setting_layout.addWidget(w)

        for w in self.play_menu:
            self.setting_layout.addWidget(w)
            w.hide()

        self.setLayout(self.setting_layout)


##confirm popup dialog that show and speak the message
class confirmDialog(QDialog):
    def __init__(self, message, parent=None):
        super().__init__(parent)

        self.setWindowTitle("confirm dialog")
        QBtn = (
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        def dialog_helper_menu():
            speak("press enter to confirm. <> or press delete to cancel")

        self.layout = QVBoxLayout()
        message = "confirm " + message
        self.layout.addWidget(QLabel(message))
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

        shortcut_O = QShortcut(QKeySequence("Ctrl+O"), self)
        shortcut_O.activated.connect(dialog_helper_menu)
        shortcut_R = QShortcut(QKeySequence("Ctrl+R"), self)
        shortcut_R.activated.connect(partial(speak, message))
        speak(message)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Backspace or event.key() == Qt.Key.Key_Delete:
            print("cancel clicked")
            speak("Cancel")
            self.reject()


class MainWindow(QMainWindow):
    """
    Merge left and right widget, and act as middle man for communication\n
    Control the application status, implement functionality to left and right widget.\n
    Handle all logic operation
    """

    def show_information_box(self):
        message_box = QMessageBox()
        message_box.setIcon(QMessageBox.Icon.Information)
        message_box.setWindowTitle("Information")
        message_box.setText("This is an information message.")
        message_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        message_box.setFocus()
        message_box.exec()

    ##change the application flow status and re-init / clean the variable
    def change_main_flow_status(self, status):
        print("change status", status)
        match status:
            case Bot_flow_status.setting_status:
                self.getOpponentMoveTimer.stop()
                self.check_game_end_timer.stop()
                self.getScoreTimer.stop()
                self.main_flow_status = Bot_flow_status.setting_status
                self.input_mode = Input_mode.command_mode
                self.rightWidget.commandPanel.setAccessibleDescription(
                    "type the letter 'C' for computer mode, type the letter 'O' for online players mode "
                )
                self.alphabet = ["A", "B", "C", "D", "E", "F", "G", "H"]
                self.number = ["1", "2", "3", "4", "5", "6", "7", "8"]
                self.chessBoard = None
                self.rightWidget.colorBox.setText("Assigned Color: ")
                self.userColor = None
                self.opponentColor = None
                self.rightWidget.right_layout = self.rightWidget.setting_layout
                self.rightWidget.opponentBox.setText("Opponent move: \n")
                for label in self.leftWidget.grids.values():
                    label.deleteLater()
                for w in self.rightWidget.play_menu:
                    w.hide()
                for w in self.rightWidget.setting_menu:
                    w.show()
                self.rightWidget.playWithComputerButton.setFocus()
                self.currentFoucs = 0
                self.leftWidget.grids = dict()

                return
            case Bot_flow_status.board_init_status:
                self.main_flow_status = Bot_flow_status.board_init_status

                self.leftWidget.chessWebView.loadFinished.connect(
                    partial(print, "connect")
                )
                self.leftWidget.chessWebView.loadFinished.disconnect()
                self.getOpponentMoveTimer.stop()
                self.check_game_end_timer.stop()
                self.getScoreTimer.stop()
                self.input_mode = Input_mode.command_mode
                for w in self.rightWidget.setting_menu:
                    w.hide()
                for w in self.rightWidget.play_menu:
                    w.show()
                self.chessBoard = None
                self.userColor = None
                self.opponentColor = None
                self.leftWidget.grids = dict()
                return
            case Bot_flow_status.game_play_status:
                self.check_game_end_timer.start(2000)
                self.rightWidget.commandPanel.setFocus()
                self.currentFoucs = len(self.rightWidget.play_menu)
                self.main_flow_status = Bot_flow_status.game_play_status
                return

    ##initialize a vs computer game for user
    def playWithComputerHandler(self):
        if self.main_flow_status == Bot_flow_status.board_init_status:
            speak("Still " + Speak_template.initialize_game_sentense.value, True)
            return
        if (
            self.main_flow_status == Bot_flow_status.game_play_status
            and not self.game_flow_status == Game_flow_status.game_end
        ):
            speak("Please resign before start a new game", True)
            return
        print("computer mode selected")
        self.change_main_flow_status(Bot_flow_status.board_init_status)
        self.game_play_mode = Game_play_mode.computer_mode
        speak(
            "computer engine mode <>" + Speak_template.initialize_game_sentense.value,
            True,
        )
        self.leftWidget.chessWebView.load(
            QUrl("https://www.chess.com/play/computer/komodo1")
        )

        def clickNCapture():
            self.leftWidget.chessWebView.loadFinished.disconnect()
            if not self.main_flow_status == Bot_flow_status.game_play_status:
                self.capture_screenshot()

        if self.leftWidget.userLoginName != None:
            self.leftWidget.chessWebView.loadFinished.connect(
                partial(
                    self.clickWebButton,
                    [("button", "start"), ("button", "choose"), ("button", "play")],
                    0,
                    clickNCapture,
                    0,
                )
            )
        else:
            self.leftWidget.chessWebView.loadFinished.connect(
                partial(
                    self.clickWebButton,
                    [("button", "start"), ("button", "choose"), ("button", "play")],
                    0,
                    clickNCapture,
                    0,
                )
            )

    ##initialize a vs online player game for user
    def playWithOtherButtonHandler(self):  ###url
        if self.main_flow_status == Bot_flow_status.board_init_status:
            speak("Still " + Speak_template.initialize_game_sentense.value, True)
            return
        if (
            self.main_flow_status == Bot_flow_status.game_play_status
            and not self.game_flow_status == Game_flow_status.game_end
        ):
            speak("Please resign before start a new game", True)
            return
        print("online mode selected")
        self.change_main_flow_status(Bot_flow_status.board_init_status)
        self.game_play_mode = Game_play_mode.online_mode
        speak(
            "online player mode <>" + Speak_template.initialize_game_sentense.value,
            True,
        )
        self.leftWidget.chessWebView.load(QUrl("https://www.chess.com/play/online"))

        def clickNCapture():
            self.leftWidget.chessWebView.loadFinished.disconnect()

            def test(clocks):
                if clocks == None or clocks[0] == clocks[1]:
                    self.leftWidget.checkTime(test)
                else:
                    print("clocks detected :", clocks)
                    if not self.main_flow_status == Bot_flow_status.game_play_status:
                        QTimer.singleShot(3000, self.capture_screenshot)
                        # self.capture_screenshot()

            self.leftWidget.checkTime(test)
            # self.capture_screenshot()

        if self.leftWidget.userLoginName != None:
            print("login name", self.leftWidget.userLoginName)
            self.leftWidget.chessWebView.loadFinished.connect(
                partial(
                    self.clickWebButton,
                    [
                        ("button", "min"),
                        ("button", "More Time Controls"),
                        ("button", "30 min"),
                        ("button", "play"),
                    ],
                    0,
                    clickNCapture,
                    0,
                )
            )
        else:
            print("No login")
            self.leftWidget.chessWebView.loadFinished.connect(
                partial(
                    self.clickWebButton,
                    [
                        ("button", "min"),
                        ("button", "30 min"),
                        ("button", "play"),
                        ("a", "play as a guest"),
                    ],
                    0,
                    clickNCapture,
                    0,
                )
            )

    ##convert move to human readable form
    def move_to_human_form(self, attackerColor, uciString, sanString):
        counter_color = "WHITE" if attackerColor == "BLACK" else "BLACK"
        human_string = attackerColor
        uciString = str(uciString).lower()
        sanString = str(sanString).lower()
        target_square = uciString[:2]
        dest_square = uciString[2:4]

        self.chessBoard.board_object.pop()

        en_passant = self.chessBoard.board_object.has_legal_en_passant()
        target_piece_type = self.chessBoard.check_grid(target_square).__str__().lower()

        dest_piece_type = self.chessBoard.check_grid(dest_square).__str__().lower()

        print(target_piece_type, dest_piece_type)
        # self.chessBoard.moveWithValidate(sanString)
        if sanString.count("x"):
            human_string = (
                human_string
                + " "
                + PIECE_TYPE_CONVERSION[target_piece_type]
                + " captures"
            )
            if en_passant and target_piece_type == "p" and dest_piece_type == None:
                human_string = (
                    human_string + " on " + dest_square.upper() + " en passant"
                )
            else:
                human_string = (
                    human_string
                    + " "
                    + counter_color
                    + " "
                    + PIECE_TYPE_CONVERSION[dest_piece_type]
                    + " on "
                    + dest_square.upper()
                )
        else:
            human_string = (
                human_string
                + " "
                + PIECE_TYPE_CONVERSION[target_piece_type]
                + " moves to "
                + dest_square
            )

        if sanString.count("O-O-O"):
            human_string = human_string + " queenside castling"
        elif sanString.count("O-O"):
            human_string = human_string + " kingside castling"
        elif sanString.count("="):
            human_string = (
                human_string
                + " and promoted to "
                + PIECE_TYPE_CONVERSION[
                    sanString[sanString.index("=") + 1].__str__().lower()
                ]
            )

        if sanString.count("+"):
            human_string = human_string + " and check "
        self.chessBoard.moveWithValidate(sanString)
        print(human_string)
        return human_string

    ##check the score when end game
    def check_score(self):

        def callBack(x):
            if (
                not self.game_flow_status == Game_flow_status.game_end
                or not self.game_play_mode == Game_play_mode.online_mode
            ):
                self.getScoreTimer.stop()
                return
            if not x == None and (x[0] or x[1]):
                speak_string = ""
                print("rating: ", x[0], "league: ", x[1])
                if not x[0] == None:
                    speak_string = speak_string + "rating " + x[0]
                if not x[1] == None:
                    speak_string = speak_string + "league " + x[1]
                self.getScoreTimer.stop()
                speak(speak_string)
            else:
                self.getScoreTimer.start(1000)

        jsCode = """
            function checkScore(){{
                rating = document.querySelectorAll(".rating-score-component")[1]
                league = document.querySelectorAll(".league-score-component")[0]

                if(!rating.textContent){{
                    rating = null 
                }}
                else{{
                    rating = rating.textContent?.trim()
                }}

                if(!league.textContent){{
                    league = null 
                }}
                else{{
                    league = rating.textContent?.trim()
                }}
                return [rating, league]
            }}

            checkScore();
        """
        return self.leftWidget.chessWebView.page().runJavaScript(jsCode, callBack)

    ##click resign button on web view
    def resign_handler(self):
        dlg = confirmDialog("to resign from current game.")
        if dlg.exec():
            self.change_main_flow_status(Bot_flow_status.setting_status)

            def callBack():
                self.game_flow_status = Game_flow_status.game_end
                speak(Speak_template.user_resign.value)
                self.getOpponentMoveTimer.stop()
                self.getScoreTimer.start(1000)
                return

            if (
                self.leftWidget.userLoginName == None
                or self.game_play_mode == Game_play_mode.computer_mode
            ):
                self.clickWebButton(
                    [
                        ("button", "abort"),
                        ("button", "resign"),
                        ("button", "yes", True),
                    ],
                    0,
                    callBack,
                    0,
                )
            else:
                self.clickWebButton(
                    [
                        ("button", "abort"),
                        ("button", "resign"),
                        ("button", "yes", True),
                    ],
                    0,
                    callBack,
                    0,
                )
        else:
            speak("Cancel!")

    ##handle check position query, user input square name or piece type to check the location
    def check_position_handler(self):
        input = self.rightWidget.check_position.text().lower()
        print(any(char.isdigit() for char in input))
        if any(char.isdigit() for char in input):
            grid = input
            piece = self.chessBoard.check_grid(grid).__str__()
            speak_sentence = grid.upper()

            print(piece)
            if not piece == "Invalid square name":
                if not piece == "None":
                    if piece.__str__().islower():
                        speak_sentence = speak_sentence + " BLACK "
                    else:
                        speak_sentence = speak_sentence + " WHITE "
                    speak(
                        speak_sentence + PIECE_TYPE_CONVERSION[piece.__str__().lower()]
                    )
                else:
                    speak(speak_sentence + " empty")
            else:
                speak(speak_sentence)
            self.rightWidget.check_position.clear()
            return
        else:
            piece_type = input
            try:
                piece_type = PIECE_TYPE_CONVERSION[piece_type]
            except Exception as e:
                print(e)
            grid = self.chessBoard.check_piece(piece_type)
            speak_string = ""
            white = grid["WHITE"]
            if len(white) > 0:
                speak_string = (
                    speak_string
                    + len(white).__str__()
                    + " WHITE "
                    + piece_type
                    + white.__str__().upper()
                )
            else:
                speak_string = speak_string + "NO WHITE " + piece_type + "found "

            speak_string = speak_string + " and "
            black = grid["BLACK"]
            if len(white) > 0:
                speak_string = (
                    speak_string
                    + len(black).__str__()
                    + " BLACK "
                    + piece_type
                    + black.__str__().upper()
                )
            else:
                speak_string = speak_string + "NO BLACK " + piece_type + "found "
            speak(speak_string)
            self.rightWidget.check_position.clear()
            return

    ## interpret the input command and perform different task accordingly
    def CommandPanelHandler(self):
        def focus_back():
            if self.input_mode == Input_mode.arrow_mode:
                self.leftWidget.grids[self.currentFoucs].setFocus()
            else:
                self.rightWidget.commandPanel.setFocus()
            return

        input = self.rightWidget.commandPanel.text().lower()

        if input.count("computer") or input == "c":
            self.playWithComputerHandler()
            self.rightWidget.commandPanel.clear()
            return
        elif input.count("online") or input == "o":
            self.playWithOtherButtonHandler()
            self.rightWidget.commandPanel.clear()
            return
        match self.main_flow_status:
            # case Bot_flow_status.setting_status:
            #     if input == "computer":
            #         self.playWithComputerHandler()
            #         self.rightWidget.commandPanel.clear()
            #         return
            #     elif input == "online":
            #         self.playWithOtherButtonHandler()
            #         self.rightWidget.commandPanel.clear()
            #         return
            case Bot_flow_status.board_init_status:
                return
            case Bot_flow_status.game_play_status:
                if input.count("color"):
                    speak("You are playing as {}".format(self.userColor))
                    return
                if input.count("time") or input == "t":
                    if self.game_play_mode == Game_play_mode.online_mode:

                        def timeCallback(clocks):
                            if not clocks == None:
                                user_time = clocks[1].split(":")
                                user = (
                                    user_time[0]
                                    + " minutes "
                                    + user_time[1]
                                    + " seconds"
                                )

                                opponent_time = clocks[0].split(":")
                                opponent = (
                                    opponent_time[0]
                                    + " minutes "
                                    + opponent_time[1]
                                    + " seconds"
                                )
                                speak(
                                    Speak_template.check_time_sentense.value.format(
                                        user, opponent
                                    )
                                )

                        self.leftWidget.checkTime(timeCallback)
                        self.rightWidget.commandPanel.clear()
                        return
                    else:
                        speak("No timer for computer mode")
                        self.rightWidget.commandPanel.clear()
                        return
                if input.count("resign"):
                    self.resign_handler()
                    self.rightWidget.commandPanel.clear()
                    return
                if input.count("where"):
                    piece_type = input.replace("where", "").replace(" ", "")
                    try:
                        piece_type = PIECE_TYPE_CONVERSION[piece_type]
                    except Exception as e:
                        print(e)
                    grid = self.chessBoard.check_piece(piece_type)
                    speak_string = ""
                    white = grid["WHITE"]
                    if len(white) > 0:
                        speak_string = (
                            speak_string
                            + len(white).__str__()
                            + " WHITE "
                            + piece_type
                            + white.__str__().upper()
                        )
                    else:
                        speak_string = speak_string + "NO WHITE " + piece_type

                    speak_string = speak_string + " and "
                    black = grid["BLACK"]
                    if len(white) > 0:
                        speak_string = (
                            speak_string
                            + len(black).__str__()
                            + " BLACK "
                            + piece_type
                            + black.__str__().upper()
                        )
                    else:
                        speak_string = speak_string + "NO BLACK " + piece_type
                    # speak(piece_type + " " + grid.__str__())
                    speak(speak_string)
                    self.rightWidget.commandPanel.clear()
                    return
                elif input.count("what"):
                    grid = input.replace("what", "").replace(" ", "")
                    piece = self.chessBoard.check_grid(grid).__str__()
                    speak_sentence = grid.upper()

                    print(piece)
                    if not piece == "Invalid square name":
                        if not piece == "None":
                            if piece.__str__().islower():
                                speak_sentence = speak_sentence + " BLACK "
                            else:
                                speak_sentence = speak_sentence + " WHITE "
                            speak(
                                speak_sentence
                                + PIECE_TYPE_CONVERSION[piece.__str__().lower()]
                            )
                        else:
                            speak(speak_sentence + " empty")
                    else:
                        speak(speak_sentence)
                    self.rightWidget.commandPanel.clear()
                    return
                if self.game_flow_status == Game_flow_status.user_turn:
                    movePair = self.chessBoard.moveWithValidate(input)
                    # check_win = self.chessBoard.detect_win()

                    print(self.chessBoard.board_object)
                    san_string = ""
                    uci_string = ""
                    human_string = ""
                    if len(movePair) == 2:
                        uci_string = movePair[0]
                        san_string = movePair[1]
                        human_string = self.move_to_human_form(
                            self.userColor, uci_string, san_string
                        )

                        # movePair = movePair[0]

                    if len(uci_string) == 5:
                        target = uci_string[:2]
                        dest = uci_string[2:4]
                        promoteTo = (
                            san_string[san_string.index("=") + 1].__str__().lower()
                        )
                        promote_index = list(PIECE_TYPE_CONVERSION).index(promoteTo)

                        # dlg = confirmMoveDialog("pawn", dest, promote=promoteTo)
                        dlg = confirmDialog(human_string)
                        if dlg.exec():
                            self.all_grids_switch(False)
                            targetWidget = self.leftWidget.grids[target]
                            destWidget = self.leftWidget.grids[dest]
                            if widgetDragDrop(targetWidget, destWidget):
                                match self.userColor:
                                    case "BLACK":
                                        place = str(dest[0]) + str(
                                            int(dest[1]) + promote_index
                                        )
                                    case "WHITE":
                                        place = str(dest[0]) + str(
                                            int(dest[1]) - promote_index
                                        )
                                promoteWidget = self.leftWidget.grids[place]
                                if widgetClick(promoteWidget):
                                    self.rightWidget.commandPanel.clear()
                                    QTimer.singleShot(1000, focus_back)
                                    self.getOpponentMoveTimer.start(1000)
                        else:
                            self.chessBoard.board_object.pop()
                            self.rightWidget.commandPanel.clear()
                            print("Cancel!")

                    elif len(uci_string) == 4:
                        target = uci_string[:2]

                        dest = uci_string[2:4]
                        target_type = PIECE_TYPE_CONVERSION.get(
                            self.chessBoard.check_grid(dest).__str__().lower()
                        )
                        # dlg = confirmMoveDialog(target_type, dest)
                        dlg = confirmDialog(human_string)
                        if dlg.exec():
                            self.all_grids_switch(False)
                            # QTimer.singleShot(3000, partial(self.clickStart,input))
                            # print(self.chessBoard.board_object)

                            targetWidget = self.leftWidget.grids[target]
                            destWidget = self.leftWidget.grids[dest]
                            self.rightWidget.commandPanel.clear()
                            if widgetDragDrop(targetWidget, destWidget):
                                QTimer.singleShot(1000, focus_back)
                                self.getOpponentMoveTimer.start(1000)
                        else:
                            self.chessBoard.board_object.pop()
                            self.rightWidget.commandPanel.clear()
                            print("Cancel!")
                    elif movePair == "Promotion":
                        print("Promotion")
                        speak(
                            "Please indicate the promotion piece by typing the first letter"
                        )
                        self.rightWidget.commandPanel.setFocus()
                    else:
                        speak(input + movePair)
                        print(input + movePair)  ##error move speak
                        self.rightWidget.commandPanel.clear()
                else:
                    speak("Please wait for your opponent's move")

    ##check game end, sync with mirrored chess board and announce opponent's move
    def announceMove(self, sanString):
        print("broadcast move: ", sanString)
        if sanString == None or self.chessBoard == None:
            return False
        crawl_result = None
        check_win = self.chessBoard.detect_win()
        if not check_win == "No win detected.":  ##check user wins
            print(check_win)
            speak(check_win)
            self.game_flow_status = Game_flow_status.game_end
            self.change_main_flow_status(Bot_flow_status.setting_status)
            self.getOpponentMoveTimer.stop()
            self.getScoreTimer.start(1000)
            return True

        match self.opponentColor:
            case "WHITE":
                print("check none ", sanString[0] != None)
                if sanString[0] != None:
                    print(sanString)
                    movePair = self.chessBoard.moveWithValidate(sanString[0])
                    if not len(movePair) == 2:
                        if not crawl_result == None:
                            self.game_flow_status = Game_flow_status.game_end
                            self.change_main_flow_status(Bot_flow_status.setting_status)
                            self.getOpponentMoveTimer.stop()
                            self.getScoreTimer.start(1000)
                            speak(crawl_result, True)
                            return True
                        else:
                            return False
                    uci_string = movePair[0]
                    san_string = movePair[1]

                    print(self.chessBoard.board_object)
                    if len(uci_string) <= 5:
                        human_string = self.move_to_human_form(
                            self.opponentColor, uci_string, san_string
                        )

                        check_win = self.chessBoard.detect_win()
                        print(check_win)
                        print(crawl_result)
                        speak(
                            human_string,
                            importance=True,
                        )
                        self.rightWidget.opponentBox.setText(
                            "Opponent move: \n" + human_string
                        )
                        self.game_flow_status = Game_flow_status.user_turn
                        if not check_win == "No win detected.":
                            speak(check_win, True)
                            self.game_flow_status = Game_flow_status.game_end
                            self.change_main_flow_status(Bot_flow_status.setting_status)
                            self.getOpponentMoveTimer.stop()
                            self.getScoreTimer.start(1000)
                        if not crawl_result == None:
                            self.game_flow_status = Game_flow_status.game_end
                            self.change_main_flow_status(Bot_flow_status.setting_status)
                            self.getOpponentMoveTimer.stop()
                            self.getScoreTimer.start(1000)
                            speak(crawl_result, True)
                        return True
            case "BLACK":
                if sanString and sanString[1] != None:
                    print(sanString)
                    movePair = self.chessBoard.moveWithValidate(sanString[1])
                    if not len(movePair) == 2:
                        if not crawl_result == None:
                            self.game_flow_status = Game_flow_status.game_end
                            self.change_main_flow_status(Bot_flow_status.setting_status)
                            self.getOpponentMoveTimer.stop()
                            self.getScoreTimer.start(1000)
                            speak(crawl_result, True)
                            return True
                        else:
                            return False
                    uci_string = movePair[0]
                    san_string = movePair[1]

                    print(self.chessBoard.board_object)
                    if len(uci_string) <= 5:
                        human_string = self.move_to_human_form(
                            self.opponentColor, uci_string, san_string
                        )
                        # piece = self.chessBoard.check_grid(dest).__str__()
                        check_win = self.chessBoard.detect_win()
                        print(check_win)
                        print(crawl_result)
                        speak(
                            human_string,
                            importance=True,
                        )
                        self.rightWidget.opponentBox.setText(
                            "Opponent move: \n" + human_string
                        )
                        self.game_flow_status = Game_flow_status.user_turn
                        if not check_win == "No win detected.":
                            speak(check_win, True)
                            self.game_flow_status = Game_flow_status.game_end
                            self.change_main_flow_status(Bot_flow_status.setting_status)
                            self.getOpponentMoveTimer.stop()
                            self.getScoreTimer.start(1000)
                        elif not crawl_result == None:
                            self.game_flow_status = Game_flow_status.game_end
                            self.change_main_flow_status(Bot_flow_status.setting_status)
                            self.getOpponentMoveTimer.stop()
                            self.getScoreTimer.start(1000)
                            speak(crawl_result, True)
                        return True

            case _:
                return False

    ##Check whether opponent resigned
    def check_game_end(self):
        def callback(x):
            win_move = None
            win_index = None
            reason = None
            if not x == None:
                for index in range(len(x)):
                    if not x[index] == None and x[index].count("#"):
                        win_move = x[index]
                    if not x[index] == None and x[index].count("1/2-1/2"):
                        reason = "DRAW"
                    if not x[index] == None and x[index].count("1-0"):
                        reason = "WHITE wins"
                    if not x[index] == None and x[index].count("0-1"):
                        reason = "BLACK wins"
                if not reason == None:
                    if win_move == None:
                        if reason == "BLACK wins":
                            reason = "WHITE resigned"
                        elif reason == "WHITE wins":
                            reason = "BLACK resigned"
                        self.game_flow_status = Game_flow_status.game_end
                        self.change_main_flow_status(Bot_flow_status.setting_status)
                        self.getScoreTimer.start(1000)
                        self.getOpponentMoveTimer.stop()
                        speak(reason)
                    else:
                        self.announceMove((win_move, win_move))

        jsCode = """
            function childImg(move){{
                let sanString = '';
                if(!move)
                    return null
                for (let i of move?.childNodes){{
                    sanString+=i?.textContent || i?.getAttribute('data-figurine')
                }}    
                return sanString
            }}
            function getOpponentMove() {{
                let moves = document.querySelectorAll('{0}');
                let move = moves[moves.length-1]
                if(move?.querySelector('[class*=result]')){{
                    LastMove = moves[moves.length-1]
                    if (moves.length != 1){{
                        move = moves[moves.length-2]
                    }}
                    move = move.querySelectorAll('[class~=node]')
                    return [LastMove?.querySelector('[class*=white]')?.outerText,LastMove?.querySelector('[class*=black]')?.outerText,childImg(move[0]),childImg(move[1])]
                }}
                move = move.querySelectorAll('[class~=node]')
                return [childImg(move[0]),childImg(move[1])]
            }}
            getOpponentMove();
            """.format(
            ".move"
        )
        self.leftWidget.chessWebView.page().runJavaScript(jsCode, callback)

    ##JS to get opponent move SAN
    def getOpponentMove(self):
        if self.input_mode == Input_mode.arrow_mode:
            self.all_grids_switch(True)

        self.game_flow_status = Game_flow_status.opponent_turn

        def callback(x):
            if self.announceMove(x):
                self.getOpponentMoveTimer.stop()
            else:
                self.getOpponentMoveTimer.start(1000)

        jsCode = """
            function childImg(move){{
                let sanString = '';
                if(!move)
                    return null
                for (let i of move?.childNodes){{
                    sanString+=i?.textContent || i?.getAttribute('data-figurine')
                }}    
                return sanString
            }}
            function getOpponentMove() {{
                let moves = document.querySelectorAll('{0}');
                let move = moves[moves.length-1]
                if(move?.querySelector('[class*=result]')){{
                    LastMove = moves[moves.length-1]
                    if (moves.length != 1){{
                        move = moves[moves.length-2]
                    }}
                    move = move.querySelectorAll('[class~=node]')
                    return [childImg(LastMove?.querySelector('[class*=white]')),childImg(LastMove?.querySelector('[class*=black]')),childImg(move[0]),childImg(move[1])]
                }}
                move = move.querySelectorAll('[class~=node]')
                return [childImg(move[0]),childImg(move[1])]
            }}
            getOpponentMove();
            """.format(
            ".move"
        )
        self.leftWidget.chessWebView.page().runJavaScript(jsCode, callback)

    ##JS to click on web view button
    def clickWebButton(
        self, displayTextList, index, finalCallback, retry
    ):  ##avoid double load finish
        if index >= len(displayTextList):
            print("click finished")
            # QTimer.singleShot(1000, finalCallback)
            finalCallback()
            # self.capture_screens
            # hot()
            return True

        def next_click(result):
            if result == displayTextList[index][1].lower() or retry >= 6:
                QTimer.singleShot(
                    1000,
                    partial(
                        self.clickWebButton,
                        displayTextList,
                        index + 1,
                        finalCallback,
                        0,
                    ),
                )
            else:
                ## retry
                add = retry + 1
                QTimer.singleShot(
                    500,
                    partial(
                        self.clickWebButton, displayTextList, index, finalCallback, add
                    ),
                )

        # print(displayTextList[index][0], displayTextList[index][1].lower())
        if len(displayTextList[index]) == 3:
            jsCode = """
            function out() {{
                let buts = document.querySelectorAll('{0}');
                for(but of buts){{
                    if(but?.textContent?.trim()?.toLowerCase()=='{1}'||but?.innerText?.trim()?.toLowerCase() == '{1}'){{
                        but.click();
                        console.error(but?.textContent)
                        console.error("**********************************")
                        console.error('{1}')
                        console.error("**********************************")
                        return '{1}';
                    }}
                }}
                return false;
            }}
            out();
            """.format(
                displayTextList[index][0], displayTextList[index][1].lower()
            )
        else:
            jsCode = """
                function out() {{
                    let buts = document.querySelectorAll('{0}');
                    for(but of buts){{
                        if(but?.textContent?.trim()?.toLowerCase().includes('{1}')||but?.innerText?.trim()?.toLowerCase().includes('{1}')){{
                            but.click();
                            console.error(but?.textContent)
                            console.error("**********************************")
                            console.error('{1}')
                            console.error("**********************************")
                            return '{1}';
                        }}
                    }}
                    return false;
                }}
                out();
                """.format(
                displayTextList[index][0], displayTextList[index][1].lower()
            )
        return self.leftWidget.chessWebView.page().runJavaScript(jsCode, next_click)

    ##assign square after detect the web view chessboard and color
    def getBoard(self):
        for row in range(8):
            for col in range(8):
                self.leftWidget.grids[self.alphabet[col] + self.number[row]] = (
                    self.leftWidget.grids.pop(row.__str__() + col.__str__())
                )
                self.leftWidget.grids[
                    self.alphabet[col] + self.number[row]
                ].setAccessibleName(self.alphabet[col] + self.number[row])

        self.chessBoard = ChessBoard()
        self.change_main_flow_status(Bot_flow_status.game_play_status)

    ##toggle the marked square layer -> hide before perfrom click
    def all_grids_switch(self, on_off):
        for grid in self.leftWidget.grids.values():
            if on_off:
                grid.show()
            else:
                grid.hide()

    ##computer vision to detect the chessboard
    def capture_screenshot(self, retry=3):
        if retry <= 0:
            speak("board detection error, retry initialize", True)
            if self.game_play_mode == Game_play_mode.computer_mode:
                self.playWithComputerHandler()
            else:
                self.playWithOtherButtonHandler()
            return

        try:
            file_path = os.path.join(current_dir, "Tmp", "board_screenshot.png")
            # file_path = "./widget_screenshot.png"
            screenshot = self.leftWidget.chessWebView.grab()
            screenshot.save(file_path)
            print("cap here")
            viewWidth = self.leftWidget.chessWebView.width()
            viewHeight = self.leftWidget.chessWebView.height()
            x, y, w, h = detectChessboard(file_path, viewWidth, viewHeight)
        except Exception as e:
            print("error retry", e)
            retry = retry - 1
            QTimer.singleShot(2000, partial(self.capture_screenshot, retry))
            return

        x = int(x)
        y = int(y)
        w = int((w / 8))
        h = int((h / 8))
        print(x, y, w, h)

        for row in range(8):
            for col in range(8):
                label = QLabel(self.leftWidget)
                label.setGeometry(x + col * w, y + row * h, w, h)
                # if (row + col) % 2 == 0:
                #     label.setStyleSheet("background-color: rgba(0, 0, 255, 100);")
                # else:
                #     label.setStyleSheet("background-color: rgba(255, 0, 0, 100);")
                self.leftWidget.grids[row.__str__() + col.__str__()] = label
                label.show()
                # label.hide()  # comment this to check whether the board detect success

        user_rook_file = os.path.join(current_dir, "Tmp", "color_detection_user.png")

        user_rook = self.leftWidget.grids["77"]

        self.leftWidget.chessWebView.grab(
            QRect(user_rook.x(), user_rook.y(), w, h)
        ).save(user_rook_file)

        color = userColor(user_rook_file)
        self.userColor = color
        self.rightWidget.colorBox.setText("Assigned Color: " + color)
        if color == "BLACK":
            self.opponentColor = "WHITE"
            self.alphabet.reverse()
            speak(Speak_template.user_black_side_sentense.value)
            self.game_flow_status = Game_flow_status.opponent_turn
            self.getOpponentMoveTimer.start(1000)
        else:
            self.opponentColor = "BLACK"
            self.number.reverse()
            speak(Speak_template.user_white_side_sentense.value)
            self.game_flow_status = Game_flow_status.user_turn

        self.getBoard()

    ##switch to command mode
    def switch_command_mode(self):
        print("shortcut ctrl + F pressed")
        speak("command mode <> you can type your move here")
        self.arrow_mode_switch(False)
        self.input_mode = Input_mode.command_mode
        self.currentFoucs = len(self.rightWidget.play_menu)
        self.rightWidget.commandPanel.setFocus()

    ##switch to arrow mode, only allowd when game started
    def switch_arrow_mode(self):
        print("shortcut ctrl + J pressed")
        if self.main_flow_status == Bot_flow_status.game_play_status:

            speak("arrow_mode")
            self.input_mode = Input_mode.arrow_mode
            self.arrow_mode_switch(True)
            self.all_grids_switch(True)
            self.rightWidget.commandPanel.clear()

            self.leftWidget.setStyleSheet(
                "QLabel:focus { border: 5px solid rgba(255, 0, 0, 1); }"
            )
            init_focus = self.alphabet[0].__str__() + self.number[-1].__str__()
            self.leftWidget.grids[init_focus].setFocus()
            self.currentFoucs = init_focus

    ##arrow key move and speak the square information
    def handle_arrow(self, direction):
        if not self.main_flow_status == Bot_flow_status.game_play_status:
            return
        file = self.currentFoucs[0]
        rank = self.currentFoucs[1]

        alphabet_index = self.alphabet.index(file)
        number_index = self.number.index(rank)
        # print(self.currentFoucs, direction)
        match direction:
            case "UP":
                num = max(number_index - 1, 0)
                self.leftWidget.grids[file + self.number[num]].setFocus()
                self.currentFoucs = file + self.number[num]
            case "DOWN":
                num = min(number_index + 1, 7)
                self.leftWidget.grids[file + self.number[num]].setFocus()
                self.currentFoucs = file + self.number[num]
            case "LEFT":
                alp = max(alphabet_index - 1, 0)
                self.leftWidget.grids[self.alphabet[alp] + rank].setFocus()
                self.currentFoucs = self.alphabet[alp] + rank
            case "RIGHT":
                alp = min(alphabet_index + 1, 7)
                self.leftWidget.grids[self.alphabet[alp] + rank].setFocus()
                self.currentFoucs = self.alphabet[alp] + rank
        # QLabel.setAccessibleDescription("HELLO")
        # QLabel.setAccessibleName("Name")
        piece = self.chessBoard.check_grid(self.currentFoucs).__str__()
        if piece == "None":
            speak("{0}".format(self.currentFoucs.upper()))
            return
        else:
            color = "white" if piece.isupper() else "black"
            piece_square_text = "{0} {1} {2}".format(
                self.currentFoucs.upper(),
                color,
                PIECE_TYPE_CONVERSION.get(piece.lower()),
            )
            print(piece_square_text)
            speak(piece_square_text)
            self.leftWidget.grids[self.currentFoucs].setAccessibleDescription(
                piece_square_text
            )

    ##select the piece under arrow mode
    def handle_space(self):
        if not self.input_mode == Input_mode.arrow_mode:
            return
        if len(self.rightWidget.commandPanel.text()) == 4:
            self.CommandPanelHandler()
            return
        if not self.currentFoucs == None:
            piece = self.chessBoard.check_grid(self.currentFoucs).__str__()
            if not piece == "None":
                color = "white" if piece.isupper() else "black"
                piece = PIECE_TYPE_CONVERSION.get(piece.lower())
                speak(color + " " + piece + " selected")

        current_value = self.rightWidget.commandPanel.text()
        self.rightWidget.commandPanel.setText(current_value + self.currentFoucs)
        if len(self.rightWidget.commandPanel.text()) == 4:
            self.CommandPanelHandler()

    ##clear the selected piece under arrow mode
    def handle_arrow_delete(self):
        if not self.input_mode == Input_mode.arrow_mode:
            return
        self.rightWidget.commandPanel.setText("")

    ##control tab event on right widget
    def handle_tab(self):
        print("tab")
        if self.input_mode == Input_mode.command_mode:
            unhidden_widgets = []
            layout = self.rightWidget.layout()
            for i in range(layout.count()):
                widget = layout.itemAt(i).widget()
                if widget and not widget.isHidden():
                    unhidden_widgets.append(widget)
            if int(self.currentFoucs + 1) >= len(unhidden_widgets):
                unhidden_widgets[0].setFocus()
                self.currentFoucs = 0
            else:
                unhidden_widgets[self.currentFoucs + 1].setFocus()
                self.currentFoucs = self.currentFoucs + 1

            intro = unhidden_widgets[self.currentFoucs].text()
            if intro == "":
                intro = unhidden_widgets[self.currentFoucs].accessibleDescription()
            speak(intro)
        else:
            self.leftWidget.grids[self.currentFoucs].setFocus()

    ##switch to arrow mode
    def arrow_mode_switch(self, on_off):
        arrows = ["UP", "DOWN", "LEFT", "RIGHT", "SPACE", "DELETE"]
        for arrow in arrows:
            self.all_shortcut.get(arrow).setEnabled(on_off)

    ##repeat the previous sentence
    def repeat_previous(self):
        speak(previous_sentence)

    ##tell user different options based on the application status
    def helper_menu(self):
        print("helper")
        match self.main_flow_status:
            case Bot_flow_status.setting_status:
                speak(Speak_template.setting_state_help_message.value)
                return
            case Bot_flow_status.board_init_status:
                speak(Speak_template.init_state_help_message.value)
                return
            case Bot_flow_status.game_play_status:
                if self.input_mode == Input_mode.command_mode:
                    sentence = Speak_template.command_panel_help_message.value
                    # if self.game_play_mode == Game_play_mode.online_mode:
                    #     sentence = (
                    #         + Speak_template.command_panel_help_message.value
                    #     )

                    speak(sentence)
                elif self.input_mode == Input_mode.arrow_mode:
                    speak(
                        Speak_template.arrow_mode_help_message.value
                        + "or press control F for command mode"
                    )

    def __init__(self, *args, **kwargs):
        global previous_sentence
        self.alphabet = ["A", "B", "C", "D", "E", "F", "G", "H"]
        self.number = ["1", "2", "3", "4", "5", "6", "7", "8"]
        super(MainWindow, self).__init__(*args, **kwargs)

        shortcut_F = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut_F.activated.connect(self.switch_command_mode)

        shortcut_J = QShortcut(QKeySequence("Ctrl+J"), self)
        shortcut_J.activated.connect(self.switch_arrow_mode)

        shortcut_UP = QShortcut(QKeySequence(Qt.Key.Key_Up), self)
        shortcut_UP.activated.connect(partial(self.handle_arrow, "UP"))

        shortcut_DOWN = QShortcut(QKeySequence(Qt.Key.Key_Down), self)
        shortcut_DOWN.activated.connect(partial(self.handle_arrow, "DOWN"))

        shortcut_LEFT = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        shortcut_LEFT.activated.connect(partial(self.handle_arrow, "LEFT"))

        shortcut_RIGHT = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        shortcut_RIGHT.activated.connect(partial(self.handle_arrow, "RIGHT"))

        shortcut_SPACE = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        shortcut_SPACE.activated.connect(self.handle_space)

        shortcut_DELETE = QShortcut(QKeySequence(Qt.Key.Key_Backspace), self)
        shortcut_DELETE.activated.connect(self.handle_arrow_delete)

        shortcut_TAB = QShortcut(QKeySequence(Qt.Key.Key_Tab), self)
        shortcut_TAB.activated.connect(self.handle_tab)

        shortcut_F1 = QShortcut(QKeySequence("Ctrl+1"), self)
        shortcut_F1.activated.connect(self.playWithComputerHandler)

        shortcut_F2 = QShortcut(QKeySequence("Ctrl+2"), self)
        shortcut_F2.activated.connect(self.playWithOtherButtonHandler)

        shortcut_R = QShortcut(QKeySequence("Ctrl+R"), self)
        shortcut_R.activated.connect(self.repeat_previous)

        shortcut_O = QShortcut(QKeySequence("Ctrl+O"), self)
        shortcut_O.activated.connect(self.helper_menu)
        self.all_shortcut = {
            "F": shortcut_F,
            "J": shortcut_J,
            "UP": shortcut_UP,
            "DOWN": shortcut_DOWN,
            "LEFT": shortcut_LEFT,
            "RIGHT": shortcut_RIGHT,
            "SPACE": shortcut_SPACE,
            "DELETE": shortcut_DELETE,
        }

        self.arrow_mode_switch(False)
        ##initialize flow status
        self.main_flow_status = Bot_flow_status.setting_status
        self.game_flow_status = Game_flow_status.not_start
        self.input_mode = Input_mode.command_mode
        self.game_play_mode = None

        ##initialize UI components
        self.mainWidget = QWidget()
        self.leftWidget = LeftWidget()
        self.rightWidget = RightWidget()

        def timeCallback(clocks):
            if not clocks == None:
                user_time = clocks[1].split(":")
                user = user_time[0] + " minutes " + user_time[1] + " seconds"

                opponent_time = clocks[0].split(":")
                opponent = (
                    opponent_time[0] + " minutes " + opponent_time[1] + " seconds"
                )
                speak(Speak_template.check_time_sentense.value.format(user, opponent))

        self.rightWidget.check_time.clicked.connect(
            partial(self.leftWidget.checkTime, timeCallback)
        )
        self.rightWidget.playWithComputerButton.clicked.connect(
            self.playWithComputerHandler
        )
        self.rightWidget.playWithOtherButton.clicked.connect(
            self.playWithOtherButtonHandler
        )

        self.rightWidget.resign.clicked.connect(self.resign_handler)

        self.rightWidget.commandPanel.returnPressed.connect(self.CommandPanelHandler)
        self.rightWidget.check_position.returnPressed.connect(
            self.check_position_handler
        )

        self.leftWidget.chessWebView.loadFinished.connect(self.leftWidget.checkLogined)

        self.leftWidget.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.getScoreTimer = QTimer()
        self.getScoreTimer.timeout.connect(self.check_score)

        self.getOpponentMoveTimer = QTimer()
        self.getOpponentMoveTimer.timeout.connect(self.getOpponentMove)

        self.check_game_end_timer = QTimer()
        self.check_game_end_timer.timeout.connect(self.check_game_end)

        mainLayout = QHBoxLayout()
        mainLayout.addWidget(self.leftWidget)
        mainLayout.addWidget(self.rightWidget)
        self.mainWidget.setLayout(mainLayout)
        self.setCentralWidget(self.mainWidget)

        self.chessBoard = None
        self.userColor = None
        self.opponentColor = None
        ##need to modify /Users/longlong/miniforge3/envs/fyp/lib/python3.12/site-packages/pyttsx3/drivers/nsss.py
        ## import objc and self.super
        self.rightWidget.playWithComputerButton.setFocus()
        self.currentFoucs = 0
        # self.show_information_box()


def speak(sentence, importance=False, dialog=False):
    global previous_sentence
    global internal_speak_engine

    previous_sentence = sentence
    if internal_speak_engine:
        speak_thread.queue.put((sentence, importance))
    else:
        print("no speak engine")


if __name__ == "__main__":
    global speak_thread
    global current_dir
    global previous_sentence
    previous_sentence = ""

    speak_thread = TTSThread()
    # speak_thread.start()
    current_dir = os.path.dirname(os.path.realpath(__file__))

    app = QApplication(sys.argv)
    app.setApplicationName("Chess Bot")

    window = MainWindow()

    global internal_speak_engine
    internal_speak_engine = window.rightWidget.screen_reader_checkBox.isChecked()

    icon = QIcon(os.path.join(current_dir, "Resource", "Logo", "chessBot_logo.png"))
    window.setWindowIcon(icon)

    window.show()

    def welcome_callback():
        speak(
            Speak_template.welcome_sentense.value
            + Speak_template.game_intro_sentense.value,
            True,
        )
        window.leftWidget.chessWebView.loadFinished.disconnect()

    window.leftWidget.chessWebView.loadFinished.connect(welcome_callback)

    window.move(10, 10)
    # window.switch_arrow_mode()
    sys.exit(app.exec())
