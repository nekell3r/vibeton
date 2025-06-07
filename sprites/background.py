import pygame
import random
from config import SCREEN_WIDTH, WINDOW_COLOR, DARK_GREY

class BackgroundElement:
    def __init__(self, y, height, min_width, max_width, color_palette, speed_factor, z_order):
        self.base_y = y
        self.height_variation = height * 0.3
        self.current_height = height + random.uniform(-self.height_variation, self.height_variation)

        self.rect = pygame.Rect(random.randint(0, SCREEN_WIDTH),
                                self.base_y - int(self.current_height),
                                random.randint(min_width, max_width),
                                int(self.current_height))
        self.color = random.choice(color_palette)
        self.speed_factor = speed_factor
        self.z_order = z_order
        self.has_windows = random.random() < 0.7

    def update(self, world_speed_param, dt):
        self.rect.x -= world_speed_param * self.speed_factor
        if self.rect.right < 0:
            self.rect.left = SCREEN_WIDTH

            min_w_candidate_float = self.rect.width // 1.5
            potential_min_w_float = min_w_candidate_float if min_w_candidate_float > 20 else 20.0

            max_w_candidate_float = self.rect.width * 1.5
            potential_max_w_float = max_w_candidate_float if max_w_candidate_float < 250 else 250.0

            final_min_w = int(potential_min_w_float)
            final_max_w = int(potential_max_w_float)

            if final_min_w > final_max_w:
                final_max_w = final_min_w

            self.rect.width = random.randint(final_min_w, final_max_w)

            self.current_height = self.rect.height + random.uniform(-self.height_variation, self.height_variation)
            self.current_height = max(30.0, min(self.current_height, self.base_y * 0.8))
            self.rect.height = int(self.current_height)
            self.rect.top = self.base_y - self.rect.height

    def draw(self, surface, offset_x=0, offset_y=0):
        draw_rect = self.rect.move(offset_x, offset_y)
        pygame.draw.rect(surface, self.color, draw_rect)

        darker_color = tuple(max(0, c - 20) for c in self.color)
        pygame.draw.line(surface, darker_color, draw_rect.topleft, draw_rect.bottomleft, 3)
        pygame.draw.line(surface, darker_color, draw_rect.topleft, draw_rect.topright, 3)

        if self.has_windows and self.rect.width > 20 and self.rect.height > 20:
            win_size_w = max(5, int(self.rect.width * 0.15))
            win_size_h = max(5, int(self.rect.height * 0.1))
            gap_w = max(3, int(win_size_w * 0.5))
            gap_h = max(3, int(win_size_h * 0.5))

            num_x = int((self.rect.width - gap_w) / (win_size_w + gap_w))
            num_y = int((self.rect.height - gap_h) / (win_size_h + gap_h))

            if num_x > 0 and num_y > 0:
                for r_idx in range(num_y):
                    for c_idx in range(num_x):
                        win_x = draw_rect.left + gap_w + c_idx * (win_size_w + gap_w)
                        win_y = draw_rect.top + gap_h + r_idx * (win_size_h + gap_h)
                        if random.random() < 0.6:
                            pygame.draw.rect(surface, WINDOW_COLOR, (win_x, win_y, win_size_w, win_size_h)) 