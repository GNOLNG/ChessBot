import chess
import chess.variant

name_conversion = {
    "queen": "q",
    "knight": "n",
    "rook": "r",
    "bishop": "b",
    "pawn": "p",
    "king": "k",
}


## a mirrored chessboard that sync with actual web view chessboard
class ChessBoard:
    def __init__(self):
        self.board_object = chess.Board()
        print(self.board_object)
        print()

    def moveByUCI(self, uciString):
        """
        This function make move by using UCI string [target, destination]\n
        Parameters :
            - uciString

        Returns:
            success:
                -turple(true, Board object)
            fails:
                -turple(false, Error type)
        """
        try:
            move = chess.Move.from_uci(uciString)
            sanString = self.board_object.san(move)
            self.board_object.push_uci(uciString)
            print("UCI move: ", uciString, sanString)
            return (uciString.upper(), sanString.upper())
        except Exception as e:
            return e

    def moveBySan(self, sanString):
        """
        This function make move by using SAN string\n
        Parameters :
            - sanString

        Returns:
            success:
                -turple(true, Board object)
            fails:
                -turple(false, Error type)
        """
        try:
            if sanString == "oo" or sanString == "00":
                sanString = "O-O"
            elif sanString == "ooo" or sanString == "000":
                sanString = "O-O-O"

            uciString = self.board_object.parse_san(sanString).uci()

            move = chess.Move.from_uci(uciString)
            standard_san_string = self.board_object.san(move)

            self.board_object.push_san(standard_san_string)
            print("SAN move", uciString, standard_san_string)
            return (uciString.upper(), standard_san_string.upper())
        except Exception as e:
            return e

    def moveWithValidate(self, moveString):
        ## make move first -> user confirm = no change -> user cancel = back
        moveString = "".join(filter(str.isalnum, moveString))
        moveString = moveString.replace(" ", "").replace("null", "").lower()

        ##check coordinate notation
        uciTrial = self.moveByUCI(moveString)
        print("uci Trial trial: ", moveString, " ", uciTrial)
        if not isinstance(uciTrial, Exception):
            return uciTrial
        elif isinstance(uciTrial, chess.IllegalMoveError):
            print(self.check_grid(moveString[:2]).__str__().lower())
            if (
                moveString.endswith("8") or moveString.endswith("1")
            ) and self.check_grid(moveString[:2]).__str__().lower() == "p":
                return "Promotion"
            return "Illegal move"

        ##check SAN
        sanTrial = self.moveBySan(moveString)
        print("San Trial trial: ", moveString, " ", sanTrial)
        if not isinstance(sanTrial, Exception):
            return sanTrial

        ##check SAN with capitalized
        capSanTrial = self.moveBySan(moveString.capitalize())
        print("cap San Trial trial: ", moveString, " ", capSanTrial)
        if not isinstance(capSanTrial, Exception):
            return capSanTrial
        elif isinstance(capSanTrial, chess.IllegalMoveError):
            return "Illegal move"

        return "Invalid move"

    ##check piece type by square name
    def check_grid(self, grid):
        grid = grid.lower()
        try:
            piece = self.board_object.piece_at(chess.SQUARE_NAMES.index(grid))
        except Exception as e:
            return "Invalid square name"
        return piece

    ##check the locations by piece type
    def check_piece(self, piece):
        target_piece = piece.lower()
        if len(piece) > 1:
            target_piece = name_conversion.get(piece.lower())
        white_list = []
        black_list = []
        for square in chess.SQUARE_NAMES:
            result_piece = self.check_grid(square)
            if (
                not result_piece == None
                and result_piece.symbol().lower() == target_piece
            ):
                if result_piece.symbol().islower():
                    black_list.append(square)
                else:
                    white_list.append(square)

        return {"WHITE": white_list, "BLACK": black_list}

    ##detect whether game end
    def detect_win(self):
        if self.board_object.is_checkmate():
            if self.board_object.turn:
                return "Black wins by checkmate!"
            else:
                return "White wins by checkmate!"
        elif self.board_object.is_stalemate():
            return "Stalemate!"
        elif self.board_object.is_insufficient_material():
            return "Insufficient material!"
        else:
            return "No win detected."


chessboard_in = ChessBoard()
