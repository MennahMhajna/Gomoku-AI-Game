import tkinter as tk
from tkinter import messagebox
import copy
import threading
import random
import sys
import os
from PIL import Image, ImageTk, ImageDraw, ImageFilter

try:
    import winsound
    def play_click_sound():
        winsound.MessageBeep()
except ImportError:
    import platform
    if platform.system() == 'Darwin':
        def play_click_sound():
            os.system('afplay /System/Library/Sounds/Glass.aiff &')
    else:
        def play_click_sound():
            pass

PLAYER_SYMBOLS = ['⚫', '⚪']
WIN_LENGTH = 5
AI_DEPTH = 2
AI_DELAY = 0.3
BLOCK_SYMBOL = '🚫'
MAX_BLOCKS = 3
WIN_POINTS = 3
TIE_POINTS = 1
LOSS_POINTS = 0
MAX_ROUNDS = 3

X_COLOR = '#1976D2'
O_COLOR = '#D32F2F'
BLOCK_COLOR = '#222222'
WIN_COLOR = '#FFD600'
BOMB_FLASH_COLOR = '#BDBDBD'
DEFAULT_BG = '#C172F5'  # Bright purple from bottom of board gradient (193, 114, 245)

CELL_SIZE = 60
BOARD_PADDING = 32
GRID_RADIUS = 24

class GomokuApp:
    """מחלקה ראשית לאפליקציית המשחק - מנהלת את דף הפתיחה"""
    
    def __init__(self, root):
        """אתחול האפליקציה הראשית - יצירת חלון וצגת דף הפתיחה"""
        self.root = root
        # --- רקע גרדיאנט על כל החלון ---
        self.bg_canvas = tk.Canvas(root, width=1100, height=800, highlightthickness=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.draw_gradient(self.bg_canvas, '#3A4ED0', '#7B2FF7', 1100, 800)
        # ---
        self.show_start_page()

    def show_start_page(self):
        """יצירת דף הפתיחה עם הוראות המשחק וכפתור התחלה"""
        try:
            bg_img = Image.open('background.png').resize((self.root.winfo_screenwidth(), self.root.winfo_screenheight()))
        except Exception:
            print('background.png not found, using solid color background.')
            bg_img = Image.new('RGB', (self.root.winfo_screenwidth(), self.root.winfo_screenheight()), '#5DADE2')
        self.bg_photo = ImageTk.PhotoImage(bg_img)
        self.bg_label = tk.Label(self.root, image=self.bg_photo)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        
        card_width, card_height = 750, 450
        card_canvas = tk.Canvas(self.root, width=card_width, height=card_height, highlightthickness=0, bd=0, bg='#FFFFFF')
        card_canvas.place(relx=0.5, rely=0.5, anchor='center')
        
        card_img = Image.new('RGBA', (card_width, card_height), (255,255,255,0))
        draw = ImageDraw.Draw(card_img)
        radius = 40
        fill = (255,255,255,230)
        draw.rounded_rectangle([0,0,card_width,card_height], radius, fill=fill)
        card_img_tk = ImageTk.PhotoImage(card_img)
        card_canvas.create_image(0, 0, anchor='nw', image=card_img_tk)
        card_canvas.image = card_img_tk
        
        card_frame = tk.Frame(card_canvas, width=card_width, height=card_height, bg='#FFFFFF')
        card_canvas.create_window(card_width//2, card_height//2, window=card_frame, anchor='center')
        
        title = tk.Label(card_frame, text="🎯 Gomoku – The Game", font=("Arial Black", 28), fg='#00AEEF', bg='#FFFFFF', pady=10)
        title.pack(pady=(30, 0))
        underline = tk.Frame(card_frame, bg='#00AEEF', height=3, width=card_width//2)
        underline.pack(pady=(0, 18))
        
        instructions = [
            ("🔴🔵", "Create 5 in a row to win."),
            ("🚫", "Each player can block 3 cells in all rounds"),
            ("💣", "Each player can use a bomb once in all rounds"),
            ("✌️", "Each player can play double move once in all rounds"),
            ("⏳", "Winner is best of 3 rounds.")
        ]
        instr_frame = tk.Frame(card_frame, bg='#FFFFFF')
        instr_frame.pack(pady=(0, 30))
        for emoji, text in instructions:
            row = tk.Frame(instr_frame, bg='#FFFFFF')
            row.pack(anchor='w', pady=4)
            tk.Label(row, text=emoji, font=("Arial", 18), bg='#FFFFFF', fg='#222').pack(side='left', padx=(0,8))
            tk.Label(row, text=text, font=("Arial", 16), bg='#FFFFFF', fg='#222').pack(side='left')
        
        btn_w, btn_h = 320, 56
        self.start_btn_canvas = tk.Canvas(card_frame, width=btn_w, height=btn_h, highlightthickness=0, bg='#FFFFFF')
        self.start_btn_canvas.pack(pady=30)
        self.start_btn_canvas.create_rectangle(2, 2, btn_w-2, btn_h-2, fill='#1976D2', outline='#1565C0', width=3, tags='rect')
        self.start_btn_canvas.create_text(btn_w//2, btn_h//2, text='▶ Start Game', font=("Arial", 20, "bold"), fill='white', tags='text')
        
        def on_enter(e):
            self.start_btn_canvas.itemconfig('rect', fill='#1565C0')
        def on_leave(e):
            self.start_btn_canvas.itemconfig('rect', fill='#1976D2')
        def on_click(e):
            self.start_game_animated()
        self.start_btn_canvas.bind('<Enter>', on_enter)
        self.start_btn_canvas.bind('<Leave>', on_leave)
        self.start_btn_canvas.bind('<Button-1>', on_click)
        
        self._card_canvas = card_canvas
        self._card_img_tk = card_img_tk
        self._btn_canvas = None

    def start_game_animated(self):
        """התחלת משחק עם אנימציה - מעבר לדף המשחק"""
        self.root.after(100, self._delayed_start)

    def _delayed_start(self):
        """פונקציה פנימית - מחיקת דף הפתיחה ויצירת משחק חדש"""
        for widget in self.root.winfo_children():
            try:
                widget.destroy()
            except:
                pass
        self.game = GomokuGUI(self.root)

    def draw_gradient(self, canvas, color1, color2, width, height):
        """יצירת רקע גרדיאנט על canvas נתון"""
        r1, g1, b1 = self.root.winfo_rgb(color1)
        r2, g2, b2 = self.root.winfo_rgb(color2)
        r_ratio = (r2 - r1) / height
        g_ratio = (g2 - g1) / height
        b_ratio = (b2 - b1) / height
        for i in range(height):
            nr = int(r1 + (r_ratio * i)) // 256
            ng = int(g1 + (g_ratio * i)) // 256
            nb = int(b1 + (b_ratio * i)) // 256
            color = f'#{nr:02x}{ng:02x}{nb:02x}'
            canvas.create_line(0, i, width, i, fill=color)

    def center_window(self, width, height):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

class GomokuGUI:
    """מחלקת המשחק הראשית - מנהלת את כל לוגיקת המשחק והממשק"""
    
    def __init__(self, root):
        """אתחול משחק חדש - יצירת לוח, כפתורים וממשק המשתמש"""
        self.root = root
        self.root.title("Gomoku – Advanced Algorithms Project (Polished)")
        self.center_window(1100, 800)
        
        # Create gradient background
        self.bg_canvas = tk.Canvas(root, highlightthickness=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.draw_window_gradient()
        
        self.current_player = 0
        self.rounds = 0
        self.set_board_size()
        self.board = [[None for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.buttons = [[None for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.game_over = False
        self.block_mode = False
        self.bomb_mode = False
        self.blocks_left = [MAX_BLOCKS, MAX_BLOCKS]
        self.bomb_used = [False, False]
        self.double_move_used = [False, False]
        self.last_action = [None, None]
        self.scores = [0, 0]
        self.winning_cells = []
        self.double_move_active = [False, False]
        self.double_move_pending = False
        
        self.avatar_frame = tk.Frame(root, bg='#C172F5')
        self.avatar_frame.pack(pady=10)
        self.man_img = Image.open('man.png').resize((110, 110))
        self.robot_img = Image.open('robot.png').resize((110, 110))
        self.man_photo = None
        self.robot_photo = None
        self.man_border = tk.Label(self.avatar_frame, bg='#C172F5')
        self.man_border.grid(row=0, column=0, padx=120)
        self.robot_border = tk.Label(self.avatar_frame, bg='#C172F5')
        self.robot_border.grid(row=0, column=2, padx=120)
        self.avatar_spacer = tk.Label(self.avatar_frame, text='', width=10, bg='#C172F5')
        self.avatar_spacer.grid(row=0, column=1)
        self.update_avatar_highlight()
        self.man_score_label = tk.Label(self.avatar_frame, text=f"{self.scores[0]}", font=("Arial", 22, "bold"), fg="#FFFFFF", bg='#C172F5')
        self.man_score_label.grid(row=0, column=0, sticky='sw', padx=(0, 10), pady=(100, 0))
        self.robot_score_label = tk.Label(self.avatar_frame, text=f"{self.scores[1]}", font=("Arial", 22, "bold"), fg="#FFFFFF", bg='#C172F5')
        self.robot_score_label.grid(row=0, column=2, sticky='se', padx=(10, 0), pady=(100, 0))
        
        self.scoreboard_frame = tk.Frame(root, bg='#C172F5')
        self.scoreboard_frame.pack(pady=5)
        self.level_label = tk.Label(self.avatar_frame, text=self.get_level_text(), font=("Arial", 24, "bold"), fg="#FFFFFF", bg='#C172F5')
        self.level_label.grid(row=0, column=1, pady=(30, 0))
        
        # יצירת frame שמכיל את הגריד והכפתורים
        self.game_frame = tk.Frame(root, bg='#C172F5')
        self.game_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # הגריד בצד שמאל
        self.board_outer_frame = tk.Frame(self.game_frame, bg='#C172F5')
        self.board_outer_frame.pack(side='left', fill=tk.BOTH, expand=True)
        
        # Create canvas without scrollbars
        self.board_canvas = tk.Canvas(self.board_outer_frame, bg=DEFAULT_BG, highlightthickness=0)
        self.board_canvas.pack(expand=True, fill='both')
        
        # הכפתורים בצד ימין
        self.buttons_frame_right = tk.Frame(self.game_frame, bg='#C172F5')
        self.buttons_frame_right.pack(side='right', padx=20, pady=20)
        
        # עיצוב מודרני לכפתורים עם Canvas - אחד מעל השני
        self.block_button_canvas = tk.Canvas(self.buttons_frame_right, width=80, height=50, bg='#C172F5', highlightthickness=0)
        self.block_button_canvas.pack(pady=5)
        self.create_rounded_button(self.block_button_canvas, "🚫", self.toggle_block_mode, '#C172F5', '#FFFFFF')
        
        self.bomb_button_canvas = tk.Canvas(self.buttons_frame_right, width=80, height=50, bg='#C172F5', highlightthickness=0)
        self.bomb_button_canvas.pack(pady=5)
        self.create_rounded_button(self.bomb_button_canvas, "💣", self.activate_bomb_mode, '#C172F5', '#FFFFFF')
        
        self.double_move_button_canvas = tk.Canvas(self.buttons_frame_right, width=80, height=50, bg='#C172F5', highlightthickness=0)
        self.double_move_button_canvas.pack(pady=5)
        self.create_rounded_button(self.double_move_button_canvas, "✌️ Double!", self.activate_double_move, '#C172F5', '#FFFFFF')
        
        self.draw_modern_board()
        self.board_canvas.bind('<Button-1>', self.handle_canvas_click)
        self.board_canvas.bind('<Configure>', lambda e: self.draw_modern_board())
        
        self.buttons_frame = tk.Frame(root, bg='#C172F5')
        self.buttons_frame.pack(pady=10)
        self.reset_all_button_canvas = tk.Canvas(self.buttons_frame, width=140, height=50, bg='#C172F5', highlightthickness=0)
        self.reset_all_button_canvas.grid(row=0, column=0, padx=10, pady=5)
        self.create_rounded_button(self.reset_all_button_canvas, "Reset All", self.reset_all, '#C172F5', '#FFFFFF')
        self.update_option_buttons()

    def center_window(self, width, height):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def draw_window_gradient(self):
        """הגדרת רקע הסגול הבהיר על כל החלון במשחק"""
        self.bg_canvas.configure(bg='#C172F5')

    def set_board_size(self):
        """הגדרת גודל הלוח לפי הסיבוב - 5x5, 8x8, 10x10"""
        if self.rounds == 0:
            self.board_size = 5
        elif self.rounds == 1:
            self.board_size = 8
        else:
            self.board_size = 10

    def get_level_text(self):
        """קבלת טקסט הרמה הנוכחית"""
        return f"Level: {self.rounds+1}"

    def update_info_labels(self):
        """עדכון תוויות המידע - ניקוד ורמה"""
        self.man_score_label.config(text=f"{self.scores[0]}")
        self.robot_score_label.config(text=f"{self.scores[1]}")
        self.level_label.config(text=self.get_level_text())

    def update_option_buttons(self):
        """עדכון מצב כפתורי האפשרויות המיוחדות - חסימה, פצצה, תור כפול"""
        if self.blocks_left[0] <= 0:
            self.block_button_canvas.itemconfig(1, fill='#CCCCCC')  # button_rect
            self.block_button_canvas.itemconfig(2, fill='#888888')  # text_item
        else:
            self.block_button_canvas.itemconfig(1, fill='#C172F5')
            self.block_button_canvas.itemconfig(2, fill='#FFFFFF')
        if self.bomb_used[0]:
            self.bomb_button_canvas.itemconfig(1, fill='#CCCCCC')
            self.bomb_button_canvas.itemconfig(2, fill='#888888')
        else:
            self.bomb_button_canvas.itemconfig(1, fill='#C172F5')
            self.bomb_button_canvas.itemconfig(2, fill='#FFFFFF')
        if self.double_move_used[0]:
            self.double_move_button_canvas.itemconfig(1, fill='#CCCCCC')
            self.double_move_button_canvas.itemconfig(2, fill='#888888')
        else:
            self.double_move_button_canvas.itemconfig(1, fill='#C172F5')
            self.double_move_button_canvas.itemconfig(2, fill='#FFFFFF')

    def update_option_buttons_for(self, player_index):
        """עדכון כפתורי האפשרויות עבור שחקן ספציפי"""
        if self.blocks_left[player_index] <= 0:
            self.block_button_canvas.itemconfig(1, fill='#CCCCCC')
            self.block_button_canvas.itemconfig(2, fill='#888888')
        else:
            self.block_button_canvas.itemconfig(1, fill='#C172F5')
            self.block_button_canvas.itemconfig(2, fill='#FFFFFF')
        if self.bomb_used[player_index]:
            self.bomb_button_canvas.itemconfig(1, fill='#CCCCCC')
            self.bomb_button_canvas.itemconfig(2, fill='#888888')
        else:
            self.bomb_button_canvas.itemconfig(1, fill='#C172F5')
            self.bomb_button_canvas.itemconfig(2, fill='#FFFFFF')
        if self.double_move_used[player_index]:
            self.double_move_button_canvas.itemconfig(1, fill='#CCCCCC')
            self.double_move_button_canvas.itemconfig(2, fill='#888888')
        else:
            self.double_move_button_canvas.itemconfig(1, fill='#C172F5')
            self.double_move_button_canvas.itemconfig(2, fill='#FFFFFF')

    def toggle_block_mode(self):
        """הפעלה/כיבוי של מצב חסימה - מאפשר לשחקן לחסום תאים"""
        if self.game_over or self.bomb_mode or self.blocks_left[self.current_player] <= 0:
            return
        self.block_mode = not self.block_mode
        if self.block_mode:
            self.block_button_canvas.itemconfig(1, fill='#D4C7F7')
            # self.status_label.config(text="Block Mode: Click a cell to block.")
        else:
            self.block_button_canvas.itemconfig(1, fill='#C172F5')
            # self.status_label.config(text=f"Player's turn ({PLAYER_SYMBOLS[self.current_player]})")

    def activate_bomb_mode(self):
        """הפעלת מצב פצצה - מאפשר לשחקן לנקות שורות/עמודות/אלכסונים"""
        if self.game_over or self.bomb_mode or self.bomb_used[self.current_player]:
            return
        self.bomb_mode = True
        self.bomb_button_canvas.itemconfig(1, fill='#D4C7F7')
        # self.status_label.config(text=f"Bomb Mode: Choose what to clear!")
        # Show bomb type selection buttons
        self.show_bomb_type_buttons()

    def show_bomb_type_buttons(self):
        """הצגת כפתורי בחירת סוג הפצצה - עמודה, שורה, אלכסון"""
        self.bomb_type_frame = tk.Frame(self.buttons_frame_right, bg='#C172F5')
        self.bomb_type_frame.pack(pady=5)
        self.bomb_type = tk.StringVar(value='col')
        tk.Button(self.bomb_type_frame, text="Column", font=("Arial", 11), command=lambda: self.set_bomb_type('col')).pack(side=tk.LEFT, padx=2)
        tk.Button(self.bomb_type_frame, text="Row", font=("Arial", 11), command=lambda: self.set_bomb_type('row')).pack(side=tk.LEFT, padx=2)
        tk.Button(self.bomb_type_frame, text="Diagonal ↘", font=("Arial", 11), command=lambda: self.set_bomb_type('diag1')).pack(side=tk.LEFT, padx=2)
        tk.Button(self.bomb_type_frame, text="Diagonal ↙", font=("Arial", 11), command=lambda: self.set_bomb_type('diag2')).pack(side=tk.LEFT, padx=2)

    def set_bomb_type(self, bomb_type):
        """הגדרת סוג הפצצה שנבחר - עמודה, שורה, או אלכסון"""
        self.bomb_type = bomb_type
        # self.status_label.config(text=f"Bomb Mode: Click a cell to clear its {self.bomb_type_name(bomb_type)}!")
        if hasattr(self, 'bomb_type_frame'):
            self.bomb_type_frame.destroy()

    def bomb_type_name(self, bomb_type):
        """קבלת שם טקסטואלי לסוג הפצצה"""
        return {'col': 'column', 'row': 'row', 'diag1': 'diagonal ↘', 'diag2': 'diagonal ↙'}.get(bomb_type, 'column')

    def activate_double_move(self):
        """הפעלת תור כפול - מאפשר לשחקן לשחק פעמיים ברצף"""
        if self.double_move_used[self.current_player]:
            # self.status_label.config(text="Double Move already used!")
            return
        self.double_move_active[self.current_player] = True
        self.double_move_used[self.current_player] = True
        if self.current_player == 0:
            self.update_option_buttons_for(0)  # עדכון מיידי של כפתור השחקן האנושי
        # self.status_label.config(text="Double Move Active! שחק פעמיים ברצף")
        self.double_move_counter = 0  # סופר מהלכים כפולים

    def handle_click(self, row, col):
        """טיפול בלחיצה על תא בלוח - בדיקת מצב המשחק ופעולה מתאימה"""
        if self.double_move_active[self.current_player]:
            if self.game_over:
                return
            if self.board[row][col] is not None:
                return
            self.make_move(row, col, self.current_player, skip_switch=True)
            self.double_move_counter += 1
            if self.double_move_counter < 2:
                return
            else:
                self.double_move_active[self.current_player] = False
                self.double_move_counter = 0
                self.current_player = 1 - self.current_player
                if self.current_player == 1 and not self.game_over:
                    self.root.after(int(AI_DELAY * 1000), self.ai_move)
                return
        if self.game_over or self.current_player != 0:
            return
        if self.bomb_mode:
            bomb_type = getattr(self, 'bomb_type', 'col')
            self.use_bomb(row, col, bomb_type)
            return
        if self.block_mode:
            self.place_block(row, col)
            return
        if self.board[row][col] is not None:
            return
        if not self.blocks_left[self.current_player] <= 0 and self.last_action[self.current_player] == 'block':
            return
        self.make_move(row, col, 0)
        self.last_action[0] = 'move'
        if not self.game_over:
            self.root.after(int(AI_DELAY * 1000), self.ai_move)

    def place_block(self, row, col):
        """הצבת חסימה בתא נתון - מונעת משחק בתא זה"""
        if self.board[row][col] is not None:
            return
        if self.blocks_left[self.current_player] <= 0:
            return
        self.board[row][col] = BLOCK_SYMBOL
        self.blocks_left[self.current_player] -= 1
        if self.current_player == 0:
            self.update_option_buttons_for(0)
        self.block_mode = False
        self.block_button_canvas.itemconfig(1, fill='#C172F5')
        self.last_action[self.current_player] = 'move'
        self.current_player = 1 - self.current_player
        self.update_avatar_highlight()
        self.update_option_buttons()
        if self.current_player == 1 and not self.game_over:
            self.root.after(int(AI_DELAY * 1000), self.ai_move)
        elif self.current_player == 0 and not self.game_over:
            self.last_action[0] = 'move'
        self.draw_modern_board()

    def use_bomb(self, row, col, bomb_type='col'):
        """שימוש בפצצה - ניקוי שורה, עמודה או אלכסון מהלוח"""
        if self.bomb_used[self.current_player]:
            self.bomb_mode = False
            self.bomb_button_canvas.itemconfig(1, fill='#E8E4F3')
            return
        bomb_cells = self.get_bombed_cells(row, col, bomb_type)
        
        # Show bomb emoji first
        for r, c in bomb_cells:
            if hasattr(self, 'board_offset_x') and hasattr(self, 'cell_size'):
                x0 = self.board_offset_x + BOARD_PADDING + c * self.cell_size
                y0 = self.board_offset_y + BOARD_PADDING + r * self.cell_size
                font_size = max(20, self.cell_size // 2)
                self.board_canvas.create_text(x0 + self.cell_size//2, y0 + self.cell_size//2, text='💣', font=("Apple Color Emoji", font_size), fill='black', tags='bomb_effect')
        self.root.update()
        self.root.after(350)
        self.board_canvas.delete('bomb_effect')
        
        # Show explosion emoji
        for r, c in bomb_cells:
            if hasattr(self, 'board_offset_x') and hasattr(self, 'cell_size'):
                x0 = self.board_offset_x + BOARD_PADDING + c * self.cell_size
                y0 = self.board_offset_y + BOARD_PADDING + r * self.cell_size
                font_size = max(20, self.cell_size // 2)
                self.board_canvas.create_text(x0 + self.cell_size//2, y0 + self.cell_size//2, text='💥', font=("Apple Color Emoji", font_size), fill='red', tags='explosion_effect')
        self.root.update()
        self.root.after(350)
        self.board_canvas.delete('explosion_effect')
        
        for r, c in bomb_cells:
            self.board[r][c] = None
        self.bomb_used[self.current_player] = True
        if self.current_player == 0:
            self.update_option_buttons_for(0)
        self.bomb_mode = False
        self.bomb_button_canvas.itemconfig(1, fill='#C172F5')
        self.last_action[self.current_player] = 'bomb'
        self.current_player = 1 - self.current_player
        self.update_avatar_highlight()
        self.update_option_buttons()
        if self.current_player == 1 and not self.game_over:
            self.root.after(int(AI_DELAY * 1000), self.ai_move)
        if hasattr(self, 'bomb_type_frame'):
            self.bomb_type_frame.destroy()
        if hasattr(self, 'bomb_type'):
            del self.bomb_type
        self.draw_modern_board()

    def get_bombed_cells(self, row, col, bomb_type):
        """קבלת רשימת התאים שיינקו על ידי הפצצה לפי סוגה"""
        if bomb_type == 'col':
            return [(r, col) for r in range(self.board_size)]
        elif bomb_type == 'row':
            return [(row, c) for c in range(self.board_size)]
        elif bomb_type == 'diag1':  # ↘ main diagonal through (row, col)
            cells = []
            # Go to the top-left of the diagonal
            r, c = row, col
            while r > 0 and c > 0:
                r -= 1
                c -= 1
            # Collect all cells along the diagonal
            while r < self.board_size and c < self.board_size:
                cells.append((r, c))
                r += 1
                c += 1
            return cells
        elif bomb_type == 'diag2':  # ↙ anti-diagonal through (row, col)
            cells = []
            # Go to the top-right of the diagonal
            r, c = row, col
            while r > 0 and c < self.board_size - 1:
                r -= 1
                c += 1
            # Collect all cells along the diagonal
            while r < self.board_size and c >= 0:
                cells.append((r, c))
                r += 1
                c -= 1
            return cells
        else:
            return [(r, col) for r in range(self.board_size)]

    def make_move(self, row, col, player, skip_switch=False):
        """ביצוע מהלך - הצבת חתיכה ובדיקת ניצחון"""
        symbol = PLAYER_SYMBOLS[player]
        color = X_COLOR if player == 0 else O_COLOR
        self.board[row][col] = symbol
        
        # ציור הגריד מיד אחרי הצעד
        self.draw_modern_board()
        
        win_cells = self.get_win_cells(row, col, symbol)
        if win_cells:
            self.game_over = True
            self.disable_board()
            self.highlight_winning_cells(win_cells)
            # אפקט ניצחון
            self.show_win_effect(win_cells, player)
            return
        elif self.is_board_full():
            self.game_over = True
            self.handle_game_end(winner=None)
            return
        if not skip_switch:
            self.current_player = 1 - player
            self.last_action[player] = 'move'
            self.update_avatar_highlight()

    def highlight_winning_cells(self, win_cells):
        """סימון התאים המנצחים בלוח"""
        self.winning_cells = win_cells
    
    def show_win_effect(self, win_cells, player):
        """הצגת אפקט ניצחון עם אימוג'י על התאים המנצחים"""
        winner_emoji = "🏆" if player == 0 else "🤖"
        
        # הצגת האימוג'י על כל התאים המנצחים
        for r, c in win_cells:
            if hasattr(self, 'board_offset_x') and hasattr(self, 'cell_size'):
                x0 = self.board_offset_x + BOARD_PADDING + c * self.cell_size
                y0 = self.board_offset_y + BOARD_PADDING + r * self.cell_size
                font_size = max(20, self.cell_size // 2)
                self.board_canvas.create_text(x0 + self.cell_size//2, y0 + self.cell_size//2, 
                                           text=winner_emoji, font=("Apple Color Emoji", font_size), 
                                           fill='#FFD700', tags='win_effect')
        
        self.root.update()
        self.root.after(1500)  # המתנה של 1.5 שניות
        
        # מחיקת האפקט
        self.board_canvas.delete('win_effect')
        
        # המשך לסיום המשחק
        self.handle_game_end(winner=player)

    def get_win_cells(self, row, col, symbol):
        """בדיקה אם יש רצף מנצח מהתא הנוכחי - מחזיר את התאים המנצחים"""
        for d_row, d_col in [(0,1),(1,0),(1,1),(1,-1)]:
            cells = [(row, col)]
            r, c = row + d_row, col + d_col
            while 0 <= r < self.board_size and 0 <= c < self.board_size and self.board[r][c] == symbol:
                cells.append((r, c))
                r += d_row
                c += d_col
            r, c = row - d_row, col - d_col
            while 0 <= r < self.board_size and 0 <= c < self.board_size and self.board[r][c] == symbol:
                cells.insert(0, (r, c))
                r -= d_row
                c -= d_col
            if len(cells) >= WIN_LENGTH:
                return cells[:WIN_LENGTH]
        return None

    def handle_game_end(self, winner):
        """טיפול בסיום משחק - עדכון ניקוד, הצגת הודעה ומעבר לסיבוב הבא"""
        self.rounds += 1
        if winner == 0:
            self.scores[0] += WIN_POINTS
            self.scores[1] += LOSS_POINTS
            msg = f"Player wins!"
        elif winner == 1:
            self.scores[1] += WIN_POINTS
            self.scores[0] += LOSS_POINTS
            msg = f"AI wins!"
        else:
            self.scores[0] += TIE_POINTS
            self.scores[1] += TIE_POINTS
            msg = "It's a tie!"
        self.update_info_labels()
        messagebox.showinfo("Round Over", f"{msg}\n\nScore:\nPlayer: {self.scores[0]}\nAI: {self.scores[1]}\nRounds played: {self.rounds}")
        if self.rounds >= MAX_ROUNDS:
            if self.scores[0] > self.scores[1]:
                series_msg = "Player wins the series!"
            elif self.scores[1] > self.scores[0]:
                series_msg = "AI wins the series!"
            else:
                series_msg = "The series ends in a tie!"
            messagebox.showinfo("Series Over", f"Series finished!\n{series_msg}\n\nFinal Score:\nPlayer: {self.scores[0]}\nAI: {self.scores[1]}\n\nStarting new tournament...")
            self.reset_all()
        else:
            self.next_game()

    def ai_move(self):
        """ביצוע מהלך AI - שימוש באסטרטגיות שונות כולל חסימה, פצצה ותור כפול"""
        if self.game_over:
            return
            
        if self.blocks_left[1] > 0:
            dangerous_cell = self.ai_find_dangerous_cell()
            if dangerous_cell:
                row, col = dangerous_cell
                self.ai_place_block(row, col)
                return
                
        if not self.bomb_used[1]:
            bomb_target = self.ai_find_bomb_target()
            if bomb_target:
                row, col, bomb_type = bomb_target
                self.ai_use_bomb(row, col, bomb_type)
                return
                
        if not self.double_move_used[1]:
            best = self.find_best_move()
            if best:
                row, col = best
                if self.get_win_cells(row, col, '⚪'):
                    self.double_move_active[1] = True
                    self.double_move_used[1] = True
                    self.double_move_counter = 0
                    
        if self.double_move_active[1]:
            for _ in range(2):
                if self.game_over:
                    return
                best = self.find_best_move()
                if best:
                    row, col = best
                    self.make_move(row, col, 1, skip_switch=True)
                    self.double_move_counter += 1
                else:
                    break
            self.double_move_active[1] = False
            self.double_move_counter = 0
            self.current_player = 0
            return
            
        best = self.find_best_move()
        if best:
            row, col = best
            self.make_move(row, col, 1)

    def find_best_move(self):
        """מציאת המהלך הטוב ביותר עבור AI - אלגוריתם minimax"""
        for row in range(self.board_size):
            for col in range(self.board_size):
                if self.board[row][col] is None:
                    if self.get_win_cells(row, col, '⚪'):
                        return (row, col)
        
        for row in range(self.board_size):
            for col in range(self.board_size):
                if self.board[row][col] is None:
                    if self.get_win_cells(row, col, '⚫'):
                        return (row, col)
        
        best_score = float('-inf')
        best_move = None
        for row in range(self.board_size):
            for col in range(self.board_size):
                if self.board[row][col] is None:
                    new_board = copy.deepcopy(self.board)
                    new_board[row][col] = '⚪'
                    score = self.minimax(new_board, AI_DEPTH - 1, False, float('-inf'), float('inf'))
                    if score > best_score:
                        best_score = score
                        best_move = (row, col)
        return best_move



    def minimax(self, board, depth, maximizing, alpha, beta):
        """אלגוריתם minimax עם alpha-beta pruning לחישוב המהלך הטוב ביותר"""
        winner = self.get_winner(board)
        if winner in ('O', '⚪'):
            return 1_000_000
        elif winner in ('X', '⚫'):
            return -1_000_000
        elif self.is_full(board):
            return 0
        if depth == 0:
            return self.evaluate_board(board)
        if maximizing:
            max_eval = float('-inf')
            for row in range(self.board_size):
                for col in range(self.board_size):
                    if board[row][col] is None:
                        board[row][col] = '⚪'
                        eval = self.minimax(board, depth-1, False, alpha, beta)
                        board[row][col] = None
                        max_eval = max(max_eval, eval)
                        alpha = max(alpha, eval)
                        if beta <= alpha:
                            return max_eval
            return max_eval
        else:
            min_eval = float('inf')
            for row in range(self.board_size):
                for col in range(self.board_size):
                    if board[row][col] is None:
                        board[row][col] = '⚫'
                        eval = self.minimax(board, depth-1, True, alpha, beta)
                        board[row][col] = None
                        min_eval = min(min_eval, eval)
                        beta = min(beta, eval)
                        if beta <= alpha:
                            return min_eval
            return min_eval

    def evaluate_board(self, board):
        """הערכת מצב הלוח - חישוב ציון עבור AI"""
        score = 0
        for row in range(self.board_size):
            for col in range(self.board_size):
                if board[row][col] not in (None, BLOCK_SYMBOL):
                    symbol = board[row][col]
                    for d_row, d_col in [(0,1),(1,0),(1,1),(1,-1)]:
                        score += self.evaluate_direction(board, row, col, d_row, d_col, symbol)
        return score

    def evaluate_direction(self, board, row, col, d_row, d_col, symbol):
        """הערכת כיוון ספציפי בלוח - חישוב ציון עבור רצף נתון"""
        prev_r, prev_c = row - d_row, col - d_col
        if 0 <= prev_r < self.board_size and 0 <= prev_c < self.board_size and board[prev_r][prev_c] == symbol:
            return 0
        length = 0
        r, c = row, col
        while 0 <= r < self.board_size and 0 <= c < self.board_size and board[r][c] == symbol:
            length += 1
            r += d_row
            c += d_col
        if length < 2:
            return 0
        end_r, end_c = r, c
        open_ends = 0
        for check_r, check_c in [(row - d_row, col - d_col), (end_r, end_c)]:
            if 0 <= check_r < self.board_size and 0 <= check_c < self.board_size and board[check_r][check_c] is None:
                open_ends += 1
        if symbol in ('O', '⚪'):
            base = 10
        else:
            base = -10
        if open_ends == 2:
            return base ** length
        elif open_ends == 1:
            return (base ** length) // 2
        else:
            return 0

    def get_winner(self, board):
        """בדיקה אם יש מנצח בלוח נתון"""
        for row in range(self.board_size):
            for col in range(self.board_size):
                symbol = board[row][col]
                if symbol not in ('X', 'O', '⚫', '⚪'):
                    continue
                for d_row, d_col in [(0,1),(1,0),(1,1),(1,-1)]:
                    if self.count_consecutive_board(board, row, col, d_row, d_col, symbol) >= WIN_LENGTH:
                        return symbol
        return None

    def count_consecutive_board(self, board, row, col, d_row, d_col, symbol):
        """ספירת רצף של חתיכות בכיוון נתון בלוח"""
        count = 0
        r, c = row, col
        while 0 <= r < self.board_size and 0 <= c < self.board_size and board[r][c] == symbol:
            count += 1
            r += d_row
            c += d_col
        return count

    def is_full(self, board):
        """בדיקה אם הלוח מלא - תיקו"""
        for row in board:
            for cell in row:
                if cell is None:
                    return False
        return True

    def is_board_full(self):
        """בדיקה אם הלוח הנוכחי מלא"""
        for row in self.board:
            for cell in row:
                if cell is None:
                    return False
        return True

    def disable_board(self):
        """כיבוי הלוח - מניעת משחק נוסף"""
        pass

    def next_game(self):
        """מעבר למשחק הבא בטורניר - יצירת לוח חדש ועדכון ממשק"""
        if self.rounds >= MAX_ROUNDS:
            return
        self.current_player = 0
        self.set_board_size()
        self.board = [[None for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.buttons = [[None for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.game_over = False
        self.block_mode = False
        self.bomb_mode = False
        self.last_action = [None, None]
        self.update_info_labels()
        self.block_button_canvas.itemconfig(1, fill='#C172F5')
        self.bomb_button_canvas.itemconfig(1, fill='#C172F5')
        self.winning_cells = []
        
        # Recreate board canvas properly
        for widget in self.board_outer_frame.winfo_children():
            widget.destroy()
        
        # Recreate canvas without scrollbars
        self.board_canvas = tk.Canvas(self.board_outer_frame, bg=DEFAULT_BG, highlightthickness=0)
        self.board_canvas.pack(expand=True, fill='both')
        
        self.draw_modern_board()
        self.board_canvas.bind('<Button-1>', self.handle_canvas_click)
        self.board_canvas.bind('<Configure>', lambda e: self.draw_modern_board())
        self.update_option_buttons()

    def reset_all(self):
        """איפוס מלא של המשחק - ניקוד, סיבובים ואפשרויות"""
        self.scores = [0, 0]
        self.rounds = 0
        self.blocks_left = [MAX_BLOCKS, MAX_BLOCKS]
        self.bomb_used = [False, False]
        self.double_move_used = [False, False]
        self.next_game()
        self.update_info_labels()
        self.update_option_buttons()

    def make_circle_avatar(self, img, border_color=None, border_width=6):
        """יצירת אווטאר עגול עם מסגרת צבעונית"""
        size = img.size[0]
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        avatar = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        avatar.paste(img, (0, 0), mask)
        if border_color:
            border = Image.new('RGBA', (size + border_width*2, size + border_width*2), (0,0,0,0))
            border_draw = ImageDraw.Draw(border)
            border_draw.ellipse((0, 0, size + border_width*2 - 1, size + border_width*2 - 1), fill=None, outline=border_color, width=border_width)
            border.paste(avatar, (border_width, border_width), avatar)
            return ImageTk.PhotoImage(border)
        else:
            return ImageTk.PhotoImage(avatar)

    def update_avatar_highlight(self):
        """עדכון הדגשת האווטארים - סימון השחקן הנוכחי"""
        dark_green = '#008000'
        if self.current_player == 0:
            self.man_photo = self.make_circle_avatar(self.man_img, border_color=dark_green, border_width=8)
            self.robot_photo = self.make_circle_avatar(self.robot_img, border_color=None)
        else:
            self.man_photo = self.make_circle_avatar(self.man_img, border_color=None)
            self.robot_photo = self.make_circle_avatar(self.robot_img, border_color=dark_green, border_width=8)
        self.man_border.config(image=self.man_photo)
        self.robot_border.config(image=self.robot_photo)

    def create_rounded_rect(self, canvas, x1, y1, x2, y2, r=16, **kwargs):
        """יצירת מלבן מעוגל על canvas עם רדיוס נתון"""
        points = [
            x1+r, y1,
            x2-r, y1,
            x2, y1,
            x2, y1+r,
            x2, y2-r,
            x2, y2,
            x2-r, y2,
            x1+r, y2,
            x1, y2,
            x1, y2-r,
            x1, y1+r,
            x1, y1
        ]
        return canvas.create_polygon(points, smooth=True, **kwargs)
    
    def create_rounded_button(self, canvas, text, command, bg_color, fg_color):
        """יצירת כפתור מעוגל מותאם אישית על canvas"""
        width = canvas.winfo_reqwidth()
        height = canvas.winfo_reqheight()
        
        # ציור הכפתור המעוגל
        button_rect = self.create_rounded_rect(canvas, 2, 2, width-2, height-2, r=12, 
                                             fill=bg_color, outline='#D4C7F7', width=2)
        
        # הוספת הטקסט
        text_item = canvas.create_text(width//2, height//2, text=text, 
                                     font=("Arial", 14, "bold"), fill=fg_color)
        
        # הוספת אפקט hover
        def on_enter(e):
            canvas.itemconfig(button_rect, fill='#D4C7F7')
        
        def on_leave(e):
            canvas.itemconfig(button_rect, fill=bg_color)
        
        def on_click(e):
            command()
        
        canvas.bind('<Enter>', on_enter)
        canvas.bind('<Leave>', on_leave)
        canvas.bind('<Button-1>', on_click)
        
        return button_rect, text_item

    def draw_modern_board(self):
        """ציור הלוח המודרני עם גרדיאנט, חתיכות מעוצבות ואפקטים"""
        self.board_canvas.delete('all')
        size = self.board_size
        
        # Get canvas dimensions
        canvas_w = self.board_canvas.winfo_width()
        canvas_h = self.board_canvas.winfo_height()
        
        # If canvas is not yet configured, use default size
        if canvas_w <= 1 or canvas_h <= 1:
            canvas_w = 800
            canvas_h = 600
        
        # Calculate cell size to fill the canvas
        cell_size = min((canvas_w - 2 * BOARD_PADDING) // size, (canvas_h - 2 * BOARD_PADDING) // size)
        
        # Ensure minimum cell size
        if cell_size < 20:
            cell_size = 20
        
        # Calculate board dimensions
        w = h = cell_size * size + BOARD_PADDING * 2
        
        # Center the board
        offset_x = (canvas_w - w) // 2
        offset_y = (canvas_h - h) // 2
        
        # Create gradient background for the board container
        board_img = Image.new('RGBA', (w, h), (0,0,0,0))
        draw = ImageDraw.Draw(board_img)
        
        # Create gradient from purple to blue
        for y in range(h):
            ratio = y / h
            r = int(90 * (1 - ratio) + 193 * ratio)  # Purple to blue
            g = int(95 * (1 - ratio) + 114 * ratio)
            b = int(239 * (1 - ratio) + 245 * ratio)
            draw.rectangle([0, y, w-1, y], fill=(r, g, b, 180))
        
        # Add rounded corners and shadow
        shadow = Image.new('RGBA', (w+20, h+20), (0,0,0,0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle([10,10,w+10-1,h+10-1], radius=25, fill=(0,0,0,40))
        shadow = shadow.filter(ImageFilter.GaussianBlur(8))
        
        # Composite shadow and board
        board_img_with_shadow = Image.alpha_composite(shadow.crop((0,0,w,h)), board_img)
        self._board_img_tk = ImageTk.PhotoImage(board_img_with_shadow)
        self.board_canvas.create_image(offset_x, offset_y, anchor='nw', image=self._board_img_tk)
        
        # Store board position for click handling
        self.board_offset_x = offset_x
        self.board_offset_y = offset_y
        self.cell_size = cell_size
        
        # Draw grid cells
        for r in range(size):
            for c in range(size):
                x0 = offset_x + BOARD_PADDING + c*cell_size
                y0 = offset_y + BOARD_PADDING + r*cell_size
                x1 = x0 + cell_size
                y1 = y0 + cell_size
                
                # Create semi-transparent cell with rounded corners
                cell_img = Image.new('RGBA', (cell_size, cell_size), (0,0,0,0))
                cell_draw = ImageDraw.Draw(cell_img)
                cell_draw.rounded_rectangle([0,0,cell_size-1,cell_size-1], radius=18, 
                                          fill=(255,255,255,25), outline=(255,255,255,50), width=1)
                cell_img_tk = ImageTk.PhotoImage(cell_img)
                self.board_canvas.create_image(x0, y0, anchor='nw', image=cell_img_tk)
                if not hasattr(self, '_cell_imgs_tk'):
                    self._cell_imgs_tk = []
                self._cell_imgs_tk.append(cell_img_tk)
                
                # Draw pieces with glossy effect
                val = self.board[r][c]
                if val in ('⚫', 'X'):
                    # Blue glossy piece for player 1
                    piece_size = cell_size - 16  # Leave some margin
                    piece_img = Image.new('RGBA', (piece_size, piece_size), (0,0,0,0))
                    piece_draw = ImageDraw.Draw(piece_img)
                    
                    # Main blue circle
                    piece_draw.ellipse([0,0,piece_size-1,piece_size-1], fill=(115,209,255,200), outline=(59,144,224,255), width=3)
                    
                    # Shine effect (white highlight)
                    shine_size = piece_size // 3
                    piece_draw.ellipse([2,2,shine_size,shine_size], fill=(255,255,255,120))
                    
                    # Shadow effect
                    piece_draw.ellipse([3,3,piece_size-1,piece_size-1], fill=(59,144,224,80))
                    
                    piece_img_tk = ImageTk.PhotoImage(piece_img)
                    piece_offset = (cell_size - piece_size) // 2
                    self.board_canvas.create_image(x0+piece_offset, y0+piece_offset, anchor='nw', image=piece_img_tk)
                    self._cell_imgs_tk.append(piece_img_tk)
                    
                elif val in ('⚪', 'O'):
                    # Orange-pink glossy piece for player 2
                    piece_size = cell_size - 16  # Leave some margin
                    piece_img = Image.new('RGBA', (piece_size, piece_size), (0,0,0,0))
                    piece_draw = ImageDraw.Draw(piece_img)
                    
                    # Main orange-pink circle
                    piece_draw.ellipse([0,0,piece_size-1,piece_size-1], fill=(255,182,163,200), outline=(247,96,96,255), width=3)
                    
                    # Shine effect (white highlight)
                    shine_size = piece_size // 3
                    piece_draw.ellipse([2,2,shine_size,shine_size], fill=(255,255,255,120))
                    
                    # Shadow effect
                    piece_draw.ellipse([3,3,piece_size-1,piece_size-1], fill=(247,96,96,80))
                    
                    piece_img_tk = ImageTk.PhotoImage(piece_img)
                    piece_offset = (cell_size - piece_size) // 2
                    self.board_canvas.create_image(x0+piece_offset, y0+piece_offset, anchor='nw', image=piece_img_tk)
                    self._cell_imgs_tk.append(piece_img_tk)
                    
                elif val == BLOCK_SYMBOL:
                    # Block symbol with red tint
                    font_size = max(20, cell_size // 2)
                    self.board_canvas.create_text(x0 + cell_size//2, y0 + cell_size//2, 
                                                text=BLOCK_SYMBOL, font=("Apple Color Emoji", font_size), fill='#D32F2F')

    def handle_canvas_click(self, event):
        """טיפול בלחיצה על canvas הלוח - המרת קואורדינטות וטיפול במהלך"""
        x = event.x
        y = event.y
        
        # Check if click is within board bounds
        if not hasattr(self, 'board_offset_x') or not hasattr(self, 'cell_size'):
            return
            
        board_x = x - self.board_offset_x
        board_y = y - self.board_offset_y
        
        # Check if click is within the actual board area
        if (board_x < BOARD_PADDING or board_y < BOARD_PADDING or 
            board_x >= BOARD_PADDING + self.board_size * self.cell_size or 
            board_y >= BOARD_PADDING + self.board_size * self.cell_size):
            return
            
        # Calculate cell coordinates
        col = int((board_x - BOARD_PADDING) // self.cell_size)
        row = int((board_y - BOARD_PADDING) // self.cell_size)
        
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            self.handle_click(row, col)

    def on_mousewheel(self, event):
        """טיפול בגלילת עכבר - שינוי גודל הלוח"""
        self.board_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def ai_use_bomb(self, row, col, bomb_type):
        """AI משתמש בפצצה - בחירת מיקום וסוג פצצה אופטימלי"""
        if self.bomb_used[1]:
            return
        bomb_cells = self.get_bombed_cells(row, col, bomb_type)
        
        # Show bomb emoji first
        for r, c in bomb_cells:
            if hasattr(self, 'board_offset_x') and hasattr(self, 'cell_size'):
                x0 = self.board_offset_x + BOARD_PADDING + c * self.cell_size
                y0 = self.board_offset_y + BOARD_PADDING + r * self.cell_size
                font_size = max(20, self.cell_size // 2)
                self.board_canvas.create_text(x0 + self.cell_size//2, y0 + self.cell_size//2, text='💣', font=("Apple Color Emoji", font_size), fill='black', tags='ai_bomb_effect')
        self.root.update()
        self.root.after(350)
        self.board_canvas.delete('ai_bomb_effect')
        
        # Show explosion emoji
        for r, c in bomb_cells:
            if hasattr(self, 'board_offset_x') and hasattr(self, 'cell_size'):
                x0 = self.board_offset_x + BOARD_PADDING + c * self.cell_size
                y0 = self.board_offset_y + BOARD_PADDING + r * self.cell_size
                font_size = max(20, self.cell_size // 2)
                self.board_canvas.create_text(x0 + self.cell_size//2, y0 + self.cell_size//2, text='💥', font=("Apple Color Emoji", font_size), fill='red', tags='ai_explosion_effect')
        self.root.update()
        self.root.after(350)
        self.board_canvas.delete('ai_explosion_effect')
        
        for r, c in bomb_cells:
            self.board[r][c] = None
        self.bomb_used[1] = True
        self.last_action[1] = 'bomb'
        self.current_player = 0
        self.update_avatar_highlight()
        self.draw_modern_board()

    def ai_place_block(self, row, col):
        """AI מחסום תא - בחירת מיקום חסימה אסטרטגי"""
        if self.board[row][col] is not None or self.blocks_left[1] <= 0:
            return
        if hasattr(self, 'board_offset_x') and hasattr(self, 'cell_size'):
            x0 = self.board_offset_x + BOARD_PADDING + col * self.cell_size
            y0 = self.board_offset_y + BOARD_PADDING + row * self.cell_size
            font_size = max(20, self.cell_size // 2)
            self.board_canvas.create_text(x0 + self.cell_size//2, y0 + self.cell_size//2, text='🚫', font=("Apple Color Emoji", font_size), fill='#D32F2F', tags='ai_block_effect')
        self.root.update()
        self.root.after(200)
        self.board_canvas.delete('ai_block_effect')
        self.board[row][col] = BLOCK_SYMBOL
        self.blocks_left[1] -= 1
        self.last_action[1] = 'move'
        self.current_player = 0
        self.update_avatar_highlight()
        self.draw_modern_board()

    def ai_find_dangerous_cell(self):
        """מציאת תא מסוכן לחסימה - AI מחפש רצפים של 4+ חתיכות"""
        for row in range(self.board_size):
            for col in range(self.board_size):
                if self.board[row][col] is not None:
                    continue
                for d_row, d_col in [(0,1), (1,0), (1,1), (1,-1)]:
                    count = 0
                    r, c = row + d_row, col + d_col
                    while 0 <= r < self.board_size and 0 <= c < self.board_size and self.board[r][c] in ('X', '⚫'):
                        count += 1
                        r += d_row
                        c += d_col
                    r, c = row - d_row, col - d_col
                    while 0 <= r < self.board_size and 0 <= c < self.board_size and self.board[r][c] in ('X', '⚫'):
                        count += 1
                        r -= d_row
                        c -= d_col
                    if count >= 4:
                        return (row, col)
        return None

    def ai_find_bomb_target(self):
        """מציאת יעד לפצצה - AI מחפש אזורים צפופים לניקוי"""
        best_target = None
        max_score = 0

        for row in range(self.board_size):
            for col in range(self.board_size):
                for bomb_type in ['col', 'row', 'diag1', 'diag2']:
                    bomb_cells = self.get_bombed_cells(row, col, bomb_type)
                    score = 0
                    for r, c in bomb_cells:
                        if self.board[r][c] in ('X', '⚫'):
                            score += 2
                        elif self.board[r][c] in ('O', '⚪'):
                            score -= 1
                    if score > max_score and score >= 6:
                        max_score = score
                        best_target = (row, col, bomb_type)

        return best_target


def main():
    """פונקציה ראשית - יצירת חלון והפעלת המשחק"""
    root = tk.Tk()
    root.geometry('1100x800')
    root.minsize(900, 600)
    app = GomokuApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()