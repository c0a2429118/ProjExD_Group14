import pygame
import sys
import time
import random
import os

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

# --- プレイヤー定数 ---
EMPTY = 0
PLAYER_BLACK = 1
PLAYER_WHITE = 2  # CPU

pygame.init()
#　画面サイズ修正
screen = pygame.display.set_mode((TOTAL_WIDTH, HEIGHT + 80))
pygame.display.set_caption("オセロ (プレイヤー vs CPU)")

try:
    # ### 修正点①: 文字サイズを小さく変更 ###
    font = pygame.font.SysFont("MSGothic", 28)
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


# --- Othello盤のロジックを管理するクラス ---
class Board:
    def __init__(self):
        self.grid = [[EMPTY] * 8 for _ in range(8)]
        self.grid[3][3] = PLAYER_WHITE
        self.grid[4][4] = PLAYER_WHITE
        self.grid[3][4] = PLAYER_BLACK
        self.grid[4][3] = PLAYER_BLACK

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

    def get_valid_moves(self, player):
        return [(x, y) for y in range(8) for x in range(8)
                if self.is_valid_move(x, y, player)]

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
            while (0 <= nx < 8 and 0 <= ny < 8) and self.grid[ny][nx] == opponent:
                stones_to_flip.append((nx, ny))
                nx += dx
                ny += dy
            if (0 <= nx < 8 and 0 <= ny < 8) and self.grid[ny][nx] == player:
                #追加返した石の数を加算
                total_flips += len(stones_to_flip)
                for fx, fy in stones_to_flip:
                    self.grid[fy][fx] = player

        #追加返した石の数
        return total_flips

    def count_stones(self):
        return (
            sum(r.count(PLAYER_BLACK) for r in self.grid),
            sum(r.count(PLAYER_WHITE) for r in self.grid)
        )


# --- ゲーム全体の進行と描画を管理するクラス ---
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
        self.current_player = PLAYER_BLACK
        self.game_over = False
        self.message = "あなたの番です (黒)"

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
        self.next_chatter_pool: Optional[List[str]] = None

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
                    pygame.quit()
                    sys.exit()

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

            if self.current_player == PLAYER_WHITE and not self.game_over:
                pygame.time.wait(500)
                self.ai_move()
                self.check_game_flow()

            self.draw()
            pygame.display.flip()
            clock.tick(30)

    def ai_move(self):
        valid_moves = self.board.get_valid_moves(PLAYER_WHITE)
        if not valid_moves:
            return

        best_move = None
        max_flips = -1

        for move in valid_moves:
            temp_board = [row[:] for row in self.board.grid]
            opponent = PLAYER_BLACK
            flips = 0
            for dx, dy in [(-1, -1), (-1, 0), (-1, 1),
                           (0, -1), (0, 1),
                           (1, -1), (1, 0), (1, 1)]:
                nx, ny = move[0] + dx, move[1] + dy
                stones_to_flip = []
                while (0 <= nx < 8 and 0 <= ny < 8) and temp_board[ny][nx] == opponent:
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
        self.message = "あなたの番です (黒)"

    def check_game_flow(self):
        if not self.board.get_valid_moves(self.current_player):
            opponent = PLAYER_WHITE if self.current_player == PLAYER_BLACK else PLAYER_BLACK
            if not self.board.get_valid_moves(opponent):
                #ゲームオーバーか
                if not self.game_over:
                    self.end_game()
            else:
                self.message = f"{'あなた' if self.current_player == PLAYER_BLACK else 'CPU'}はパスしました"
                self.draw()
                pygame.display.flip()
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

    def draw(self):
        screen.fill(GREEN)
        for i in range(9):
            pygame.draw.line(screen, BLACK, (i * CELL_SIZE, 0), (i * CELL_SIZE, HEIGHT), 2)
            pygame.draw.line(screen, BLACK, (0, i * CELL_SIZE), (WIDTH, i * CELL_SIZE), 2)

        for y in range(8):
            for x in range(8):
                if self.board.grid[y][x] != EMPTY:
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

        ui_bar_rect = pygame.Rect(0, HEIGHT, WIDTH, 80)
        pygame.draw.rect(screen, GRAY, ui_bar_rect)

        message_surf = font.render(self.message, True, FONT_COLOR)
        message_rect = message_surf.get_rect(centery=ui_bar_rect.centery, left=20)
        screen.blit(message_surf, message_rect)

        b, w = self.board.count_stones()
        score_text = f"黒(あなた):{b}  白(CPU):{w}"
        score_surf = font.render(score_text, True, FONT_COLOR)
        score_rect = score_surf.get_rect(centery=ui_bar_rect.centery, right=WIDTH - 20)
        screen.blit(score_surf, score_rect)


if __name__ == "__main__":
    game = Game()
    game.run()