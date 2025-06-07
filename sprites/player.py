import pygame
import random
import math
from config import (PLAYER_SIZE, PLAYER_START_X, LANE_YS, BLUE_PLAYER,
                   BLACK)
from utils.particles import Particle

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.base_width, self.base_height = PLAYER_SIZE
        self.image_buffer = 5
        self.image = pygame.Surface((self.base_width + self.image_buffer * 2, self.base_height + self.image_buffer * 2),
                                    pygame.SRCALPHA)
        self.rect = self.image.get_rect(midbottom=(PLAYER_START_X, LANE_YS[1]))
        
        # Создаем отдельный rect для коллизий, который всегда остается на полосе
        self.collision_rect = self.rect.copy()

        self.current_lane_index = 1
        self.is_jumping = False
        self.jump_power = -30
        self.gravity = 0.4
        self.y_velocity = 0
        self.jump_offset = 0
        self.can_collide = True

        self.base_y_on_lane = LANE_YS[self.current_lane_index]
        self.anim_y_offset = 0

        self.jetpack_timer = 0
        self.anim_timer = random.uniform(0, 2 * math.pi)

        self.current_tilt = 0
        self.target_tilt = 0

        self.draw_player_shape()

    def draw_player_shape(self):
        self.image.fill((0, 0, 0, 0))

        player_drawing_surf = pygame.Surface((self.base_width, self.base_height), pygame.SRCALPHA)
        player_drawing_surf.fill((0, 0, 0, 0))

        main_color = BLUE_PLAYER
        highlight_color = tuple(min(255, c + 40) for c in main_color)
        shadow_color = tuple(max(0, c - 30) for c in main_color)
        detail_color_dark = (40, 60, 100)
        detail_color_light = (150, 180, 240)
        eye_base_color = (220, 255, 255)

        body_height_ratio = 0.80
        body_y_start = self.base_height * (1 - body_height_ratio)

        body_points = [
            (self.base_width * 0.1, body_y_start),
            (self.base_width * 0.9, body_y_start),
            (self.base_width, self.base_height * 0.95),
            (self.base_width * 0.7, self.base_height),
            (self.base_width * 0.3, self.base_height),
            (0, self.base_height * 0.95)
        ]
        pygame.draw.polygon(player_drawing_surf, main_color, body_points)
        pygame.draw.polygon(player_drawing_surf, shadow_color, body_points, 2)

        body_highlight_rect = pygame.Rect(self.base_width * 0.2, body_y_start + 2, self.base_width * 0.6,
                                          self.base_height * 0.15)
        pygame.draw.ellipse(player_drawing_surf, highlight_color, body_highlight_rect)

        head_height = self.base_height * 0.35
        head_width = self.base_width * 0.8
        head_x = (self.base_width - head_width) / 2
        head_y = 0

        head_rect = pygame.Rect(head_x, head_y, head_width, head_height)
        pygame.draw.ellipse(player_drawing_surf, detail_color_light, head_rect)
        pygame.draw.ellipse(player_drawing_surf, shadow_color, head_rect, 2)

        eye_anim_scale = 0.9 + 0.1 * (math.sin(self.anim_timer * 2.5) * 0.5 + 0.5)
        eye_width = head_width * 0.6 * eye_anim_scale
        eye_height = head_height * 0.4 * eye_anim_scale
        eye_x = (self.base_width - eye_width) / 2
        eye_y = head_y + head_height * 0.25
        eye_rect = pygame.Rect(eye_x, eye_y, eye_width, eye_height)

        eye_brightness = 0.8 + 0.2 * (math.sin(self.anim_timer * 1.5 + math.pi / 2) * 0.5 + 0.5)
        current_eye_color = tuple(int(c * eye_brightness) for c in eye_base_color)
        pygame.draw.ellipse(player_drawing_surf, current_eye_color, eye_rect)
        pygame.draw.ellipse(player_drawing_surf, detail_color_dark, eye_rect, 1)

        panel_width = self.base_width * 0.15
        panel_height = self.base_height * 0.4
        panel_y = body_y_start + self.base_height * 0.1
        pygame.draw.rect(player_drawing_surf, shadow_color,
                         (self.base_width * 0.05, panel_y, panel_width, panel_height), border_radius=3)
        pygame.draw.rect(player_drawing_surf, shadow_color,
                         (self.base_width * 0.80, panel_y, panel_width, panel_height), border_radius=3)

        nozzle_radius = self.base_width * 0.08
        nozzle_y = self.base_height - nozzle_radius * 0.8
        pygame.draw.circle(player_drawing_surf, detail_color_dark, (self.base_width * 0.35, nozzle_y), nozzle_radius)
        pygame.draw.circle(player_drawing_surf, detail_color_dark, (self.base_width * 0.65, nozzle_y), nozzle_radius)

        if self.current_tilt != 0:
            rotated_surf = pygame.transform.rotate(player_drawing_surf, self.current_tilt)
            new_rect = rotated_surf.get_rect(center=(self.image.get_width() / 2, self.image.get_height() / 2))
            self.image.blit(rotated_surf, new_rect)
        else:
            self.image.blit(player_drawing_surf, player_drawing_surf.get_rect(
                center=(self.image.get_width() / 2, self.image.get_height() / 2)))

    def update(self, dt):
        self.anim_timer += dt * 3.5
        tilt_speed_factor = dt * 10
        self.current_tilt += (self.target_tilt - self.current_tilt) * tilt_speed_factor

        if self.is_jumping:
            self.can_collide = False
            self.y_velocity += self.gravity
            self.jump_offset += self.y_velocity

            # Ограничиваем максимальную высоту прыжка
            if self.jump_offset < -180:
                self.jump_offset = -180
                self.y_velocity = 0

            # Наклон во время прыжка
            if self.y_velocity < 0:
                self.target_tilt = -20
            else:
                self.target_tilt = 15

            # Обновляем позицию относительно текущей полосы
            self.rect.bottom = self.base_y_on_lane + self.jump_offset

            # Проверяем приземление
            if self.jump_offset >= 0:
                self.jump_offset = 0
                self.is_jumping = False
                self.y_velocity = 0
                self.target_tilt = 0
                self.can_collide = True  # Включаем коллизии после приземления
                return [Particle(
                    self.rect.centerx + random.uniform(-self.base_width / 2.5, self.base_width / 2.5),
                    self.rect.bottom,
                    (160, 160, 160), random.uniform(2.5, 5),
                    random.uniform(-50, 50), random.uniform(-60, -25), 280, 0.45
                ) for _ in range(10)]

            # Частицы джетпака
            self.jetpack_timer -= dt
            if self.jetpack_timer <= 0:
                particles = []
                for i in [-1, 1]:
                    start_x = self.rect.centerx + i * (self.base_width * 0.2)
                    start_y = self.rect.bottom - self.image_buffer
                    particles.append(Particle(
                        start_x, start_y,
                        random.choice([(255, 100, 0), (255, 150, 30), (255, 200, 80)]),
                        random.uniform(4, 7),
                        random.uniform(-20, 20),
                        random.uniform(50, 100),
                        -50, 0.3
                    ))
                self.jetpack_timer = 0.02
                return particles
        else:
            self.can_collide = True  # Включаем коллизии в обычном состоянии
            self.anim_y_offset = math.sin(self.anim_timer) * 2.5
            self.rect.bottom = self.base_y_on_lane + self.anim_y_offset
            self.target_tilt = math.sin(self.anim_timer * 0.8) * 4

        self.rect.top = max(0, self.rect.top)
        self.draw_player_shape()
        return []

    def change_lane(self, direction):
        if not self.is_jumping:
            prev_lane_index = self.current_lane_index
            self.current_lane_index = max(0, min(len(LANE_YS) - 1, self.current_lane_index + direction))
            if prev_lane_index != self.current_lane_index:
                self.base_y_on_lane = LANE_YS[self.current_lane_index]
                self.rect.bottom = self.base_y_on_lane + self.anim_y_offset
                self.collision_rect.midbottom = (self.rect.centerx, self.base_y_on_lane)
                self.target_tilt = direction * 18

    def jump(self):
        if not self.is_jumping:
            self.is_jumping = True
            self.y_velocity = self.jump_power
            self.jump_offset = 0
            self.jetpack_timer = 0.02
            self.target_tilt = -20
            self.can_collide = False  # Отключаем коллизии при начале прыжка

            return [Particle(
                self.rect.centerx + random.uniform(-10, 10),
                self.rect.bottom - self.image_buffer,
                random.choice([(255, 220, 120), (255, 250, 180), (255, 255, 0)]),
                random.uniform(4, 8),
                random.uniform(-40, 40),
                random.uniform(70, 120),
                -120, 0.6
            ) for _ in range(20)]
        return [] 