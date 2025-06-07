import pygame
import random
import math
from config import (SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_COLOR, DARK_GREY, GROUND_COLOR_TOP,
                   GROUND_COLOR_BOTTOM, WEATHER_TYPES, LANE_YS, PLAYER_SIZE)

class WeatherSystem:
    def __init__(self):
        self.current_weather = "clear"
        self.next_weather = None
        self.transition_progress = 1.0  # 1.0 means no transition
        self.weather_timer = 0
        self.weather_duration = random.randint(*WEATHER_TYPES["clear"]["duration"])
        self.rain_drops = []
        self.snow_flakes = []  # Список для хранения снежинок
        self.max_rain_drops = 350
        self.max_snow_flakes = 400  # Сделал больше для гуще
        # --- Для ступенчатого снега ---
        self.snow_level = 0  # 0 - нет, 1 - немного, 2 - максимум
        self.snow_stage_timer = 0
        self.snow_stage_target = 0
        # --- Кэш для статичного снега на земле ---
        self._snow_ground_cache = {}
        self._snow_ground_cache_params = {}
        
    def get_static_snow_ground(self, ground_height, screen_width):
        key = (self.snow_level, ground_height, screen_width)
        if key in self._snow_ground_cache:
            return self._snow_ground_cache[key]
        # Генерируем поверхность снега
        snow_surface = pygame.Surface((screen_width, ground_height), pygame.SRCALPHA)
        snow_level = self.snow_level
        if snow_level > 0:
            alpha = 120 if snow_level == 1 else 230
            snow_surface.fill((255, 255, 255, alpha))
            snow_detail = pygame.Surface((screen_width, ground_height), pygame.SRCALPHA)
            n_snow = 40 if snow_level == 1 else 100
            for _ in range(n_snow):
                x = random.randint(0, screen_width)
                y = random.randint(0, ground_height)
                size = random.randint(15, 30) if snow_level == 1 else random.randint(30, 60)
                a = random.randint(60, 120) if snow_level == 1 else random.randint(150, 255)
                pygame.draw.circle(snow_detail, (255, 255, 255, a), (x, y), size)
            n_spark = 60 if snow_level == 1 else 300
            for _ in range(n_spark):
                x = random.randint(0, screen_width)
                y = random.randint(0, ground_height)
                size = random.randint(1, 2) if snow_level == 1 else random.randint(1, 3)
                a = random.randint(80, 120) if snow_level == 1 else random.randint(200, 255)
                pygame.draw.circle(snow_detail, (255, 255, 255, a), (x, y), size)
            snow_surface.blit(snow_detail, (0, 0))
        self._snow_ground_cache[key] = snow_surface
        return snow_surface

    def clear_snow_ground_cache(self):
        self._snow_ground_cache = {}

    def update(self, dt):
        self.weather_timer += dt
        
        # --- Новый стабильный дождь ---
        if WEATHER_TYPES[self.current_weather]["rain_chance"] > 0:
            need = int(self.max_rain_drops * WEATHER_TYPES[self.current_weather]["rain_chance"]) - len(self.rain_drops)
            if need > 0:
                for _ in range(min(2, need)):
                    self.rain_drops.append({
                        'x': random.randint(0, SCREEN_WIDTH),
                        'y': random.randint(-50, 0),
                        'speed': random.uniform(450, 650),
                        'length': random.randint(10, 20)
                    })
            # Не очищаем rain_drops полностью при смене погоды
        else:
            # Плавно уменьшаем количество капель, удаляя по 10 за кадр
            self.rain_drops = self.rain_drops[10:] if len(self.rain_drops) > 10 else []
        
        # --- Новый стабильный снег ---
        if WEATHER_TYPES[self.current_weather]["snow_chance"] > 0:
            need = int(self.max_snow_flakes * WEATHER_TYPES[self.current_weather]["snow_chance"]) - len(self.snow_flakes)
            if need > 0:
                for _ in range(min(2, need)):
                    self.snow_flakes.append({
                        'x': random.randint(0, SCREEN_WIDTH),
                        'y': random.randint(-50, 0),
                        'speed_y': random.uniform(80, 130),
                        'speed_x': random.uniform(-20, 20),
                        'size': random.uniform(2, 4),
                        'angle': random.uniform(0, 360),
                        'spin': random.uniform(-90, 90)
                    })
        else:
            # Плавно уменьшаем количество снежинок, удаляя по 12 за кадр
            self.snow_flakes = self.snow_flakes[12:] if len(self.snow_flakes) > 12 else []
        
        # Обновляем существующие капли
        active_drops = []
        for drop in self.rain_drops:
            drop['y'] += drop['speed'] * dt
            if drop['y'] < SCREEN_HEIGHT:
                active_drops.append(drop)
            else:
                if random.random() < WEATHER_TYPES[self.current_weather]["rain_chance"]:
                    drop['y'] = random.randint(-50, 0)
                    drop['x'] = random.randint(0, SCREEN_WIDTH)
                    active_drops.append(drop)
        self.rain_drops = active_drops

        # Обновляем существующие снежинки
        active_flakes = []
        for flake in self.snow_flakes:
            flake['y'] += flake['speed_y'] * dt
            flake['x'] += flake['speed_x'] * dt
            flake['angle'] += flake['spin'] * dt
            if flake['y'] < SCREEN_HEIGHT and 0 <= flake['x'] <= SCREEN_WIDTH:
                active_flakes.append(flake)
            else:
                if random.random() < WEATHER_TYPES[self.current_weather]["snow_chance"]:
                    flake['y'] = random.randint(-50, 0)
                    flake['x'] = random.randint(0, SCREEN_WIDTH)
                    active_flakes.append(flake)
        self.snow_flakes = active_flakes
        
        # Смена погоды
        if self.weather_timer >= self.weather_duration:
            if self.next_weather is None:
                # Определяем следующую погоду в правильном порядке
                if self.current_weather == "clear":
                    self.next_weather = "sunset"
                elif self.current_weather == "sunset":
                    self.next_weather = "night"
                elif self.current_weather == "night":
                    self.next_weather = "snowy"
                elif self.current_weather in ["rainy", "snowy"]:
                    self.next_weather = "sunrise"
                elif self.current_weather == "sunrise":
                    self.next_weather = "clear"
                self.transition_progress = 0.0
            
            if self.transition_progress < 1.0:
                self.transition_progress = min(1.0, self.transition_progress + dt * 0.5)
                if self.transition_progress >= 1.0:
                    self.current_weather = self.next_weather
                    self.next_weather = None
                    self.weather_timer = 0
                    self.weather_duration = random.randint(*WEATHER_TYPES[self.current_weather]["duration"])
        
        # --- Логика ступенчатого снега ---
        # При переходе к snowy начинаем накапливать снег
        if self.current_weather == "snowy":
            if self.snow_stage_target != 2:
                self.snow_stage_target = 2
                self.snow_stage_timer = 0
            if self.snow_level < self.snow_stage_target:
                self.snow_stage_timer += dt
                if self.snow_stage_timer > 2.0:
                    self.snow_level += 1
                    self.snow_stage_timer = 0
                    self.clear_snow_ground_cache()
        # При переходе к sunrise начинаем таять снег
        elif self.current_weather == "sunrise":
            if self.snow_stage_target != 0:
                self.snow_stage_target = 0
                self.snow_stage_timer = 0
            if self.snow_level > self.snow_stage_target:
                self.snow_stage_timer += dt
                if self.snow_stage_timer > 2.0:
                    self.snow_level -= 1
                    self.snow_stage_timer = 0
                    self.clear_snow_ground_cache()
        # Если не снег и не рассвет — сбрасываем снег
        elif self.current_weather not in ["snowy", "sunrise"]:
            if self.snow_level != 0:
                self.snow_level = 0
                self.clear_snow_ground_cache()
            self.snow_stage_target = 0
            self.snow_stage_timer = 0
    
    def get_current_sky_colors(self):
        current = WEATHER_TYPES[self.current_weather]
        if self.next_weather is None or self.transition_progress >= 1.0:
            return current["sky_top"], current["sky_bottom"]
        
        next_weather = WEATHER_TYPES[self.next_weather]
        t = self.transition_progress
        
        sky_top = tuple(int(current["sky_top"][i] * (1 - t) + next_weather["sky_top"][i] * t) for i in range(3))
        sky_bottom = tuple(int(current["sky_bottom"][i] * (1 - t) + next_weather["sky_bottom"][i] * t) for i in range(3))
        
        return sky_top, sky_bottom
    
    def draw_weather(self, surface, offset_x=0, offset_y=0):
        # Отрисовка дождя
        for drop in self.rain_drops:
            end_y = drop['y'] + drop['length']
            pygame.draw.line(surface, (200, 200, 255),
                           (drop['x'] + offset_x, drop['y'] + offset_y),
                           (drop['x'] + offset_x - 2, end_y + offset_y), 2)
        
        # Отрисовка снега
        for flake in self.snow_flakes:
            x = flake['x'] + offset_x
            y = flake['y'] + offset_y
            size = flake['size']
            angle = flake['angle']
            
            # Рисуем снежинку как звездочку
            for i in range(4):
                rot_angle = angle + i * 45
                rad_angle = math.radians(rot_angle)
                end_x = x + math.cos(rad_angle) * size
                end_y = y + math.sin(rad_angle) * size
                pygame.draw.line(surface, (255, 255, 255),
                               (x, y), (end_x, end_y), 1)

class BackgroundElement:
    def __init__(self, y, height, min_width, max_width, color_palette, speed_factor, z_order):
        self.base_y = y
        self.height_variation = height * 0.3
        self.current_height = height + random.uniform(-self.height_variation, self.height_variation)
        self.current_height = max(30.0, min(self.current_height, self.base_y * 0.8))
        ground_height = int(LANE_YS[0] * 0.3)
        max_building_height = self.base_y - ground_height
        self.current_height = min(self.current_height, max_building_height)
        self.rect = pygame.Rect(random.randint(0, SCREEN_WIDTH),
                                self.base_y - int(self.current_height),
                                random.randint(min_width, max_width),
                                int(self.current_height))
        self.color = random.choice(color_palette)
        self.speed_factor = speed_factor
        self.z_order = z_order
        self.has_windows = random.random() < 0.7
        self.snow_height = random.randint(5, 10)
        # --- Кэш для статичных снежных шапок ---
        self._snow_caps = {}
        for snow_level in [1, 2]:
            self._snow_caps[snow_level] = self._generate_snow_cap(snow_level)

    def _generate_snow_cap(self, snow_level):
        width = self.rect.width
        height = self.snow_height + 5
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        # Генерируем форму шапки один раз
        points = [
            (0, self.snow_height),
            (random.randint(2, 5), int(self.snow_height * 0.5)),
            (width // 2 + random.randint(-3, 3), int(self.snow_height * 0.2)),
            (width - random.randint(2, 5), int(self.snow_height * 0.5)),
            (width, self.snow_height)
        ]
        if snow_level == 1:
            snow_color = (240, 240, 250, 120)
            shrink = 0.5
            points = [(x, int(y + self.snow_height * (1 - shrink))) for (x, y) in points]
        else:
            snow_color = (240, 240, 250, 230)
        pygame.draw.polygon(surf, snow_color, points)
        if snow_level == 2:
            pygame.draw.line(surf, (200, 200, 210), points[0], points[-1], 2)
        return surf

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

            # Генерируем новую высоту здания с учетом вариации
            base_height = self.rect.height
            self.current_height = base_height + random.uniform(-self.height_variation, self.height_variation)
            self.current_height = max(30.0, min(self.current_height, self.base_y * 0.8))
            
            # Ограничиваем высоту здания, чтобы оно не выходило за верхнюю границу земли
            ground_height = int(LANE_YS[0] * 0.3)  # Такая же формула как в draw_ground
            max_building_height = self.base_y - ground_height
            self.current_height = min(self.current_height, max_building_height)
            
            self.rect.height = int(self.current_height)
            self.rect.top = self.base_y - self.rect.height

    def draw(self, surface, offset_x=0, offset_y=0, weather_system=None):
        draw_rect = self.rect.move(offset_x, offset_y)
        pygame.draw.rect(surface, self.color, draw_rect)
        darker_color = tuple(max(0, c - 20) for c in self.color)
        pygame.draw.line(surface, darker_color, draw_rect.topleft, draw_rect.bottomleft, 3)
        pygame.draw.line(surface, darker_color, draw_rect.topleft, draw_rect.topright, 3)
        # Статичные снежные шапки
        if weather_system and hasattr(weather_system, 'snow_level') and weather_system.snow_level > 0:
            snow_cap = self._snow_caps.get(weather_system.snow_level)
            if snow_cap:
                surface.blit(snow_cap, (draw_rect.left, draw_rect.top - self.snow_height))

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

def draw_ground(surface, offset_x=0, offset_y=0, weather_system=None):
    # Рисуем основную землю до дороги
    road_rect_y = LANE_YS[0] - PLAYER_SIZE[1] * 0.8
    ground_height = int(road_rect_y * 0.6)  # Земля занимает 60% пространства до дороги
    ground_y = int(road_rect_y - ground_height)  # Начинаем от дороги вверх
    
    # Создаем поверхность для земли
    ground_surface = pygame.Surface((SCREEN_WIDTH, ground_height), pygame.SRCALPHA)
    
    # Градиент земли
    for y in range(ground_height):
        progress = y / ground_height
        color = (
            int(GROUND_COLOR_TOP[0] * (1 - progress) + GROUND_COLOR_BOTTOM[0] * progress),
            int(GROUND_COLOR_TOP[1] * (1 - progress) + GROUND_COLOR_BOTTOM[1] * progress),
            int(GROUND_COLOR_TOP[2] * (1 - progress) + GROUND_COLOR_BOTTOM[2] * progress)
        )
        pygame.draw.line(ground_surface, color, (0, y), (SCREEN_WIDTH, y))

    # Ступенчатый снег на земле
    snow_level = getattr(weather_system, 'snow_level', 0) if weather_system else 0
    if snow_level > 0 and weather_system:
        snow_surface = weather_system.get_static_snow_ground(ground_height, SCREEN_WIDTH)
        ground_surface.blit(snow_surface, (0, 0))
    else:
        # Рисуем статичную траву (используем seed для одинаковой генерации)
        random.seed(42)  # Фиксированный seed для повторяемости
        grid_size = 40  # Увеличили размер ячейки
        for grid_x in range(0, SCREEN_WIDTH, grid_size):
            for grid_y in range(0, ground_height, grid_size):
                if random.random() < 0.7:  # 70% шанс травы в каждой ячейке
                    x = grid_x + random.randint(0, grid_size//2)
                    y = grid_y + random.randint(0, grid_size//2)
                    
                    num_blades = random.randint(2, 3)
                    for _ in range(num_blades):
                        grass_height = random.randint(8, 15)  # Увеличили высоту травы
                        bend = random.randint(-3, 3)
                        color_variation = random.randint(-10, 10)
                        grass_color = tuple(max(0, min(255, c + color_variation)) for c in GROUND_COLOR_TOP)
                        
                        control_point = (x + bend, y - grass_height/2)
                        end_point = (x + bend*1.5, y - grass_height)
                        
                        points = [(x, y), control_point, end_point]
                        pygame.draw.lines(ground_surface, grass_color, False, points, 2)
                
                # 30% шанс камней
                elif random.random() < 0.3:
                    x = grid_x + random.randint(0, grid_size//2)
                    y = grid_y + random.randint(0, grid_size//2)
                    size = random.randint(3, 7)
                    color_variation = random.randint(-30, -10)
                    stone_color = tuple(max(0, min(255, c + color_variation)) for c in GROUND_COLOR_BOTTOM)
                    
                    points = []
                    num_points = random.randint(6, 8)
                    
                    for i in range(num_points):
                        angle = 2 * math.pi * i / num_points
                        dist = size + random.randint(-1, 1)
                        point_x = x + math.cos(angle) * dist
                        point_y = y + math.sin(angle) * dist
                        points.append((point_x, point_y))
                    
                    if len(points) >= 3:
                        pygame.draw.polygon(ground_surface, stone_color, points)
                        highlight_pos = (x + random.randint(-1, 1), y + random.randint(-1, 1))
                        pygame.draw.circle(ground_surface, tuple(min(255, c + 40) for c in stone_color), highlight_pos, 1)
        random.seed()  # Сбрасываем seed
    
    # Отрисовываем всю землю разом
    surface.blit(ground_surface, (offset_x, ground_y + offset_y)) 