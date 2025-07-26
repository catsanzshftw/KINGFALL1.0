import pygame
import random
import math
import numpy as np

# --- KINGFALL EXECUTE ---

# --- Game Constants ---
WIDTH, HEIGHT = 960, 720
PADDLE_WIDTH, PADDLE_HEIGHT = 20, 120
BALL_RADIUS = 15
PADDLE_VELOCITY = 8
AI_PADDLE_VELOCITY = 8 # AI can have a different speed
WINNING_SCORE = 5

# --- Colors ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

# --- Pygame Initialization ---
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("KINGFALL PONG: PLAYER vs AI")
FONT = pygame.font.SysFont("monospace", 50, bold=True)
GAMEOVER_FONT = pygame.font.SysFont("monospace", 80, bold=True)
PROMPT_FONT = pygame.font.SysFont("monospace", 40)


# --- NES-style Sound Engine ---
def generate_square_wave(frequency, duration, volume=0.1):
    sample_rate = pygame.mixer.get_init()[0]
    period = int(sample_rate / frequency)
    amplitude = 2**15 - 1
    num_samples = int(duration * sample_rate)
    
    samples = np.zeros(num_samples, dtype=np.int16)
    for i in range(num_samples):
        if (i // (period / 2)) % 2 == 0:
            samples[i] = amplitude
        else:
            samples[i] = -amplitude
            
    samples = (samples * volume).astype(np.int16)
    return pygame.mixer.Sound(buffer=samples)

# --- Sound Effects ---
PADDLE_HIT_SOUND = generate_square_wave(440.0, 0.05)
WALL_HIT_SOUND = generate_square_wave(220.0, 0.05)
SCORE_SOUND = generate_square_wave(880.0, 0.2)


class Paddle:
    def __init__(self, x, y, width, height, color, velocity):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.velocity = velocity

    def draw(self, win):
        pygame.draw.rect(win, self.color, self.rect)

    def move(self, up=True):
        if up:
            self.rect.y -= self.velocity
        else:
            self.rect.y += self.velocity
        
        self.rect.y = max(0, self.rect.y)
        self.rect.y = min(HEIGHT - self.rect.height, self.rect.y)

    def ai_move(self, ball):
        # AI logic: move paddle to intercept the ball
        if self.rect.centery < ball.rect.centery:
            self.move(up=False)
        if self.rect.centery > ball.rect.centery:
            self.move(up=True)


class Ball:
    def __init__(self, x, y, radius, color):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)
        self.x_vel = PADDLE_VELOCITY * random.choice([1, -1])
        self.y_vel = 0

    def draw(self, win):
        pygame.draw.ellipse(win, self.color, self.rect)

    def move(self):
        self.x += self.x_vel
        self.y += self.y_vel
        self.rect.x = self.x
        self.rect.y = self.y

    def reset(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.x_vel *= -1 # Serve to the player who just lost the point
        self.y_vel = random.uniform(-2, 2)


def handle_collision(ball, left_paddle, right_paddle):
    if ball.rect.top <= 0 or ball.rect.bottom >= HEIGHT:
        ball.y_vel *= -1
        WALL_HIT_SOUND.play()

    if ball.x_vel < 0:
        if left_paddle.rect.colliderect(ball.rect) and ball.rect.left <= left_paddle.rect.right:
            ball.x_vel *= -1
            ball.rect.left = left_paddle.rect.right
            middle_y = left_paddle.rect.centery
            difference_in_y = middle_y - ball.rect.centery
            reduction_factor = (PADDLE_HEIGHT / 2) / PADDLE_VELOCITY
            y_vel = difference_in_y / reduction_factor
            ball.y_vel = -y_vel
            PADDLE_HIT_SOUND.play()
    else:
        if right_paddle.rect.colliderect(ball.rect) and ball.rect.right >= right_paddle.rect.left:
            ball.x_vel *= -1
            ball.rect.right = right_paddle.rect.left
            middle_y = right_paddle.rect.centery
            difference_in_y = middle_y - ball.rect.centery
            reduction_factor = (PADDLE_HEIGHT / 2) / AI_PADDLE_VELOCITY
            y_vel = difference_in_y / reduction_factor
            ball.y_vel = -y_vel
            PADDLE_HIT_SOUND.play()


def draw_game_state(win, paddles, ball, left_score, right_score):
    win.fill(BLACK)
    left_score_text = FONT.render(f"{left_score}", 1, WHITE)
    right_score_text = FONT.render(f"{right_score}", 1, WHITE)
    win.blit(left_score_text, (WIDTH // 4 - left_score_text.get_width() // 2, 20))
    win.blit(right_score_text, (WIDTH * (3 / 4) - right_score_text.get_width() // 2, 20))
    for paddle in paddles:
        paddle.draw(win)
    ball.draw(win)
    for i in range(10, HEIGHT, HEIGHT // 20):
        if i % 2 == 1:
            continue
        pygame.draw.rect(win, WHITE, (WIDTH // 2 - 5, i, 10, HEIGHT // 20))
    pygame.display.update()


def draw_game_over(win, winner_text):
    win.fill(BLACK)
    title_text = GAMEOVER_FONT.render("GAME OVER", 1, WHITE)
    winner_display = FONT.render(winner_text, 1, WHITE)
    restart_text = PROMPT_FONT.render("Y = RESTART", 1, GREEN)
    quit_text = PROMPT_FONT.render("N = QUIT", 1, RED)
    
    win.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 4))
    win.blit(winner_display, (WIDTH // 2 - winner_display.get_width() // 2, HEIGHT // 2 - winner_display.get_height()))
    win.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT * 0.7))
    win.blit(quit_text, (WIDTH // 2 - quit_text.get_width() // 2, HEIGHT * 0.8))
    pygame.display.update()


def main():
    run = True
    game_over = False
    clock = pygame.time.Clock()

    player_paddle = Paddle(10, HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT, BLUE, PADDLE_VELOCITY)
    ai_paddle = Paddle(WIDTH - 10 - PADDLE_WIDTH, HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT, RED, AI_PADDLE_VELOCITY)
    ball = Ball(WIDTH // 2, HEIGHT // 2, BALL_RADIUS, WHITE)

    player_score = 0
    ai_score = 0
    winner_text = ""

    while run:
        clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            
            if game_over and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y:
                    player_score = 0
                    ai_score = 0
                    ball.reset()
                    player_paddle.rect.y = HEIGHT // 2 - PADDLE_HEIGHT // 2
                    ai_paddle.rect.y = HEIGHT // 2 - PADDLE_HEIGHT // 2
                    winner_text = ""
                    game_over = False
                elif event.key == pygame.K_n:
                    run = False

        if game_over:
            draw_game_over(WIN, winner_text)
            continue

        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            player_paddle.move(up=True)
        if keys[pygame.K_s]:
            player_paddle.move(up=False)

        # AI Movement
        ai_paddle.ai_move(ball)

        ball.move()
        handle_collision(ball, player_paddle, ai_paddle)

        if ball.rect.left < 0:
            ai_score += 1
            SCORE_SOUND.play()
            ball.reset()
        elif ball.rect.right > WIDTH:
            player_score += 1
            SCORE_SOUND.play()
            ball.reset()

        if player_score >= WINNING_SCORE:
            winner_text = "PLAYER WINS!"
            game_over = True
        elif ai_score >= WINNING_SCORE:
            winner_text = "AI WINS!"
            game_over = True
        
        if not game_over:
            draw_game_state(WIN, [player_paddle, ai_paddle], ball, player_score, ai_score)

    pygame.quit()


if __name__ == '__main__':
    main()
