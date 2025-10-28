import pygame
import sys
import time
import random

# --- 定数 ---
WIDTH, HEIGHT = 640, 640
CELL_SIZE = WIDTH // 8
GREEN = (0, 150, 0)
BLACK = (0, 0, 0)
WHITE = (240, 240, 240)
GRAY = (80, 80, 80)
FONT_COLOR = (255, 255, 0)

# --- プレイヤー定数 ---
EMPTY = 0
PLAYER_BLACK = 1
PLAYER_WHITE = 2  # CPU

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT + 80))
pygame.display.set_caption("オセロ (プレイヤー vs CPU)")
try:
    # ### 修正点①: 文字サイズを小さく変更 ###
    font = pygame.font.SysFont("MS Gothic", 28) # 36から28へ
except pygame.error:
    font = pygame.font.Font(None, 28) # こちらも合わせて小さく

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
        
        for dx, dy in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            nx, ny = x + dx, y + dy
            if (0 <= nx < 8 and 0 <= ny < 8) and self.grid[ny][nx] == opponent:
                while 0 <= nx < 8 and 0 <= ny < 8:
                    nx += dx; ny += dy
                    if not (0 <= nx < 8 and 0 <= ny < 8) or self.grid[ny][nx] == EMPTY: break
                    if self.grid[ny][nx] == player: return True
        return False

    def get_valid_moves(self, player):
        return [(x, y) for y in range(8) for x in range(8) if self.is_valid_move(x, y, player)]

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
            return
        
        self.grid[y][x] = player
        opponent = PLAYER_WHITE if player == PLAYER_BLACK else PLAYER_BLACK

        for dx, dy in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            nx, ny = x + dx, y + dy
            stones_to_flip = []
            while (0 <= nx < 8 and 0 <= ny < 8) and self.grid[ny][nx] == opponent:
                stones_to_flip.append((nx, ny))
                nx += dx; ny += dy
            if (0 <= nx < 8 and 0 <= ny < 8) and self.grid[ny][nx] == player:
                for fx, fy in stones_to_flip:
                    self.grid[fy][fx] = player

    def count_stones(self):
        return sum(r.count(PLAYER_BLACK) for r in self.grid), sum(r.count(PLAYER_WHITE) for r in self.grid)

# --- ゲーム全体の進行と描画を管理するクラス ---
class Game:
    def __init__(self):
        self.board = Board()
        self.current_player = PLAYER_BLACK
        self.game_over = False
        self.message = "あなたの番です (黒)"
        self.show_legal_moves = True

    def run(self):
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_h:
                        self.show_legal_moves = not self.show_legal_moves
                
                if self.current_player == PLAYER_BLACK and not self.game_over:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        x, y = event.pos[0] // CELL_SIZE, event.pos[1] // CELL_SIZE
                        if self.board.is_valid_move(x, y, PLAYER_BLACK):
                            self.board.place_stone(x, y, PLAYER_BLACK)
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
            for dx, dy in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
                nx, ny = move[0] + dx, move[1] + dy
                stones_to_flip = []
                while (0 <= nx < 8 and 0 <= ny < 8) and temp_board[ny][nx] == opponent:
                    stones_to_flip.append((nx, ny))
                    nx += dx; ny += dy
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
                self.game_over = True
                self.end_game()
            else:
                self.message = f"{'あなた' if self.current_player == PLAYER_BLACK else 'CPU'}はパスしました"
                self.draw()
                pygame.display.flip()
                pygame.time.wait(1000)
                self.current_player = opponent
    
    def end_game(self):
        b, w = self.board.count_stones()
        winner = "あなたの勝ち" if b > w else "CPUの勝ち" if w > b else "引き分け"
        self.message = f"ゲーム終了！ {winner} ({b}-{w})"
    
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

        # メッセージを左寄せで表示
        message_surf = font.render(self.message, True, FONT_COLOR)
        message_rect = message_surf.get_rect(centery=ui_bar_rect.centery, left=20)
        screen.blit(message_surf, message_rect)

        # スコアを右寄せで表示
        b, w = self.board.count_stones()
        score_text = f"黒(あなた):{b}  白(CPU):{w}"
        score_surf = font.render(score_text, True, FONT_COLOR)
        score_rect = score_surf.get_rect(centery=ui_bar_rect.centery, right=WIDTH - 20)
        screen.blit(score_surf, score_rect)
        
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


if __name__ == "__main__":
    game = Game()
    game.run()