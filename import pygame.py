import pygame
import sys

# --- 定数 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# --- ゲームステート ---
STATE_TITLE = 0
STATE_IN_GAME = 1

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("オセロゲーム")
    font = pygame.font.Font(None, 80) # フォントの読み込み
    small_font = pygame.font.Font(None, 40)

    # BGMの読み込みと再生
    try:
        pygame.mixer.music.load("your_bgm.mp3")  # ここに音楽ファイル名を入れる
        pygame.mixer.music.play(-1)  # -1でループ再生
    except pygame.error as e:
        print(f"音楽ファイルを読み込めませんでした: {e}")

    game_state = STATE_TITLE # 初期状態はタイトル画面

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # --- 入力処理 ---
            if game_state == STATE_TITLE:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_s: # Sキーが押されたらゲーム開始
                        game_state = STATE_IN_GAME

        # --- 描画処理 ---
        screen.fill(BLACK) # 背景を黒で塗りつぶし

        if game_state == STATE_TITLE:
            draw_title_screen(screen, font, small_font)
        elif game_state == STATE_IN_GAME:
            # ここにオセロのゲーム本体の描画処理を書く
            draw_game_screen(screen) # 仮の関数

        pygame.display.flip() # 画面を更新

def draw_title_screen(screen, font, small_font):
    """タイトル画面を描画する関数"""
    title_text = font.render("Othello Game", True, WHITE)
    start_text = small_font.render("Press 'S' to Start", True, WHITE)

    # テキストの位置を計算
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 50))
    start_rect = start_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 50))

    # テキストを描画
    screen.blit(title_text, title_rect)
    screen.blit(start_text, start_rect)

def draw_game_screen(screen):
    """ゲーム画面を描画する仮の関数"""
    font = pygame.font.Font(None, 50)
    text = font.render("Game in Progress...", True, WHITE)
    rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
    screen.blit(text, rect)

if __name__ == '__main__':
    main()