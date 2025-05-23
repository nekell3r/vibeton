import pygame
import random
import sys
from typing import List, Dict, Any

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
LANE_WIDTH = 200
BOT_SIZE = 50
OBJECT_SIZE = 40

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)

class GameObject:
    def __init__(self, obj_type: str, lane: int, y: float):
        self.type = obj_type
        self.lane = lane
        self.y = y
        self.rect = pygame.Rect(
            lane * LANE_WIDTH + (LANE_WIDTH - OBJECT_SIZE) // 2,
            y,
            OBJECT_SIZE,
            OBJECT_SIZE
        )

    def update(self, speed: float) -> None:
        self.y += speed
        self.rect.y = self.y

    def draw(self, screen: pygame.Surface) -> None:
        color = RED if self.type == 'risk' else BLUE
        pygame.draw.rect(screen, color, self.rect)

class GameState:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Полис-Бот: Минималка")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 74)
        self.font_small = pygame.font.Font(None, 36)
        self.reset_game()

    def reset_game(self) -> None:
        self.bot_lane = 1  # 0 or 1
        self.shield_active = False
        self.objects: List[GameObject] = []
        self.game_over = False
        self.last_object_time = pygame.time.get_ticks()
        self.object_spawn_delay = 2000  # milliseconds
        self.object_speed = 5

    def handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and self.bot_lane == 1:
                    self.bot_lane = 0
                elif event.key == pygame.K_RIGHT and self.bot_lane == 0:
                    self.bot_lane = 1
                if self.game_over and event.key == pygame.K_SPACE:
                    self.reset_game()
        return True

    def spawn_object(self) -> None:
        current_time = pygame.time.get_ticks()
        if current_time - self.last_object_time > self.object_spawn_delay:
            lane = random.randint(0, 1)
            is_risk = random.choice([True, False])
            self.objects.append(GameObject(
                'risk' if is_risk else 'policy',
                lane,
                -OBJECT_SIZE
            ))
            self.last_object_time = current_time

    def update_objects(self) -> None:
        for obj in self.objects[:]:
            obj.update(self.object_speed)
            if obj.y > SCREEN_HEIGHT:
                self.objects.remove(obj)

    def check_collisions(self) -> None:
        bot_rect = pygame.Rect(
            self.bot_lane * LANE_WIDTH + (LANE_WIDTH - BOT_SIZE) // 2,
            SCREEN_HEIGHT - BOT_SIZE - 20,
            BOT_SIZE,
            BOT_SIZE
        )

        for obj in self.objects[:]:
            if bot_rect.colliderect(obj.rect):
                if obj.type == 'policy':
                    self.shield_active = True
                    self.objects.remove(obj)
                elif obj.type == 'risk':
                    if self.shield_active:
                        self.shield_active = False
                        self.objects.remove(obj)
                    else:
                        self.game_over = True

    def draw(self) -> None:
        self.screen.fill(WHITE)
        
        # Draw lanes
        for i in range(2):
            pygame.draw.rect(self.screen, GRAY, 
                           (i * LANE_WIDTH, 0, LANE_WIDTH, SCREEN_HEIGHT), 2)

        # Draw bot
        bot_color = BLUE if self.shield_active else BLACK
        pygame.draw.rect(self.screen, bot_color,
                        (self.bot_lane * LANE_WIDTH + (LANE_WIDTH - BOT_SIZE) // 2,
                         SCREEN_HEIGHT - BOT_SIZE - 20,
                         BOT_SIZE,
                         BOT_SIZE))

        # Draw objects
        for obj in self.objects:
            obj.draw(self.screen)

        # Draw game over screen
        if self.game_over:
            text = self.font_large.render('Конец игры!', True, BLACK)
            text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
            self.screen.blit(text, text_rect)
            
            restart_text = self.font_small.render('Нажмите ПРОБЕЛ для перезапуска', True, BLACK)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 50))
            self.screen.blit(restart_text, restart_rect)

        pygame.display.flip()

    def run(self) -> None:
        running = True
        while running:
            running = self.handle_events()
            
            if not self.game_over:
                self.spawn_object()
                self.update_objects()
                self.check_collisions()
            
            self.draw()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = GameState()
    game.run() 