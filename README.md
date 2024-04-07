# chess.com-bot-for-visually-impaired
This project addresses the lack of support for visually impaired users on chess.com by introducing a keyboard-operated bot. The bot enables players to navigate the board and make moves using arrow keys and keyboard input, while also announcing the opponent's moves audibly.


## Downlaod
**1. Download zip file**
- **Windows:** https://github.com/GNOLNG/chess.com-bot-for-visually-impaired/releases/download/v1/windows_ChessBot.zip

- **Mac:** https://github.com/GNOLNG/chess.com-bot-for-visually-impaired/releases/download/v1/mac_ChessBot.zip

**2. Unzip**
**3. Grant permission to the app**
- **Windows users:** click run when security warning pop up or Windows Security > Virus & threat protection > allowed thread > select "ChessBot" to allow it
- **Mac users:** Mac user: choose Apple menu  > System Settings > click Privacy & Security   > Accessibility > turn on the” ChessBot”

**4.Open the app**

**5.Login chess.com account if you want to earn score from chess.com rating system**
- With the assistance of a trusted friend: open the "ChessBot" > locate and click the login button on left bottom of the front page > login your chess.com account
<img width="649" alt="image" src="https://github.com/GNOLNG/chess.com-bot-for-visually-impaired/assets/92449126/38b80310-dc7d-423b-9cf6-fb9a3d8136dc">


## How to use
***Only two key to remember***
  - **1. Press Control + O, and the bot will tell options that you can make on that state. So, press Control + O when you get lost.**
  - **2. Press Control + R to repeat the last sentence.**
---
***Start a chess game***
  - **1. Control + 1 OR type the word 'computer' to start a "vs computer" game**  
  - **2. Control + 2 OR type the word 'online' to start a "vs online players" game**
  - **3. Once the game is ready, the bot will tell the color you are playing**  
<img width="389" alt="image" src="https://github.com/GNOLNG/chess.com-bot-for-visually-impaired/assets/92449126/acd76669-f48f-4fe3-a820-00cd84212baf">

---

***Make a move***

  There are two modes supported to make a move: command mode and arrow mode

  - **For command mode: Control + F to focus on command panel.  Coordinate-based (UCI) style and Standard algebraic notation (SAN) style**  
    - **1. For SAN style:**

| SAN text            | Example meaning |
| ----------------- | ----------- |
| Nxe4 | knight capture on e4 |
| Rd1+ | rook move to d1 and check |
| qe7# | queen move to e7 and checkmate |
| o-o /0-0 | kingside castling (short castling) |
| o-o-o/ 0-0-0 | queenside castling (long castling) |
| e8=q | pawn move to e8 and promote to queen |

  - **2. For UCI style:**

| coordinate notation text            | Example meaning |
| ----------------- | ----------- |
| e2e4 | move piece on e2 to e4 |
| e7e8q | move piece on e7 (pawn) to e8 and promote to queen |

  - **3. After inputting a move, a confirm dialog shows up. Press enter or the space bar to confirm. Or press delete to cancel.** 

- **For arrow mode: Control + J to enter arrow mode**
  - **Use the arrow key to travel the chess board**
  - **Meanwhile, the bot will tell you the piece on that square.**
  - **Press space bar to select the target piece, travel to the square you wanted to place, and press the space bar again**
---

***Opponent Move***
  - **1. after your opponent makes their move, the bot will speak out their move**
  - For example, white pawn move to h8 and promote to queen and check
---
***Query information***
  - **1. Type the word "time" to check the remaining time of the current game**
  - **2. Type the word "where" followed by piece type to check the location of that piece, e.g. where knight / where k**
  - **3. Type the word "what" followed by the square name to check the piece type on that square, e.g. what a2**

---
***Game end***
  - **The game will end once either side wins or resigns from the chess game. The bot will tell you who wins and the reason, e.g. black wins by cheakmate**
  - **You must resign from the current game before starting another game**
  - **To resign, type the word "resign" and confirm it.**

## FAQ

#### Question: Why do I need to grant permission to use this software?

Answer: The chess bot will move the piece based on your input by controlling your mouse cursor, so please avoid moving your cursor after you confirm your move.

#### Question: Can I make pre-moves (move a piece before my opponent finishes their move)?

Answer: No, the current version of the application does not support pre-moves. You must wait for your opponent to complete their move before making your own.

#### Question: Do I need to log in to my Chess.com account every time I open the application?

Answer: No, you don't need to log in to your account again each time you open the application. Your account information will persist, and you will be automatically logged in when you open the application.

## Source Code

**Coming Soon**


