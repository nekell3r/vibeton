import pygame
import random
import math
from config import (SCREEN_WIDTH, OBSTACLE_BASE_SIZE, BOOSTER_RADIUS,
                   RISK_COLORS, POLICY_COLORS, BLACK, RED, LANE_YS)
from utils.drawing import draw_text, get_font

class MovingObject(pygame.sprite.Sprite):
    def __init__(self, image, world_speed, lane_y_options):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(
            bottomleft=(SCREEN_WIDTH + random.randint(50, 200), random.choice(lane_y_options)))
        self.spawn_world_speed = world_speed

    def update(self, world_speed_param, dt):
        self.rect.x -= world_speed_param
        if self.rect.right < 0:
            self.kill()

class Obstacle(MovingObject):
    def __init__(self, world_speed, risk_type):
        self.risk_type = risk_type
        self.image = self.create_obstacle_surface()
        lane_y = random.choice(LANE_YS)
        super().__init__(self.image, world_speed, [lane_y])
        self.rect.bottom = lane_y

    def create_obstacle_surface(self):
        s = OBSTACLE_BASE_SIZE
        surf = None
        color = RISK_COLORS.get(self.risk_type, RED)

        if self.risk_type == "tree":
            surf = pygame.Surface((s, int(s * 1.4)), pygame.SRCALPHA)
            pygame.draw.rect(surf, color, (s * 0.35, s * 0.6, s * 0.3, s * 0.8))
            pygame.draw.circle(surf, (30, 150, 30), (s * 0.5, s * 0.35), s * 0.35)
            pygame.draw.circle(surf, (40, 160, 40), (s * 0.25, s * 0.5), s * 0.25)
            pygame.draw.circle(surf, (20, 140, 20), (s * 0.75, s * 0.55), s * 0.3)
        elif self.risk_type == "phone":
            surf = pygame.Surface((s * 0.6, s * 0.6), pygame.SRCALPHA)
            pygame.draw.rect(surf, color, (0, 0, s * 0.6, s * 0.6), border_radius=5)
            pygame.draw.rect(surf, (30, 30, 30), (s * 0.05, s * 0.05, s * 0.5, s * 0.3))
            pygame.draw.circle(surf, (60, 60, 60), (s * 0.3, s * 0.5), s * 0.08)
        elif self.risk_type == "accident":
            surf = pygame.Surface((s * 1.5, s * 0.8), pygame.SRCALPHA)
            rect1 = pygame.Rect(0, s * 0.1, s * 0.8, s * 0.6)
            rect2 = pygame.Rect(s * 0.5, 0, s * 0.8, s * 0.6)
            points1 = [(rect1.left, rect1.top + 5), (rect1.right - 10, rect1.top), (rect1.right, rect1.bottom - 5),
                       (rect1.left + 10, rect1.bottom)]
            points2 = [(rect2.left + 5, rect2.top), (rect2.right, rect2.top + 10), (rect2.right - 5, rect2.bottom),
                       (rect2.left, rect2.bottom - 10)]
            pygame.draw.polygon(surf, (200, 50, 50), points1)
            pygame.draw.polygon(surf, (80, 80, 180), points2)
            pygame.draw.polygon(surf, BLACK, points1, 2)
            pygame.draw.polygon(surf, BLACK, points2, 2)
        elif self.risk_type == "bill":
            surf = pygame.Surface((s * 0.8, s * 0.7), pygame.SRCALPHA)
            for i in range(3):
                offset = i * 3
                pygame.draw.rect(surf, (220 - i * 10, 220 - i * 10, 200 - i * 10),
                                 (offset, offset, s * 0.8 - offset * 1.5, s * 0.7 - offset * 1.5))
                pygame.draw.rect(surf, (50, 50, 50), (offset, offset, s * 0.8 - offset * 1.5, s * 0.7 - offset * 1.5), 1)
            for r_idx in range(3):
                pygame.draw.line(surf, (100, 100, 100), (5, 10 + r_idx * 5), (s * 0.8 - 10, 10 + r_idx * 5), 1)

        if surf is None:
            surf = pygame.Surface((s, s), pygame.SRCALPHA)
            surf.fill(color)
            draw_text(surf, self.risk_type[0].upper(), int(s * 0.7), s / 2, s / 2, BLACK, anchor="center")
        return surf

class Booster(MovingObject):
    def __init__(self, world_speed, policy_type):
        self.policy_type = policy_type
        self.base_color = POLICY_COLORS.get(policy_type, (0, 255, 0))
        self.image = pygame.Surface((BOOSTER_RADIUS * 2, BOOSTER_RADIUS * 2), pygame.SRCALPHA)
        self.anim_timer = random.uniform(0, 2 * math.pi)
        self.update_image(0)
        super().__init__(self.image, world_speed, LANE_YS)

    def update_image(self, dt):
        self.anim_timer += dt * 4
        scale_factor = 0.8 + 0.2 * (math.sin(self.anim_timer) * 0.5 + 0.5)
        current_radius = int(BOOSTER_RADIUS * scale_factor)

        self.image.fill((0, 0, 0, 0))
        center = (BOOSTER_RADIUS, BOOSTER_RADIUS)

        glow_color = (*self.base_color, 80)
        pygame.draw.circle(self.image, glow_color, center, current_radius)
        pygame.draw.circle(self.image, self.base_color, center, int(current_radius * 0.8))
        font = get_font(int(current_radius * 0.8), 'Impact')
        text_surf = font.render(self.policy_type[0].upper(), True, BLACK)
        text_rect = text_surf.get_rect(center=center)
        self.image.blit(text_surf, text_rect)

    def update(self, world_speed_param, dt):
        super().update(world_speed_param, dt)
        self.update_image(dt) 