import pygame
import sys

# ==============================
# 定数定義
# ==============================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)


class TitleScreen:
    """タイトル画面を管理するクラス"""

    def __init__(self, screen: pygame.Surface):
        """初期化処理"""
        self.screen = screen
        self.font = pygame.font.Font(None, 80)
        self.small_font = pygame.font.Font(None, 40)

        # タイトルテキスト
        self.title_text = self.font.render("My Game Title", True, WHITE)
        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, -50))

        # スタートメッセージ
        self.start_text = self.small_font.render("Press SPACE to Start", True, BLUE)
        self.start_rect = self.start_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))

        # アニメーション関連変数
        self.target_y = SCREEN_HEIGHT // 2
        self.speed = 2
        self.alpha = 0
        self.alpha_speed = 3
        self.max_alpha = 255
        self.min_alpha = 0
        self.blinking_in = True

        self.running = True

    def animate_title(self) -> None:
        """タイトル文字を中央に移動させるアニメーション"""
        if self.title_rect.centery < self.target_y:
            self.title_rect.centery += self.speed
        elif self.title_rect.centery > self.target_y:
            self.title_rect.centery = self.target_y

    def blink_start_message(self) -> None:
        """スタートメッセージを点滅させる"""
        if self.title_rect.centery != self.target_y:
            return  # タイトルが動いている間は点滅しない

        if self.blinking_in:
            self.alpha += self.alpha_speed
            if self.alpha >= self.max_alpha:
                self.alpha = self.max_alpha
                self.blinking_in = False
        else:
            self.alpha -= self.alpha_speed
            if self.alpha <= self.min_alpha:
                self.alpha = self.min_alpha
                self.blinking_in = True

        # アルファ適用
        self.start_text.set_alpha(self.alpha)
        self.screen.blit(self.start_text, self.start_rect)

    def draw(self) -> None:
        """タイトル画面を描画"""
        self.screen.fill(BLACK)
        self.animate_title()
        self.screen.blit(self.title_text, self.title_rect)
        self.blink_start_message()

    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベント処理（SPACEキーで終了）"""
        if event.type == pygame.QUIT:
            self.running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            print("ゲーム開始！")
            self.running = False  # 次の画面へ遷移予定
        return self.running


def main() -> None:
    """メイン関数"""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("動くタイトル画面")

    title_screen = TitleScreen(screen)
    clock = pygame.time.Clock()

    while title_screen.running:
        for event in pygame.event.get():
            if not title_screen.handle_event(event):
                break

        title_screen.draw()
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
 