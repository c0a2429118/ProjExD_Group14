import pygame
import sys
import time
import random
import os

# --- 作業ディレクトリをこのファイルの場所に ---
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# --- 定数 ---
WIDTH, HEIGHT = 640, 640
CELL_SIZE = WIDTH // 8
GREEN = (0, 150, 0)
BLACK = (0, 0, 0)
WHITE = (240, 240, 240)
GRAY = (80, 80, 80)
FONT_COLOR = (255, 255, 0)

EMPTY = 0
PLAYER_BLACK = 1
PLAYER_WHITE = 2  # CPU

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
screen = pygame.display.set_mode((WIDTH, HEIGHT + 80))
pygame.display.set_caption("オセロ (プレイヤー vs CPU)")
try:
    font = pygame.font.SysFont("MS Gothic", 28)
except pygame.error:
    font = pygame.font.Font(None, 28)

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
        for dx, dy in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            nx, ny = x + dx, y + dy
            if (0 <= nx < 8 and 0 <= ny < 8) and self.grid[ny][nx] == opponent:
                while 0 <= nx < 8 and 0 <= ny < 8:
                    nx += dx; ny += dy
                    if not (0 <= nx < 8 and 0 <= ny < 8) or self.grid[ny][nx] == EMPTY:
                        break
                    if self.grid[ny][nx] == player:
                        return True
        return False

    def get_valid_moves(self, player):
        return [(x, y) for y in range(8) for x in range(8) if self.is_valid_move(x, y, player)]

    def place_stone(self, x, y, player):
        if not self.is_valid_move(x, y, player):
            return
        self.grid[y][x] = player
        opponent = PLAYER_WHITE if player == PLAYER_BLACK else PLAYER_BLACK

        flipped_total = 0
        for dx, dy in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            nx, ny = x + dx, y + dy
            stones_to_flip = []
            while (0 <= nx < 8 and 0 <= ny < 8) and self.grid[ny][nx] == opponent:
                stones_to_flip.append((nx, ny))
                nx += dx; ny += dy
            if (0 <= nx < 8 and 0 <= ny < 8) and self.grid[ny][nx] == player:
                for fx, fy in stones_to_flip:
                    self.grid[fy][fx] = player
                flipped_total += len(stones_to_flip)

        # 効果音（スライドの書式：snd.play(maxtime=最大ミリ秒)）
        try:
            if flipped_total > 0 and snd_put is not None:
                snd_put.play(maxtime=SND_MAX_MS)
        except Exception as e:
            print(f"[WARN] 効果音再生に失敗: {e}")

    def count_stones(self):
        return sum(r.count(PLAYER_BLACK) for r in self.grid), sum(r.count(PLAYER_WHITE) for r in self.grid)

class Game:
    def __init__(self):
        self.board = Board()
        self.current_player = PLAYER_BLACK
        self.game_over = False
        self.message = "あなたの番です (黒)"
        self.paused = False  # BGMの一時停止状態

    def run(self):
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.mixer.music.stop()
                    pygame.quit(); sys.exit()

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

                if self.current_player == PLAYER_BLACK and not self.game_over:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        x, y = event.pos[0] // CELL_SIZE, event.pos[1] // CELL_SIZE
                        if self.board.is_valid_move(x, y, PLAYER_BLACK):
                            self.board.place_stone(x, y, PLAYER_BLACK)
                            self.current_player = PLAYER_WHITE
                            self.message = "CPUの番です (白)"
                            self.draw(); pygame.display.flip()
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
        best_move, max_flips = None, -1
        for move in valid_moves:
            temp_board = [row[:] for row in self.board.grid]
            flips = 0
            for dx, dy in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
                nx, ny = move[0] + dx, move[1] + dy
                stones_to_flip = []
                while (0 <= nx < 8 and 0 <= ny < 8) and temp_board[ny][nx] == PLAYER_BLACK:
                    stones_to_flip.append((nx, ny))
                    nx += dx; ny += dy
                if (0 <= nx < 8 and 0 <= ny < 8) and temp_board[ny][nx] == PLAYER_WHITE:
                    flips += len(stones_to_flip)
            if flips > max_flips:
                max_flips, best_move = flips, move
        if best_move:
            self.board.place_stone(best_move[0], best_move[1], PLAYER_WHITE)
        self.current_player = PLAYER_BLACK
        self.message = "あなたの番です (黒)"

    def check_game_flow(self):
        if not self.board.get_valid_moves(self.current_player):
            opponent = PLAYER_WHITE if self.current_player == PLAYER_BLACK else PLAYER_BLACK
            if not self.board.get_valid_moves(opponent):
                self.game_over = True
                self.end_game()
            else:
                self.message = f"{'あなた' if self.current_player == PLAYER_BLACK else 'CPU'}はパスしました"
                self.draw(); pygame.display.flip()
                pygame.time.wait(1000)
                self.current_player = opponent

    def end_game(self):
        b, w = self.board.count_stones()
        winner = "あなたの勝ち" if b > w else "CPUの勝ち" if w > b else "引き分け"
        self.message = f"ゲーム終了！ {winner} ({b}-{w})"
        try:
            pygame.mixer.music.stop()   # ← スライドの stop
        except Exception:
            pass

    def draw(self):
        screen.fill(GREEN)
        for i in range(9):
            pygame.draw.line(screen, BLACK, (i*CELL_SIZE,0), (i*CELL_SIZE,HEIGHT), 2)
            pygame.draw.line(screen, BLACK, (0,i*CELL_SIZE), (WIDTH,i*CELL_SIZE), 2)
        for y in range(8):
            for x in range(8):
                if self.board.grid[y][x] != EMPTY:
                    color = BLACK if self.board.grid[y][x] == PLAYER_BLACK else WHITE
                    pygame.draw.circle(screen, color, (x*CELL_SIZE+CELL_SIZE//2, y*CELL_SIZE+CELL_SIZE//2), CELL_SIZE//2-4)

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
