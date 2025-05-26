import pygame
import random
import sys
import time
import math  # Для синусоид и других эффектов

# --- Инициализация Pygame ---
pygame.init()
pygame.font.init()

# --- Константы ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE_PLAYER = (60, 120, 220)  # Игрок
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
ORANGE = (255, 165, 0)
GREY = (128, 128, 128)
DARK_GREY = (50, 50, 50)
LIGHT_GREY = (200, 200, 200)

SKY_COLOR_TOP = (100, 150, 255)  # Верхняя часть неба
SKY_COLOR_BOTTOM = (170, 210, 255)  # Нижняя часть неба
BUILDING_COLORS = [(100, 100, 120), (120, 120, 140), (80, 80, 100), (140, 140, 160)]
WINDOW_COLOR = (200, 200, 255, 100)  # Полупрозрачные окна
ROAD_COLOR = (70, 70, 70)
ROAD_LINE_COLOR = (220, 220, 0)
UI_TEXT_COLOR = (230, 230, 230)
UI_BG_COLOR = (30, 30, 30, 180)  # Полупрозрачный фон для UI
TOAST_TEXT_COLOR = WHITE
TOAST_BG_COLOR = (0, 0, 0, 200)

# Параметры игры
LANE_YS = [SCREEN_HEIGHT * 0.58, SCREEN_HEIGHT * 0.73, SCREEN_HEIGHT * 0.88]  # Чуть поднял дороги
PLAYER_START_X = 150
INITIAL_SPEED = 4.5
SPEED_INCREMENT = 0.2
SPEED_INCREMENT_INTERVAL_SEC = 10
GAME_DURATION_SEC = 90
INITIAL_HEALTH = 3

PLAYER_SIZE = (35, 55)  # чуть меньше
OBSTACLE_BASE_SIZE = 50  # Базовый размер для масштабирования
BOOSTER_RADIUS = 20

POLICY_COLORS = {"kasko": GREEN, "dms": CYAN, "property": YELLOW, "travel": MAGENTA}
RISK_COLORS = {"tree": (100, 60, 20), "phone": (100, 100, 110), "accident": RED, "bill": ORANGE}

POLICY_TYPES = list(POLICY_COLORS.keys())
RISK_TYPES = list(RISK_COLORS.keys())
RISK_PROTECTION = {"tree": "property", "phone": "property", "accident": "kasko", "bill": "dms"}
RISK_COSTS = {"tree": 30000, "phone": 15000, "accident": 50000, "bill": 25000}
TIPS_DATA = {
    "tree": f"Имущество от дерева! Экономия: {RISK_COSTS['tree']:,}₽",
    "phone": f"Имущество за телефон! Экономия: {RISK_COSTS['phone']:,}₽",
    "accident": f"КАСКО от аварии! Экономия: {RISK_COSTS['accident']:,}₽",
    "bill": f"ДМС за счет! Экономия: {RISK_COSTS['bill']:,}₽"
}

# --- Глобальные переменные для эффектов ---
screen_shake_amount = 0
screen_shake_timer = 0
particles = []


# --- Вспомогательные функции ---
def get_font(size, font_name_hint=None):
    preferred_fonts = ['Consolas', 'Arial', 'Verdana']  # Предпочтительные шрифты
    if font_name_hint:
        preferred_fonts.insert(0, font_name_hint)

    for font_name in preferred_fonts:
        try:
            found_font_name = pygame.font.match_font(font_name)
            if found_font_name:
                return pygame.font.Font(found_font_name, size)
        except:  # noqa
            continue
    return pygame.font.Font(None, size)  # Fallback на дефолтный шрифт


def draw_text(surface, text, size, x, y, color, font_name_hint=None, anchor="topleft", shadow=False, shadow_color=BLACK,
              shadow_offset=(1, 1)):
    font = get_font(size, font_name_hint)
    text_surface = font.render(text, True, color)
    rect_params = {anchor: (x, y)}
    text_rect = text_surface.get_rect(**rect_params)

    if shadow:
        shadow_surface = font.render(text, True, shadow_color)
        shadow_rect = shadow_surface.get_rect(**rect_params)
        shadow_rect.x += shadow_offset[0]
        shadow_rect.y += shadow_offset[1]
        surface.blit(shadow_surface, shadow_rect)
    surface.blit(text_surface, text_rect)


def draw_rounded_rect(surface, rect, color, corner_radius, alpha=255):
    if corner_radius < 0:
        raise ValueError(f"Corner radius {corner_radius} must be >= 0")

    # Ensure rect dimensions are at least 2*corner_radius or corner_radius will be reduced
    effective_rect_width = rect.width
    effective_rect_height = rect.height

    if effective_rect_width < 1 or effective_rect_height < 1:  # Cannot draw on zero-size rect
        return

    if corner_radius > min(effective_rect_width, effective_rect_height) / 2:
        corner_radius = min(effective_rect_width, effective_rect_height) / 2

    # Make sure corner_radius is not negative after adjustment (e.g. if width/height was 0)
    corner_radius = max(0, corner_radius)

    surf = pygame.Surface(rect.size, pygame.SRCALPHA)

    # Use a temporary color tuple for fill, as TOAST_BG_COLOR might have alpha already
    # and fill doesn't use it directly, Surface.set_alpha handles overall transparency.
    fill_color_rgb = color[:3]

    # Fill the center part
    pygame.draw.rect(surf, fill_color_rgb,
                     (0, corner_radius, effective_rect_width, effective_rect_height - 2 * corner_radius))
    pygame.draw.rect(surf, fill_color_rgb,
                     (corner_radius, 0, effective_rect_width - 2 * corner_radius, effective_rect_height))

    # Draw the circles for corners
    pygame.draw.circle(surf, fill_color_rgb, (corner_radius, corner_radius), corner_radius)
    pygame.draw.circle(surf, fill_color_rgb, (effective_rect_width - corner_radius, corner_radius), corner_radius)
    pygame.draw.circle(surf, fill_color_rgb, (corner_radius, effective_rect_height - corner_radius), corner_radius)
    pygame.draw.circle(surf, fill_color_rgb,
                       (effective_rect_width - corner_radius, effective_rect_height - corner_radius), corner_radius)

    surf.set_alpha(alpha if len(color) == 3 else color[3])  # Use passed alpha or alpha from color
    surface.blit(surf, rect.topleft)


# --- Класс Частиц ---
class Particle:
    def __init__(self, x, y, color, size, speed_x, speed_y, gravity, lifetime):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.gravity = gravity
        self.lifetime = lifetime
        self.life = 0

    def update(self, dt):
        self.life += dt
        if self.life >= self.lifetime:
            return False

        self.speed_y += self.gravity * dt
        self.x += self.speed_x * dt
        self.y += self.speed_y * dt
        self.size = max(1, self.size - 2 * dt)
        return True

    def draw(self, surface, offset_x=0, offset_y=0):
        if self.size >= 1:
            pygame.draw.circle(surface, self.color, (int(self.x + offset_x), int(self.y + offset_y)), int(self.size))


def create_explosion(x, y, color, count=20, base_speed=100, lifetime=0.5, gravity=300):
    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(base_speed * 0.5, base_speed * 1.5)
        speed_x = math.cos(angle) * speed
        speed_y = math.sin(angle) * speed
        size = random.uniform(3, 7)
        p_color = (max(0, min(255, color[0] + random.randint(-20, 20))),
                   max(0, min(255, color[1] + random.randint(-20, 20))),
                   max(0, min(255, color[2] + random.randint(-20, 20))))
        particles.append(Particle(x, y, p_color, size, speed_x, speed_y, gravity, lifetime))


def apply_screen_shake(duration=0.2, intensity=5):
    global screen_shake_timer, screen_shake_amount
    screen_shake_timer = duration
    screen_shake_amount = intensity


# --- Классы Игровых Объектов ---
# ... (остальной код остается прежним) ...

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.base_width, self.base_height = PLAYER_SIZE
        # self.image будет немного больше, чтобы вместить анимации наклона без обрезки
        self.image_buffer = 5  # Дополнительное пространство по краям
        self.image = pygame.Surface((self.base_width + self.image_buffer * 2, self.base_height + self.image_buffer * 2),
                                    pygame.SRCALPHA)
        self.rect = self.image.get_rect(midbottom=(PLAYER_START_X, LANE_YS[1]))

        self.current_lane_index = 1
        self.is_jumping = False
        self.jump_power = -21  # Чуть сильнее прыжок
        self.gravity = 0.95
        self.y_velocity = 0

        self.base_y_on_lane = LANE_YS[self.current_lane_index]  # Y координата низа игрока на текущей полосе
        self.anim_y_offset = 0  # Для анимации "дыхания"

        self.jetpack_timer = 0
        self.anim_timer = random.uniform(0, 2 * math.pi)  # Общий таймер для циклических анимаций

        self.current_tilt = 0  # Текущий угол наклона для плавной анимации
        self.target_tilt = 0  # Целевой угол наклона

        self.draw_player_shape()  # Первоначальная отрисовка

    def draw_player_shape(self):
        self.image.fill((0, 0, 0, 0))  # Очищаем предыдущий кадр

        # Временная поверхность для рисования игрока без наклона
        # Рисуем на ней, потом поворачиваем и копируем на self.image
        player_drawing_surf = pygame.Surface((self.base_width, self.base_height), pygame.SRCALPHA)
        player_drawing_surf.fill((0, 0, 0, 0))

        # --- Цвета ---
        main_color = BLUE_PLAYER
        highlight_color = tuple(min(255, c + 40) for c in main_color)
        shadow_color = tuple(max(0, c - 30) for c in main_color)
        detail_color_dark = (40, 60, 100)
        detail_color_light = (150, 180, 240)
        eye_base_color = (220, 255, 255)

        # --- Корпус ---
        body_height_ratio = 0.80
        body_y_start = self.base_height * (1 - body_height_ratio)

        # Основная форма корпуса (трапеция или скругленный прямоугольник)
        body_points = [
            (self.base_width * 0.1, body_y_start),  # top-left
            (self.base_width * 0.9, body_y_start),  # top-right
            (self.base_width, self.base_height * 0.95),  # bottom-right
            (self.base_width * 0.7, self.base_height),  # bottom-center-right (для "ног")
            (self.base_width * 0.3, self.base_height),  # bottom-center-left
            (0, self.base_height * 0.95)  # bottom-left
        ]
        pygame.draw.polygon(player_drawing_surf, main_color, body_points)
        pygame.draw.polygon(player_drawing_surf, shadow_color, body_points, 2)  # Контур

        # Блик на корпусе
        body_highlight_rect = pygame.Rect(self.base_width * 0.2, body_y_start + 2, self.base_width * 0.6,
                                          self.base_height * 0.15)
        pygame.draw.ellipse(player_drawing_surf, highlight_color, body_highlight_rect)

        # --- Голова/Кабина ---
        head_height = self.base_height * 0.35
        head_width = self.base_width * 0.8
        head_x = (self.base_width - head_width) / 2
        head_y = 0  # Начинается сверху

        head_rect = pygame.Rect(head_x, head_y, head_width, head_height)
        pygame.draw.ellipse(player_drawing_surf, detail_color_light, head_rect)
        pygame.draw.ellipse(player_drawing_surf, shadow_color, head_rect, 2)  # Контур

        # "Глаз" / Сенсор (пульсирующий)
        eye_anim_scale = 0.9 + 0.1 * (math.sin(self.anim_timer * 2.5) * 0.5 + 0.5)  # Пульсация размера
        eye_width = head_width * 0.6 * eye_anim_scale
        eye_height = head_height * 0.4 * eye_anim_scale
        eye_x = (self.base_width - eye_width) / 2
        eye_y = head_y + head_height * 0.25
        eye_rect = pygame.Rect(eye_x, eye_y, eye_width, eye_height)

        eye_brightness = 0.8 + 0.2 * (math.sin(self.anim_timer * 1.5 + math.pi / 2) * 0.5 + 0.5)  # Пульсация яркости
        current_eye_color = tuple(int(c * eye_brightness) for c in eye_base_color)
        pygame.draw.ellipse(player_drawing_surf, current_eye_color, eye_rect)
        pygame.draw.ellipse(player_drawing_surf, detail_color_dark, eye_rect, 1)  # Тонкий контур глаза

        # --- Дополнительные детали ---
        # Боковые панели/углубления
        panel_width = self.base_width * 0.15
        panel_height = self.base_height * 0.4
        panel_y = body_y_start + self.base_height * 0.1
        # Левая
        pygame.draw.rect(player_drawing_surf, shadow_color,
                         (self.base_width * 0.05, panel_y, panel_width, panel_height), border_radius=3)
        # Правая
        pygame.draw.rect(player_drawing_surf, shadow_color,
                         (self.base_width * 0.80, panel_y, panel_width, panel_height), border_radius=3)

        # "Сопла" джетпака снизу (маленькие)
        nozzle_radius = self.base_width * 0.08
        nozzle_y = self.base_height - nozzle_radius * 0.8
        pygame.draw.circle(player_drawing_surf, detail_color_dark, (self.base_width * 0.35, nozzle_y), nozzle_radius)
        pygame.draw.circle(player_drawing_surf, detail_color_dark, (self.base_width * 0.65, nozzle_y), nozzle_radius)

        # --- Поворот спрайта (если есть наклон) ---
        if self.current_tilt != 0:
            rotated_surf = pygame.transform.rotate(player_drawing_surf, self.current_tilt)
            # Центрируем повернутый спрайт на основной self.image
            # self.image_buffer нужен, чтобы повёрнутый спрайт не обрезался краями self.image
            new_rect = rotated_surf.get_rect(center=(self.image.get_width() / 2, self.image.get_height() / 2))
            self.image.blit(rotated_surf, new_rect)
        else:
            # Центрируем не повернутый спрайт
            self.image.blit(player_drawing_surf, player_drawing_surf.get_rect(
                center=(self.image.get_width() / 2, self.image.get_height() / 2)))

    def update(self, dt):
        self.anim_timer += dt * 3.5  # Ускоряем немного общую анимацию

        # Плавное изменение наклона
        # Lerp (линейная интерполяция) для наклона: current = current + (target - current) * factor
        tilt_speed_factor = dt * 10  # Скорость изменения наклона
        self.current_tilt += (self.target_tilt - self.current_tilt) * tilt_speed_factor

        if self.is_jumping:
            self.target_tilt = 0  # Сбрасываем целевой наклон от "дыхания"
            self.y_velocity += self.gravity
            self.rect.y += self.y_velocity

            # Наклон в прыжке
            if self.y_velocity < -1:  # Поднимаемся
                self.target_tilt = -12
            elif self.y_velocity > 1:  # Падаем
                self.target_tilt = 8

            if self.rect.bottom >= self.base_y_on_lane + self.anim_y_offset:
                self.rect.bottom = self.base_y_on_lane + self.anim_y_offset
                self.is_jumping = False
                self.y_velocity = 0
                self.target_tilt = 0  # Сбрасываем наклон при приземлении

                for _ in range(10):
                    particles.append(Particle(
                        self.rect.centerx + random.uniform(-self.base_width / 2.5, self.base_width / 2.5),
                        self.rect.bottom,
                        (160, 160, 160), random.uniform(2.5, 5),
                        random.uniform(-50, 50), random.uniform(-60, -25), 280, 0.45
                    ))
            else:
                self.jetpack_timer -= dt
                if self.jetpack_timer <= 0:
                    jet_angle_rad = math.radians(self.current_tilt + 90)  # Частицы вылетают перпендикулярно "низу" бота

                    # Позиция вылета частиц (из "сопел")
                    nozzle_offset_x = self.base_width * 0.15 * math.cos(
                        math.radians(self.current_tilt))  # Смещение из-за наклона
                    nozzle_y_offset = self.base_width * 0.15 * math.sin(math.radians(self.current_tilt))

                    for i in [-1, 1]:  # Два сопла
                        start_x = self.rect.centerx + i * nozzle_offset_x
                        start_y = self.rect.bottom - self.image_buffer - nozzle_y_offset  # Вычитаем image_buffer, т.к. rect относится к большой картинке

                        jet_speed = random.uniform(70, 100)
                        p_speed_x = math.cos(jet_angle_rad) * jet_speed + random.uniform(-15, 15)
                        p_speed_y = math.sin(jet_angle_rad) * jet_speed + random.uniform(-10, 10)

                        particles.append(Particle(
                            start_x, start_y,
                            random.choice([(255, 100, 0), (255, 150, 30), (255, 200, 80)]), random.uniform(4, 7),
                            p_speed_x, p_speed_y,
                            -50, 0.3
                        ))
                    self.jetpack_timer = 0.02
        else:  # Если не в прыжке (на земле)
            # Анимация "дыхания" / покачивания
            self.anim_y_offset = math.sin(self.anim_timer) * 2.5
            self.rect.bottom = self.base_y_on_lane + self.anim_y_offset
            # Легкое покачивание корпуса на земле
            self.target_tilt = math.sin(self.anim_timer * 0.8) * 4

        self.rect.top = max(0, self.rect.top)
        self.draw_player_shape()

    def change_lane(self, direction):
        if not self.is_jumping:
            prev_lane_index = self.current_lane_index
            self.current_lane_index = max(0, min(len(LANE_YS) - 1, self.current_lane_index + direction))
            if prev_lane_index != self.current_lane_index:
                self.base_y_on_lane = LANE_YS[self.current_lane_index]
                self.rect.bottom = self.base_y_on_lane + self.anim_y_offset
                # Кратковременный более сильный наклон при смене полосы
                self.target_tilt = direction * 18
                # Можно добавить таймер для автоматического возврата наклона к нулю,
                # но текущая логика lerp со временем сама вернет его к "дыхательному" наклону

    def jump(self):
        if not self.is_jumping:
            self.is_jumping = True
            self.y_velocity = self.jump_power
            self.rect.y += self.y_velocity * 0.5  # Небольшой "отрыв" сразу
            self.jetpack_timer = 0.03
            self.target_tilt = -15  # Резкий наклон вверх для старта прыжка

            for _ in range(15):
                particles.append(Particle(
                    self.rect.centerx, self.rect.bottom - self.image_buffer,  # Вычитаем image_buffer
                    random.choice([(255, 220, 120), (255, 250, 180), YELLOW]), random.uniform(3, 6),
                    random.uniform(-35, 35), random.uniform(60, 100),
                    -120, 0.55
                ))

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
                pygame.draw.rect(surf, DARK_GREY, (offset, offset, s * 0.8 - offset * 1.5, s * 0.7 - offset * 1.5), 1)
            for r_idx in range(3):  # Renamed r to r_idx to avoid conflict if used in outer scope
                pygame.draw.line(surf, (100, 100, 100), (5, 10 + r_idx * 5), (s * 0.8 - 10, 10 + r_idx * 5), 1)

        if surf is None:
            surf = pygame.Surface((s, s), pygame.SRCALPHA)
            surf.fill(color)
            draw_text(surf, self.risk_type[0].upper(), int(s * 0.7), s / 2, s / 2, BLACK, anchor="center")
        return surf


class Booster(MovingObject):
    def __init__(self, world_speed, policy_type):
        self.policy_type = policy_type
        self.base_color = POLICY_COLORS.get(policy_type, GREEN)
        self.image = pygame.Surface((BOOSTER_RADIUS * 2, BOOSTER_RADIUS * 2), pygame.SRCALPHA)
        self.anim_timer = random.uniform(0, math.pi * 2)
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


class BackgroundElement:
    def __init__(self, y, height, min_width, max_width, color_palette, speed_factor, z_order):
        self.base_y = y
        self.height_variation = height * 0.3
        self.current_height = height + random.uniform(-self.height_variation, self.height_variation)

        self.rect = pygame.Rect(random.randint(0, SCREEN_WIDTH),
                                self.base_y - int(self.current_height),  # y - это низ здания, должен быть int
                                random.randint(min_width, max_width),
                                int(self.current_height))  # height должен быть int
        self.color = random.choice(color_palette)
        self.speed_factor = speed_factor
        self.z_order = z_order
        self.has_windows = random.random() < 0.7

    def update(self, world_speed_param, dt):
        self.rect.x -= world_speed_param * self.speed_factor
        if self.rect.right < 0:
            self.rect.left = SCREEN_WIDTH

            # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
            # Рассчитываем кандидатов на новую минимальную и максимальную ширину (как float)
            min_w_candidate_float = self.rect.width // 1.5
            potential_min_w_float = min_w_candidate_float if min_w_candidate_float > 20 else 20.0

            max_w_candidate_float = self.rect.width * 1.5
            potential_max_w_float = max_w_candidate_float if max_w_candidate_float < 250 else 250.0

            # Преобразуем в int для randint
            final_min_w = int(potential_min_w_float)
            final_max_w = int(potential_max_w_float)

            # Гарантируем, что min_w <= max_w
            if final_min_w > final_max_w:
                final_max_w = final_min_w  # Новый rect.width будет равен final_min_w

            self.rect.width = random.randint(final_min_w, final_max_w)
            # --- КОНЕЦ ИСПРАВЛЕНИЯ ---

            # Корректировка высоты (убедимся, что она тоже int)
            self.current_height = self.rect.height + random.uniform(-self.height_variation, self.height_variation)
            self.current_height = max(30.0,
                                      min(self.current_height, self.base_y * 0.8))  # Используем float для вычислений
            self.rect.height = int(self.current_height)  # Присваиваем rect.height как int

            # self.rect.top должен быть int, base_y и self.rect.height уже подготовлены
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
                for r_idx in range(num_y):  # Renamed r to r_idx
                    for c_idx in range(num_x):  # Renamed c to c_idx
                        win_x = draw_rect.left + gap_w + c_idx * (win_size_w + gap_w)
                        win_y = draw_rect.top + gap_h + r_idx * (win_size_h + gap_h)
                        if random.random() < 0.6:
                            pygame.draw.rect(surface, WINDOW_COLOR, (win_x, win_y, win_size_w, win_size_h))


# --- Основной Игровой Цикл ---
def game():
    global screen_shake_timer, screen_shake_amount, particles

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Risk Rush Deluxe - ЭНЕРГОГАРАНТ (No Assets Edition)")
    clock = pygame.time.Clock()

    world_speed = INITIAL_SPEED
    score = 0
    health = INITIAL_HEALTH
    active_policy = None
    game_start_time = time.time()
    last_speed_up_time = game_start_time
    toast_message = None
    toast_end_time = 0
    toast_alpha = 0
    shown_first_collision_tips = set()

    player = Player()
    all_sprites = pygame.sprite.Group(player)
    obstacles_group = pygame.sprite.Group()
    boosters_group = pygame.sprite.Group()

    background_elements = []
    for _ in range(10):
        background_elements.append(BackgroundElement(LANE_YS[0] - 150, 100, 30, 80, BUILDING_COLORS, 0.2, 0))
    for _ in range(8):
        background_elements.append(BackgroundElement(LANE_YS[0] - 80, 150, 40, 120, BUILDING_COLORS, 0.4, 1))
    for _ in range(6):
        background_elements.append(BackgroundElement(LANE_YS[0] - 20, 80, 50, 100, BUILDING_COLORS, 0.7, 2))

    background_elements.sort(key=lambda el: el.z_order)

    stars = []
    for _ in range(100):
        stars.append({
            'x': random.randint(0, SCREEN_WIDTH),
            'y': random.randint(0, int(LANE_YS[0] * 0.8)),
            'size': random.uniform(0.5, 1.5),
            'speed_factor': random.uniform(0.05, 0.15)
        })

    base_obstacle_spawn_delay = 1.8
    obstacle_spawn_delay = base_obstacle_spawn_delay
    obstacle_spawn_timer = obstacle_spawn_delay * 0.8

    base_booster_spawn_delay = base_obstacle_spawn_delay * 2.2
    booster_spawn_delay = base_booster_spawn_delay
    booster_spawn_timer = booster_spawn_delay * 0.5

    game_state = "playing"
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)

        current_offset_x, current_offset_y = 0, 0
        if screen_shake_timer > 0:
            screen_shake_timer -= dt
            current_offset_x = random.randint(-screen_shake_amount, screen_shake_amount)
            current_offset_y = random.randint(-screen_shake_amount, screen_shake_amount)
            if screen_shake_timer <= 0:
                screen_shake_amount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False; pygame.quit(); sys.exit()  # Ensure clean exit
            if game_state == "playing":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP or event.key == pygame.K_w: player.change_lane(-1)
                    if event.key == pygame.K_DOWN or event.key == pygame.K_s: player.change_lane(1)
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a: player.change_lane(-1)
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d: player.change_lane(1)
                    if event.key == pygame.K_SPACE: player.jump()
            elif game_state in ["win", "game_over"]:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r: game(); return
                    if event.key == pygame.K_q: running = False; pygame.quit(); sys.exit()  # Ensure clean exit

        if not running: break  # Exit loop if running is set to False

        if game_state == "playing":
            current_game_time = time.time()
            if current_game_time - last_speed_up_time > SPEED_INCREMENT_INTERVAL_SEC:
                world_speed += SPEED_INCREMENT
                last_speed_up_time = current_game_time
                obstacle_spawn_delay = max(0.5, (INITIAL_SPEED / world_speed) * base_obstacle_spawn_delay)
                booster_spawn_delay = max(1.0, obstacle_spawn_delay * 2.0)

            obstacle_spawn_timer += dt
            if obstacle_spawn_timer >= obstacle_spawn_delay:
                risk_type = random.choice(RISK_TYPES)
                obs = Obstacle(world_speed, risk_type)
                all_sprites.add(obs);
                obstacles_group.add(obs)
                obstacle_spawn_timer = random.uniform(-0.1, 0.1)

            booster_spawn_timer += dt
            if booster_spawn_timer >= booster_spawn_delay:
                policy_type = random.choice(POLICY_TYPES)
                boost = Booster(world_speed, policy_type)
                all_sprites.add(boost);
                boosters_group.add(boost)
                booster_spawn_timer = random.uniform(-0.2, 0.2)

            player.update(dt)
            for sprite in all_sprites:
                if sprite != player and hasattr(sprite, 'update') and callable(getattr(sprite, 'update')):
                    sprite.update(world_speed, dt)

            for bg_el in background_elements: bg_el.update(world_speed, dt)
            for star in stars:
                star['x'] -= world_speed * star['speed_factor']
                if star['x'] < 0:
                    star['x'] = SCREEN_WIDTH
                    star['y'] = random.randint(0, int(LANE_YS[0] * 0.8))

            for booster in pygame.sprite.spritecollide(player, boosters_group, True):
                active_policy = booster.policy_type
                toast_message = f"{active_policy.upper()} АКТИВИРОВАН!"
                toast_end_time = current_game_time + 2.0
                toast_alpha = 255
                create_explosion(booster.rect.centerx, booster.rect.centery,
                                 POLICY_COLORS.get(booster.policy_type, GREEN), 30, 120, 0.6)

            for obstacle in pygame.sprite.spritecollide(player, obstacles_group, True):
                risk = obstacle.risk_type
                cost = RISK_COSTS.get(risk, 0)
                protection = RISK_PROTECTION.get(risk)

                if active_policy == protection:
                    score += cost
                    active_policy = None
                    toast_message = f"{protection.upper() if protection else ''} спас! Экономия: {cost:,}₽"
                    toast_end_time = current_game_time + 2.5
                    toast_alpha = 255
                    create_explosion(obstacle.rect.centerx, obstacle.rect.centery, GREEN, 25, 100, 0.7)
                else:
                    health -= 1
                    apply_screen_shake(0.3, 8)
                    create_explosion(player.rect.centerx, player.rect.centery, RED, 40, 150, 0.8, gravity=200)

                    base_toast = TIPS_DATA.get(risk, f"Ой! Риск: {risk}")
                    if risk not in shown_first_collision_tips:
                        toast_message = base_toast
                        shown_first_collision_tips.add(risk)
                        toast_end_time = current_game_time + 3.5
                    else:
                        toast_message = f"Убыток! Бюджет -1"
                        toast_end_time = current_game_time + 2.0
                    toast_alpha = 255

                if health <= 0: game_state = "game_over"; break

            if current_game_time - game_start_time >= GAME_DURATION_SEC and game_state == "playing":
                game_state = "win"

        # --- Отрисовка ---
        for y_grad in range(int(LANE_YS[0])):
            ratio = y_grad / LANE_YS[0]
            color = (
                int(SKY_COLOR_TOP[0] * (1 - ratio) + SKY_COLOR_BOTTOM[0] * ratio),
                int(SKY_COLOR_TOP[1] * (1 - ratio) + SKY_COLOR_BOTTOM[1] * ratio),
                int(SKY_COLOR_TOP[2] * (1 - ratio) + SKY_COLOR_BOTTOM[2] * ratio)
            )
            pygame.draw.line(screen, color, (0 + current_offset_x, y_grad + current_offset_y),
                             (SCREEN_WIDTH + current_offset_x, y_grad + current_offset_y))

        for star in stars:
            pygame.draw.circle(screen, WHITE, (int(star['x'] + current_offset_x), int(star['y'] + current_offset_y)),
                               int(star['size']))

        for bg_el in background_elements: bg_el.draw(screen, current_offset_x, current_offset_y)

        road_rect_y = LANE_YS[0] - PLAYER_SIZE[1] * 0.8
        pygame.draw.rect(screen, ROAD_COLOR, (
        0 + current_offset_x, road_rect_y + current_offset_y, SCREEN_WIDTH, SCREEN_HEIGHT - road_rect_y))

        line_y_center = (LANE_YS[0] + LANE_YS[1]) / 2 + current_offset_y
        line_y_bottom = (LANE_YS[1] + LANE_YS[2]) / 2 + current_offset_y

        segment_length = 60
        gap_length = 40
        total_pattern_length = segment_length + gap_length
        start_x_offset_road = int(
            ((time.time() * world_speed * 10) % total_pattern_length) * -1)  # Renamed start_x_offset

        for x_pos in range(start_x_offset_road, SCREEN_WIDTH, total_pattern_length):
            pygame.draw.line(screen, ROAD_LINE_COLOR, (x_pos + current_offset_x, line_y_center),
                             (x_pos + segment_length + current_offset_x, line_y_center), 5)
            pygame.draw.line(screen, ROAD_LINE_COLOR, (x_pos + current_offset_x, line_y_bottom),
                             (x_pos + segment_length + current_offset_x, line_y_bottom), 5)

        pygame.draw.rect(screen, (150, 150, 150),
                         (0 + current_offset_x, road_rect_y + current_offset_y - 5, SCREEN_WIDTH, 5))
        pygame.draw.rect(screen, (150, 150, 150),
                         (0 + current_offset_x, LANE_YS[-1] + PLAYER_SIZE[1] * 0.2 + current_offset_y, SCREEN_WIDTH, 5))

        for sprite in all_sprites:
            screen.blit(sprite.image, sprite.rect.move(current_offset_x, current_offset_y))

        active_particles = []
        for p in particles:
            if p.update(dt):
                p.draw(screen, current_offset_x, current_offset_y)
                active_particles.append(p)
        particles = active_particles

        ui_padding = 10
        ui_element_height = 40
        ui_corner_radius = 8

        elapsed_time = time.time() - game_start_time
        time_left = max(0, GAME_DURATION_SEC - elapsed_time)
        mins, secs = divmod(int(time_left), 60)
        timer_text = f"{mins:02}:{secs:02}"
        timer_font = get_font(28, 'Digital-7, Consolas')
        timer_text_size = timer_font.size(timer_text)  # Renamed from timer_surf_size
        timer_bg_rect = pygame.Rect(SCREEN_WIDTH / 2 - timer_text_size[0] / 2 - ui_padding, ui_padding,
                                    timer_text_size[0] + ui_padding * 2, ui_element_height)
        draw_rounded_rect(screen, timer_bg_rect, UI_BG_COLOR, ui_corner_radius)
        draw_text(screen, timer_text, 28, SCREEN_WIDTH / 2, ui_padding + (ui_element_height - timer_text_size[1]) / 2,
                  UI_TEXT_COLOR, font_name_hint='Digital-7, Consolas', anchor="midtop", shadow=True,
                  shadow_color=(0, 0, 0, 100))

        score_text = f"Экономия: {score:,} ₽"
        score_font = get_font(24, 'Verdana')
        score_text_size = score_font.size(score_text)  # Renamed
        score_bg_rect = pygame.Rect(SCREEN_WIDTH - score_text_size[0] - ui_padding * 3, ui_padding,
                                    score_text_size[0] + ui_padding * 2, ui_element_height)
        draw_rounded_rect(screen, score_bg_rect, UI_BG_COLOR, ui_corner_radius)
        draw_text(screen, score_text, 24, SCREEN_WIDTH - ui_padding * 2,
                  ui_padding + (ui_element_height - score_text_size[1]) / 2, GREEN, font_name_hint='Verdana',
                  anchor="topright", shadow=True)

        health_text = "Бюджет: " + "❤️" * health + "🖤" * (INITIAL_HEALTH - health)
        health_font = get_font(24)
        health_text_size = health_font.size(health_text)  # Renamed
        health_bg_rect = pygame.Rect(ui_padding, ui_padding, health_text_size[0] + ui_padding * 2, ui_element_height)
        draw_rounded_rect(screen, health_bg_rect, UI_BG_COLOR, ui_corner_radius)
        health_color = RED if health <= 1 else (YELLOW if health == 2 else GREEN)
        draw_text(screen, health_text, 24, ui_padding * 2, ui_padding + (ui_element_height - health_text_size[1]) / 2,
                  health_color, shadow=True)

        if active_policy:
            policy_text = f"АКТИВЕН: {active_policy.upper()}"
            policy_font = get_font(20, 'Impact, Arial Black')
            policy_color_val = POLICY_COLORS.get(active_policy, WHITE)  # Renamed policy_color
            policy_text_size = policy_font.size(policy_text)  # Renamed
            policy_bg_rect = pygame.Rect(SCREEN_WIDTH / 2 - policy_text_size[0] / 2 - ui_padding,
                                         ui_padding * 2 + ui_element_height, policy_text_size[0] + ui_padding * 2,
                                         int(ui_element_height * 0.8))
            draw_rounded_rect(screen, policy_bg_rect, (*policy_color_val, 180), ui_corner_radius - 2, alpha=200)
            draw_text(screen, policy_text, 20, SCREEN_WIDTH / 2,
                      ui_padding * 2 + ui_element_height + (int(ui_element_height * 0.8) - policy_text_size[1]) / 2,
                      WHITE, font_name_hint='Impact, Arial Black', anchor="midtop", shadow=True, shadow_color=BLACK)

        if toast_message and time.time() < toast_end_time:
            if toast_alpha < 255: toast_alpha = min(255, toast_alpha + 255 * dt * 5)

            toast_font = get_font(20)
            text_lines_toast = toast_message.split("! ")  # Renamed
            max_line_width_toast = 0  # Renamed
            rendered_lines_toast = []  # Renamed
            line_height_total_toast = 0  # Renamed

            for i, line in enumerate(text_lines_toast):
                if i > 0: line = "! " + line
                rendered_line = toast_font.render(line, True, TOAST_TEXT_COLOR)
                rendered_lines_toast.append(rendered_line)
                max_line_width_toast = max(max_line_width_toast, rendered_line.get_width())
                line_height_total_toast += rendered_line.get_height() + (5 if i > 0 else 0)

            toast_surf_width = max_line_width_toast + 40
            toast_surf_height = line_height_total_toast + 20

            toast_s = pygame.Surface((toast_surf_width, toast_surf_height), pygame.SRCALPHA)

            temp_toast_bg_color = (
            *TOAST_BG_COLOR[:3], int(TOAST_BG_COLOR[3] * (toast_alpha / 255.0)))  # Ensure float division for alpha
            draw_rounded_rect(toast_s, toast_s.get_rect(), temp_toast_bg_color, 10)

            current_y_offset_toast = 10  # Renamed
            for rl_toast in rendered_lines_toast:  # Renamed rl
                toast_s.blit(rl_toast, rl_toast.get_rect(centerx=toast_surf_width / 2, top=current_y_offset_toast))
                current_y_offset_toast += rl_toast.get_height() + 5

            screen.blit(toast_s, toast_s.get_rect(midbottom=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 20)))

        elif toast_message and time.time() >= toast_end_time:
            toast_alpha = max(0, toast_alpha - 255 * dt * 5)
            if toast_alpha <= 0:  # Check for <=0 for float inaccuracies
                toast_message = None
            else:
                # Re-draw logic for fading out (similar to above, but using current toast_alpha)
                toast_font = get_font(20)
                text_lines_toast = toast_message.split("! ")
                max_line_width_toast = 0
                rendered_lines_toast = []
                line_height_total_toast = 0
                for i, line in enumerate(text_lines_toast):
                    if i > 0: line = "! " + line
                    # Create text surfaces with potentially modified alpha for fading text
                    temp_text_color = (*TOAST_TEXT_COLOR[:3], int(toast_alpha))
                    rendered_line = toast_font.render(line, True, temp_text_color)
                    rendered_lines_toast.append(rendered_line)
                    max_line_width_toast = max(max_line_width_toast, rendered_line.get_width())
                    line_height_total_toast += rendered_line.get_height() + (5 if i > 0 else 0)

                toast_surf_width = max_line_width_toast + 40
                toast_surf_height = line_height_total_toast + 20
                toast_s = pygame.Surface((toast_surf_width, toast_surf_height), pygame.SRCALPHA)
                temp_toast_bg_color = (*TOAST_BG_COLOR[:3], int(TOAST_BG_COLOR[3] * (toast_alpha / 255.0)))
                draw_rounded_rect(toast_s, toast_s.get_rect(), temp_toast_bg_color, 10)
                current_y_offset_toast = 10
                for rl_toast in rendered_lines_toast:
                    rl_toast.set_alpha(int(toast_alpha))  # Apply alpha directly to text surfaces
                    toast_s.blit(rl_toast, rl_toast.get_rect(centerx=toast_surf_width / 2, top=current_y_offset_toast))
                    current_y_offset_toast += rl_toast.get_height() + 5
                screen.blit(toast_s, toast_s.get_rect(midbottom=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 20)))

        if game_state in ["win", "game_over"]:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 220))
            screen.blit(overlay, (0, 0))

            title_text = "ПОБЕДА!" if game_state == "win" else "БЮДЖЕТ ИСЧЕРПАН"  # Renamed title
            title_color_val = GREEN if game_state == "win" else RED  # Renamed title_color
            draw_text(screen, title_text, 70, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3, title_color_val,
                      font_name_hint='Impact, Arial Black', anchor="center", shadow=True, shadow_color=(50, 50, 50))
            draw_text(screen, f"Итоговая экономия: {score:,} ₽", 45, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, WHITE,
                      font_name_hint='Verdana', anchor="center", shadow=True)

            if game_state == "win":
                draw_text(screen, "Отличная работа! Узнайте больше о полисах ЭНЕРГОГАРАНТ!", 24, SCREEN_WIDTH / 2,
                          SCREEN_HEIGHT / 2 + 70, SKY_COLOR_BOTTOM, anchor="center", shadow=True)

            draw_text(screen, "Нажмите [R] для Рестарта или [Q] для Выхода", 28, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.72,
                      WHITE, anchor="center", shadow=True)

            draw_text(screen, "--- Таблица Лидеров (Мок) ---", 22, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.72 + 60, GREY,
                      anchor="center")
            mock_scores = sorted([
                ("МегаПолисМен", random.randint(max(10000, score + 5000), max(20000, score * 2 + 10000))),
                ("Вы", score),
                ("ОсторожныйВодитель", random.randint(0, max(5000, score // 2 + 1000)))
            ], key=lambda x: x[1], reverse=True)
            for i, (name, s_val) in enumerate(mock_scores[:3]):
                name_color = YELLOW if name == "Вы" else LIGHT_GREY
                draw_text(screen, f"{i + 1}. {name} ..... {s_val:,} ₽", 20, SCREEN_WIDTH / 2,
                          SCREEN_HEIGHT * 0.72 + 95 + i * 28, name_color, anchor="center")

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    print("Запуск Risk Rush Deluxe - Финальная версия (без Asset-ов)...")
    game()