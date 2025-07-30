# Gomoku-AI-Game

This project is a visually enhanced Gomoku game built with Python and Tkinter. It supports human vs AI gameplay, advanced game features, and a polished GUI inspired by modern game design.


## Game Features
- Classic Gomoku 5-in-a-row rule
- Tournament mode: 3 rounds with increasing board sizes (5x5, 8x8, 10x10)
- Unique power-ups:
  - 🚫 Block (3 per match)
  - 💣 Bomb (clears row/col/diagonal)
  - ✌️ Double move
- Beautiful animated GUI using emojis and gradients
- Highlighted win effects and score tracking
- Minimax AI with alpha-beta pruning

##  AI Algorithm
We implemented a Minimax algorithm with alpha-beta pruning. The AI evaluates positions based on open-ended sequences and blocks threats, using:
- Custom evaluation function
- Simulated move tree of depth 2
- Special moves like bomb and block used strategically

##  Technologies
- Python 3
- Tkinter
- PIL (Pillow) for graphics
- Emoji-based interaction

