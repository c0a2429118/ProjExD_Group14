import pygame
import sys
import random
import os
import time
from typing import List, Tuple, Optional, Set, Dict

# --- 作業ディレクトリをこのファイルの場所に ---
os.chdir(os.path.dirname(os.path.abspath(__file__)))
# --- 定数 ---
#右側幅追加
RIGHT_PANEL_WIDTH = 216
WIDTH, HEIGHT = 640, 640
#追加幅計算
TOTAL_WIDTH = WIDTH + RIGHT_PANEL_WIDTH
CELL_SIZE = WIDTH // 8
GREEN = (0, 150, 0)
BLACK = (0, 0, 0)
WHITE = (240, 240, 240)
GRAY = (80, 80, 80)
FONT_COLOR = (255, 255, 0)
#追加文字色定義
DIALOGUE_FONT_COLOR = (0, 0, 0)

EMPTY = 0
DIALOG_BG = (50, 50, 70)
BUTTON_COLOR = (100, 100, 150)

# プレイヤー定数
PLAYER_BLACK = 1 # 人間
PLAYER_WHITE = 2 # CPU

# --- サウンド初期化＆読み込み（スライド準拠） ---
pygame.mixer.init()
BGM_PATH = "クリームパンに見えるなぁ.mp3"
SND_PUT_PATH = "オセロ・コマ01.mp3"
SND_MAX_MS = 400  # 効果音が長すぎる場合の上限（スライドのmaxtimeの実演）

# BGM
try:
    pygame.mixer.music.load(BGM_PATH)
    pygame.mixer.music.set_volume(0.35)
    pygame.mixer.music.play(loops=-1)   # ← loops=-1で無限ループ（スライド準拠）
except Exception as e:
    print(f"[WARN] BGM 読み込み/再生に失敗: {e}")

# 効果音
snd_put = None
try:
    snd_put = pygame.mixer.Sound(SND_PUT_PATH)
    snd_put.set_volume(0.7)
except Exception as e:
    print(f"[WARN] 効果音 読み込み失敗: {e}")

pygame.init()
#　画面サイズ修正

screen = pygame.display.set_mode((TOTAL_WIDTH, HEIGHT + 80))
pygame.display.set_caption("オセロ (プレイヤー vs CPU)")

try:
    # ### 修正点①: 文字サイズを小さく変更 ###
    font = pygame.font.SysFont("MSGothic", 28)
    dialog_font = pygame.font.SysFont("MS Gothic", 32)
except pygame.error:
    dialog_font = pygame.font.Font(None, 32)
except Exception:
    font = pygame.font.Font(None, 28) # こちらも合わせて小さく

#吹き出し用フォント
try:
    dialogue_font = pygame.font.SysFont("MSGothic", 20)
except Exception:
    dialogue_font = pygame.font.Font(None, 24)


#追加画像読み込み
try:
    image1 = pygame.image.load("fig/image1.jpg")
    image1 = pygame.transform.scale(image1, (RIGHT_PANEL_WIDTH, 240))
except Exception as e:
    print(f"Error loading image1.jpg: {e}")
    image1 = None

#追加画像読み込み
try:
    image2 = pygame.image.load("fig/image2.jpg")
    image2 = pygame.transform.scale(image2, (RIGHT_PANEL_WIDTH, 83))
except Exception as e:
    print(f"Error loading image2.jpg: {e}")
    image2 = None

def gameover(screen: pygame.Surface) -> None:
    """

    引数:
        screen (pg.Surface): 画面(screen)
    """
    game_img = pygame.Surface((WIDTH, HEIGHT)) #空のサーフェス
    pygame.draw.rect(game_img, (0, 0, 0), (0, 0, 1100, 650))# 黒い四角形を作成
    game_img.set_alpha(255) #黒画面の透明度#フォントを作成
    txt = font.render("end", True, (255, 255, 255))
    game_img.blit(txt, [300,320])#文字
    screen.blit(game_img,[0, 0])
    pygame.display.update()
    pygame.time.wait(2000)

class Timer:
    """
    時間を測る機能
    """
    def __init__(self, font: pygame.font.Font):
        """
        タイマーの初期化。開始時刻と使用するフォントを記憶。
        """
        self.start_ticks = pygame.time.get_ticks()  # 開始時刻（ミリ秒）
        self.font = font
        self.elapsed_time = 0 # 経過時間（秒）
        self.game_over = False # ゲーム終了フラグ

    def update(self, game_over: bool):
        """
        経過時間を更新する。ゲームが終了したら更新を停止。
        """
        self.game_over = game_over #ゲームが終わっているか確認
        if not self.game_over:
            self.elapsed_time = (pygame.time.get_ticks() - self.start_ticks) // 1000
        



         
# --- Board クラス (ゲームロジック) ---
class Board:
    
    def __init__(self):
        self.grid = [[0] * 8 for _ in range(8)]
        self.grid[3][3] = PLAYER_WHITE; self.grid[4][4] = PLAYER_WHITE
        self.grid[3][4] = PLAYER_BLACK; self.grid[4][3] = PLAYER_BLACK
        
        self.fixed_stones = set()
        self.fix_charges = {PLAYER_BLACK: 2, PLAYER_WHITE: 2}

    #test
    def is_valid_move(self, x, y, player):
        if not (0 <= x < 8 and 0 <= y < 8) or self.grid[y][x] != EMPTY:
            return False

        opponent = PLAYER_WHITE if player == PLAYER_BLACK else PLAYER_BLACK

        for dx, dy in [(-1, -1), (-1, 0), (-1, 1),
                       (0, -1), (0, 1),
                       (1, -1), (1, 0), (1, 1)]:
            nx, ny = x + dx, y + dy
            if (0 <= nx < 8 and 0 <= ny < 8) and self.grid[ny][nx] == opponent:
                while 0 <= nx < 8 and 0 <= ny < 8:
                    nx += dx
                    ny += dy
                    if not (0 <= nx < 8 and 0 <= ny < 8) or self.grid[ny][nx] == EMPTY:
                        break
                    if self.grid[ny][nx] == player:
                        return True
        return False

    def opponent(self, player):
        return PLAYER_WHITE if player == PLAYER_BLACK else PLAYER_BLACK

    def can_place(self, x, y, player):
        if self.grid[y][x] != 0:
            return False
        
        for dx, dy in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 8 and 0 <= ny < 8 and self.grid[ny][nx] == self.opponent(player):
                while 0 <= nx < 8 and 0 <= ny < 8:
                    nx += dx
                    ny += dy
                    if not (0 <= nx < 8 and 0 <= ny < 8) or self.grid[ny][nx] == EMPTY:
                        break
                    if self.grid[ny][nx] == player:
                        return True
        return False

    def get_valid_moves(self, player):
        valid_moves = []
        for y in range(8):
            for x in range(8):
                if self.is_valid_move(x, y, player):
                    valid_moves.append((x, y))
        return valid_moves

    def get_valid_moves_positions(self, player):
        """
        現在のプレイヤーの全ての合法手の位置を取得する
        """
        valid_positions = []
        for y in range(8):
            for x in range(8):
                if self.is_valid_move(x, y, player):
                    valid_positions.append((x, y))
        return valid_positions
    
    def place_stone(self, x, y, player):
        if not self.is_valid_move(x, y, player):
            return 0

        self.grid[y][x] = player
        opponent = PLAYER_WHITE if player == PLAYER_BLACK else PLAYER_BLACK

        #追加返した石の数をカウントする変数
        total_flips = 0

        for dx, dy in [(-1, -1), (-1, 0), (-1, 1),
                       (0, -1), (0, 1),
                       (1, -1), (1, 0), (1, 1)]:
            nx, ny = x + dx, y + dy
            stones_to_flip = []
            nx, ny = x + dx, y + dy
            while 0 <= nx < 8 and 0 <= ny < 8 and self.grid[ny][nx] == self.opponent(player):
                stones_to_flip.append((nx, ny))
                nx += dx
                ny += dy
            if (0 <= nx < 8 and 0 <= ny < 8) and self.grid[ny][nx] == player:
                #追加返した石の数を加算
                total_flips += len(stones_to_flip)
                for fx, fy in stones_to_flip:
                    self.grid[fy][fx] = player
                #flipped_total += len(stones_to_flip)

        # 効果音（スライドの書式：snd.play(maxtime=最大ミリ秒)）
        try:
            if total_flips > 0 and snd_put is not None:
                snd_put.play(maxtime=SND_MAX_MS)
        except Exception as e:
            print(f"[WARN] 効果音再生に失敗: {e}")

        #追加返した石の数
        return total_flips

    def count_stones(self):
        return (
            sum(r.count(PLAYER_BLACK) for r in self.grid),
            sum(r.count(PLAYER_WHITE) for r in self.grid)
        )


# --- Game クラス (UIとゲーム進行) ---
class Game:
    """
    オセロゲーム全体の進行と描画、およびセリフ表示を管理するクラス。
    """
    def __init__(self)-> None:
        """
        Gameクラスのインスタンスを初期化
        
        セリフプールやセリフ管理用の変数を決め、
        ゲーム開始時の最初のセリフを設定する
        """
        self.board = Board()
        self.time = Timer(font)
        
        self.current_player = PLAYER_BLACK
        self.game_over = False
        self.message = "あなたの番です (黒)"
        self.paused = False  # BGMの一時停止状態

        #追加セリフプール
        self.pool1 = ["君が相手かい？", "君だと物足りないかも？", "よろしくね！", "いざ勝負！"]
        self.pool2 = ["元気してる？", "好きな授業はある？", "こんにちは", "さっき出席登録したっけ…"]
        self.pool3 = ["明日は晴れかな？", "次はここに置こうかな…？", "今日もぼくはかわいいなぁ"]
        self.pool4 = ["考えてるみたいだね", "投降も１つの選択だよ？", "疲れちゃったかな？", "眠くなっちゃうよ", "野菜でも食べる？"]
        self.pool5 = ["そこか", "本当にそれでいいの？", "あらら", "huh?", "blahblahblah.."]
        self.pool6 = ["へぇ？やるじゃんか", "なるほどね", "おっと…", "褒めてあげよう"]
        self.pool7 = ["やるね", "次は負けないよ", "おめでとう！", "君もいつかは…"]
        self.pool8 = ["工科大に栄光あれ！", "世界は広いんだよ", "まだまだだね", "畜生以下め"]

        #追加セリフ管理
        self.dialogue_text = ""
        self.dialogue_end_time: float = 0.0
        self.next_chatter_time: float = 0.0
        # self.next_chatter_pool: Optional[List[str]] = None

        #追加ゲーム開始時最初のセリフ
        self.set_dialogue(random.choice(self.pool1))

    #セリフを設定
    def set_dialogue(self, text: str) -> None: 
        """
        表示するセリフを設定し、3秒間の表示タイマーをセット

        現在の雑談タイマーをリセットし、ゲームが終了していなければ
        新しい雑談になる

        """
        self.dialogue_text = text
        self.dialogue_end_time = time.time() + 3
        self.next_chatter_time = 0
        if not self.game_over:
            self.schedule_chatter_task(self.dialogue_end_time)

    #追加次の雑談までの時間と内容
    def schedule_chatter_task(self, start_time: float) -> None:
        """
        次の雑談（独り言）セリフが発動する時間をスケジュールします。

        仕様に基づき、40%の確率で5秒後、30%で7秒後、30%で9秒後に
        発動するように設定し、使用するセリフプールを選択します。
        """
        rand_val: float = random.random()
        delay: int
        if rand_val < 0.4:#確率40%
            delay = 5
            self.next_chatter_pool = self.pool2
        elif rand_val < 0.7:#30%
            delay = 7
            self.next_chatter_pool = self.pool3
        else:
            delay = 9 #30%
            self.next_chatter_pool = self.pool4
        self.next_chatter_time = start_time + delay

    #追加吹き出しのサイズ
    def draw_text_wrapped(self, surface, text, font_obj, color, rect):
        lines = []
        words = text.split(' ')
        if len(words) == 1 and ' ' not in text:
            chars = list(text)
            current_line = ""
            for char in chars:
                test_line = current_line + char
                if font_obj.size(test_line)[0] <= rect.width:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = char
            lines.append(current_line)
        else:
            current_line = ""
            for word in words:
                test_line = current_line + word + " "
                if font_obj.size(test_line)[0] <= rect.width:
                    current_line = test_line
                else:
                    lines.append(current_line.strip())
                    current_line = word + " "
            lines.append(current_line.strip())

        y = rect.top
        for line in lines:
            if y + font_obj.get_linesize() > rect.bottom:
                break
            line_surf = font_obj.render(line, True, color)
            line_rect = line_surf.get_rect(centerx=rect.centerx, top=y)
            surface.blit(line_surf, line_rect)
            y += font_obj.get_linesize()
        self.show_legal_moves = True
        self.state = "playing"
        self.pending_move = None
        # CPUが固定を狙う戦略的なマス
        self.strategic_squares = {
            (0,0), (0,7), (7,0), (7,7), # 角
            (1,1), (1,6), (6,1), (6,6)  # 角の隣
        }

    def run(self):
        clock = pygame.time.Clock()
        while True:
            #追加セリフの表示時間雑談タイマー
            now = time.time()
            if self.dialogue_text and now > self.dialogue_end_time:
                self.dialogue_text = ""

            if not self.game_over and self.next_chatter_time != 0 and now > self.next_chatter_time:
                if self.next_chatter_pool:
                    text = random.choice(self.next_chatter_pool)
                    self.set_dialogue(text)
                #雑談ループ
                self.next_chatter_time = 0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_h:
                        self.show_legal_moves = not self.show_legal_moves
                
                if self.current_player == PLAYER_BLACK and not self.game_over:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        #マウス座標取得
                        mouse_x, mouse_y = event.pos
                        #マウスがオセロ盤の範囲内か
                        if mouse_x < WIDTH:
                            x, y = mouse_x // CELL_SIZE, mouse_y // CELL_SIZE
                            if self.board.is_valid_move(x, y, PLAYER_BLACK):
                                #返した石の数を取得 
                                flips = self.board.place_stone(x, y, PLAYER_BLACK)
                                
                                #追加返した石の数に応じてリアクション
                                if flips >= 3:
                                    text = random.choice(self.pool6)
                                else:
                                    text = random.choice(self.pool5)
                                self.set_dialogue(text)

                                self.current_player = PLAYER_WHITE
                                self.message = "CPUの番です (白)"
                                self.draw()
                                pygame.display.flip()
                                self.check_game_flow()
                    #pygame.mixer.music.stop()
                    #pygame.quit(); sys.exit()

                # --- 追加：スライドの操作確認に便利なホットキー ---
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m:  # Pause/Unpause
                        if not self.paused:
                            pygame.mixer.music.pause()
                            self.paused = True
                            self.message = "BGM一時停止 (Mで再開)"
                        else:
                            pygame.mixer.music.unpause()
                            self.paused = False
                            self.message = "BGM再開"
                    elif event.key == pygame.K_s:  # Stop
                        pygame.mixer.music.stop()
                        self.paused = False
                        self.message = "BGM停止 (Rで再生開始)"
                    elif event.key == pygame.K_r:  # Restart
                        pygame.mixer.music.play(loops=-1)
                        self.paused = False
                        self.message = "BGM再生開始"
                    elif event.key == pygame.K_UP:  # Volume up
                        vol = min(1.0, pygame.mixer.music.get_volume() + 0.05)
                        pygame.mixer.music.set_volume(vol)
                        self.message = f"BGM音量 ↑ {vol:.2f}"
                    elif event.key == pygame.K_DOWN:  # Volume down
                        vol = max(0.0, pygame.mixer.music.get_volume() - 0.05)
                        pygame.mixer.music.set_volume(vol)
                        self.message = f"BGM音量 ↓ {vol:.2f}"
                    elif event.key == pygame.K_e:  # SE test
                        if snd_put:
                            snd_put.play(maxtime=SND_MAX_MS)

                        x, y = event.pos[0] // CELL_SIZE, event.pos[1] // CELL_SIZE
                        if self.board.is_valid_move(x, y, PLAYER_BLACK):
                            self.board.place_stone(x, y, PLAYER_BLACK)
                            self.current_player = PLAYER_WHITE
                            self.message = "CPUの番です (白)"
                            self.draw()
                            pygame.display.flip()
                        self.check_game_flow()
                        self.time.update(self.game_over)

            if self.current_player == PLAYER_WHITE and not self.game_over:
                if not self.game_over:
                    self.handle_event(event)
            
            if self.current_player == PLAYER_WHITE and not self.game_over and self.state == "playing":
                self.draw()
                pygame.display.flip()
                pygame.time.wait(500)
                self.ai_move()
                self.check_game_flow()
                
            self.time.update(self.game_over)
            self.draw()
            pygame.display.flip()
            clock.tick(30)

    def ai_move(self):
        valid_moves = self.board.get_valid_moves(PLAYER_WHITE)
        if not valid_moves:
            return
        best_move, max_flips = None, -1
        for move in valid_moves:
            temp_board = [row[:] for row in self.board.grid]
            flips = self.count_flips_for_move(move[0], move[1], PLAYER_WHITE)
            for dx, dy in [(-1, -1), (-1, 0), (-1, 1),
                           (0, -1), (0, 1),
                           (1, -1), (1, 0), (1, 1)]:
                nx, ny = move[0] + dx, move[1] + dy
                stones_to_flip = []
                while (0 <= nx < 8 and 0 <= ny < 8) and temp_board[ny][nx] == PLAYER_BLACK:
                    stones_to_flip.append((nx, ny))
                    nx += dx
                    ny += dy
                if (0 <= nx < 8 and 0 <= ny < 8) and temp_board[ny][nx] == PLAYER_WHITE:
                    flips += len(stones_to_flip)
            if flips > max_flips:
                max_flips = flips
                best_move = move

        if best_move:
            self.board.place_stone(best_move[0], best_move[1], PLAYER_WHITE)
        self.current_player = PLAYER_BLACK

    def check_game_flow(self):
        if not self.board.get_valid_moves(self.current_player):
            opponent = PLAYER_WHITE if self.current_player == PLAYER_BLACK else PLAYER_BLACK
            if not self.board.get_valid_moves(opponent):
                #ゲームオーバーか
                if not self.game_over:
                    self.end_game()
            else:
                self.message = f"{'あなた' if self.current_player == PLAYER_BLACK else 'CPU'}はパスしました"
                self.draw(); pygame.display.flip()
                pygame.time.wait(1000)
                self.current_player = opponent

    def end_game(self):
        self.game_over = True
        #追加雑談タイマーを停止
        self.next_chatter_time = 0

        b, w = self.board.count_stones()
        winner = "あなたの勝ち" if b > w else "CPUの勝ち" if w > b else "引き分け"

        #追加勝敗に応じてセリフを設定 
        if b > w:
            text = random.choice(self.pool7)
        else:
            text = random.choice(self.pool8)
        self.set_dialogue(text)
        
        self.message = f"ゲーム終了！ {winner} ({b}-{w})"
        try:
            pygame.mixer.music.stop()   # ← スライドの stop
        except Exception:
            pass

        self.draw()
        gameover(screen)
        pygame.quit() 
        sys.exit()
    
    def count_flips_for_move(self, x, y, player):
        flips = 0
        for dx, dy in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            stones_to_flip = []
            nx, ny = x + dx, y + dy
            while 0 <= nx < 8 and 0 <= ny < 8 and self.board.grid[ny][nx] == self.board.opponent(player):
                stones_to_flip.append((nx, ny))
                nx += dx; ny += dy
            if 0 <= nx < 8 and 0 <= ny < 8 and self.board.grid[ny][nx] == player:
                flips += len(stones_to_flip)
        return flips

    def draw(self):
        screen.fill(GREEN)
        for i in range(9):
            pygame.draw.line(screen, BLACK, (i*CELL_SIZE,0), (i*CELL_SIZE,HEIGHT), 2)
            pygame.draw.line(screen, BLACK, (0,i*CELL_SIZE), (WIDTH,i*CELL_SIZE), 2)
        for y in range(8):
            for x in range(8):
                if self.board.grid[y][x] != 0:
                    color = BLACK if self.board.grid[y][x] == PLAYER_BLACK else WHITE
                    pygame.draw.circle(
                        screen, color,
                        (x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2),
                        CELL_SIZE // 2 - 4
                    )

        #追加右側パネル
        right_panel_rect = pygame.Rect(WIDTH, 0, RIGHT_PANEL_WIDTH, HEIGHT + 80)
        pygame.draw.rect(screen, GRAY, right_panel_rect)

        #追加image1
        if image1:
            screen.blit(image1, (WIDTH, 0))

        #追加image2
        if image2:
            screen.blit(image2, (WIDTH, 240))

        #追加吹き出し領域セリフ
        if self.dialogue_text:
            text_area_rect = pygame.Rect(
                WIDTH + 15,
                240 + 10,
                RIGHT_PANEL_WIDTH - 30,
                83 - 20
            )
            self.draw_text_wrapped(
                screen,
                self.dialogue_text,
                dialogue_font,
                DIALOGUE_FONT_COLOR,
                text_area_rect
            )

        # 合法手のヒントを描画する
        if self.show_legal_moves and not self.game_over:
            valid_moves = self.board.get_valid_moves_positions(self.current_player)
            for x, y in valid_moves:
                # 半透明のハイライト用サーフェスを作成する
                highlight_surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                pygame.draw.rect(highlight_surface, (255, 255, 0, 128), (0, 0, CELL_SIZE, CELL_SIZE))
                screen.blit(highlight_surface, (x * CELL_SIZE, y * CELL_SIZE))
                
                # ドットでヒントを描画する
                dot_x = x * CELL_SIZE + CELL_SIZE // 2
                dot_y = y * CELL_SIZE + CELL_SIZE // 2
                dot_color = WHITE if self.current_player == PLAYER_BLACK else BLACK
                pygame.draw.circle(screen, dot_color, (dot_x, dot_y), 5)
        # ### 修正点②: UIテキストの描画方法を改善 ###
        # 下部UIバーの領域を定義
        ui_bar_rect = pygame.Rect(0, HEIGHT, WIDTH, 80)
        pygame.draw.rect(screen, GRAY, ui_bar_rect)

        message_surf = font.render(self.message, True, FONT_COLOR)
        message_rect = message_surf.get_rect(centery=ui_bar_rect.centery, left=20)
        screen.blit(message_surf, message_rect)

        center = (x*CELL_SIZE+CELL_SIZE//2, y*CELL_SIZE+CELL_SIZE//2)
        pygame.draw.circle(screen, color, center, CELL_SIZE//2-4)
        if (x,y) in self.board.fixed_stones:
            pygame.draw.circle(screen, FONT_COLOR, center, 8)
        
        ui_rect = pygame.Rect(0, HEIGHT, WIDTH, 80)
        pygame.draw.rect(screen, GRAY, ui_rect)
        
        msg_surf = font.render(self.message, True, FONT_COLOR)
        screen.blit(msg_surf, (20, HEIGHT + 10))
        
        fix_info = f"固定権: あなた {self.board.fix_charges[PLAYER_BLACK]} | CPU {self.board.fix_charges[PLAYER_WHITE]}"
        fix_surf = font.render(fix_info, True, FONT_COLOR)
        screen.blit(fix_surf, (20, HEIGHT + 45))
        
        b, w = self.board.count_stones()
        score_text = f"あなた(黒):{b} CPU(白):{w}"
        score_surf = font.render(score_text, True, FONT_COLOR)
        score_rect = score_surf.get_rect(centery=ui_rect.centery, right=WIDTH-20)
        screen.blit(score_surf, score_rect)
        
        timer_x_pos = WIDTH // 2
        timer_y_pos = ui_bar_rect.centery 
        time_text = f"Time: {self.time.elapsed_time} s"
        time_surf = font.render(time_text, True, FONT_COLOR)
        time_rect = time_surf.get_rect(center=(timer_x_pos, timer_y_pos - 25))
        screen.blit(time_surf, time_rect)
        # Hキーで合法手のヒントの表示/非表示を切り替え
        legal_status = "合法走法表示: ON" if self.show_legal_moves else "合法走法表示: OFF"
        legal_surf = font.render(legal_status, True, FONT_COLOR)
        legal_rect = legal_surf.get_rect(centery=ui_bar_rect.centery + 20, left=20)
        screen.blit(legal_surf, legal_rect)
        
        # 操作ヒント    
        hint_text = "Hキー: 合法走法表示切替"
        hint_surf = font.render(hint_text, True, FONT_COLOR)
        hint_rect = hint_surf.get_rect(centery=ui_bar_rect.centery + 20, right=WIDTH - 20)
        screen.blit(hint_surf, hint_rect)

        if self.state == "awaiting_fix_choice":
            self.draw_choice_dialog()

    def draw_choice_dialog(self):
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); s.fill((0,0,0,128)); screen.blit(s,(0,0))
        self.dialog_rect = pygame.Rect(WIDTH//2-200, HEIGHT//2-100, 400, 200)
        pygame.draw.rect(screen, DIALOG_BG, self.dialog_rect, border_radius=15)
        q_text = dialog_font.render("この石を固定しますか？", True, WHITE)
        screen.blit(q_text, (self.dialog_rect.centerx - q_text.get_width()//2, self.dialog_rect.y + 30))
        self.yes_button = pygame.Rect(self.dialog_rect.x+50, self.dialog_rect.y+110, 120, 50)
        self.no_button = pygame.Rect(self.dialog_rect.x+230, self.dialog_rect.y+110, 150, 50)
        pygame.draw.rect(screen, BUTTON_COLOR, self.yes_button, border_radius=10)
        pygame.draw.rect(screen, BUTTON_COLOR, self.no_button, border_radius=10)
        yes_text = dialog_font.render("はい(Y)", True, WHITE)
        no_text = dialog_font.render("いいえ(N)", True, WHITE)
        screen.blit(yes_text, (self.yes_button.centerx-yes_text.get_width()//2, self.yes_button.centery-yes_text.get_height()//2))
        screen.blit(no_text, (self.no_button.centerx-no_text.get_width()//2, self.no_button.centery-no_text.get_height()//2))

    def process_player_choice(self, fix_it):
        x, y = self.pending_move
        self.board.place_stone(x, y, PLAYER_BLACK, fix_this_stone=fix_it)
        self.state = "playing"
        self.pending_move = None
        self.current_player = PLAYER_WHITE
        self.check_game_flow()

    def handle_event(self, event):
        if self.current_player == PLAYER_BLACK:
            if self.state == "playing":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos[0] // CELL_SIZE, event.pos[1] // CELL_SIZE
                    if self.board.can_place(x, y, PLAYER_BLACK):
                        if self.board.fix_charges[PLAYER_BLACK] > 0:
                            self.state = "awaiting_fix_choice"
                            self.pending_move = (x, y)
                        else:
                            self.board.place_stone(x, y, PLAYER_BLACK, False)
                            self.current_player = PLAYER_WHITE
                            self.check_game_flow()

            elif self.state == "awaiting_fix_choice":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.yes_button.collidepoint(event.pos): self.process_player_choice(True)
                    elif self.no_button.collidepoint(event.pos): self.process_player_choice(False)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y: self.process_player_choice(True)
                    elif event.key == pygame.K_n: self.process_player_choice(False)

    def check_game_flow(self):
        self.update_message()
        if not self.board.get_valid_moves(self.current_player):
            opponent = self.board.opponent(self.current_player)
            if not self.board.get_valid_moves(opponent):
                self.game_over = True; self.end_game()
            else:
                self.message = f"{'あなた' if self.current_player == PLAYER_BLACK else 'CPU'}はパス"
                self.draw(); pygame.display.flip(); pygame.time.wait(1000)
                self.current_player = opponent
                self.update_message()

    def update_message(self):
        if not self.game_over:
            self.message = "あなたの番です (黒)" if self.current_player == PLAYER_BLACK else "CPUの番です (白)"

    def end_game(self):
        b, w = self.board.count_stones()
        winner = "あなたの勝ち" if b > w else "CPUの勝ち" if w > b else "引き分け"
        self.message = f"ゲーム終了！ {winner} ({b}-{w})"

if __name__ == "__main__":
    game = Game()
    game.run()
