import pygame
import random
import sys
import time

# --- Инициализация Pygame ---
pygame.init()
# pygame.font.init() # Инициализация шрифтов, если вдруг основная не сработала (обычно не нужно)

# --- Константы ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)  # Игрок
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
ORANGE = (255, 165, 0)
GREY = (128, 128, 128)
DARK_GREY = (50, 50, 50)

SKY_COLOR = (135, 206, 235)  # Голубое небо для "города"
BUILDING_COLORS = [(160, 160, 160), (180, 180, 180), (140, 140, 140)]  # Цвета зданий
ROAD_COLOR = (100, 100, 100)
ROAD_LINE_COLOR = (200, 200, 0)  # Желтая разметка
UI_TEXT_COLOR = (30, 30, 30)  # Темный текст для UI
TOAST_TEXT_COLOR = WHITE
TOAST_BG_COLOR = (0, 0, 0, 190)  # Полупрозрачный фон для Toast

# Параметры игры
LANE_YS = [SCREEN_HEIGHT * 0.6, SCREEN_HEIGHT * 0.75, SCREEN_HEIGHT * 0.9 - 20]
PLAYER_START_X = 150
INITIAL_SPEED = 4.0  # Начальная скорость мира
SPEED_INCREMENT = 0.25  # Увеличение скорости
SPEED_INCREMENT_INTERVAL_SEC = 10  # Интервал увеличения скорости
GAME_DURATION_SEC = 90  # Длительность сессии <m-document-mention>{"documentId":"9be9eba6-11b5-457a-a6e9-d3f713bbddbc","blockName":"pdf","documentName":"","blockParams":{"pdf_page_number":"1","pdf_page_y":"66.11185","pdf_page_x":"5.5208373","pdf_width":"91.82204","pdf_height":"62.306915"},"collapsed":true}</m-document-mention>
INITIAL_HEALTH = 3

# Размеры объектов (для плейсхолдеров)
PLAYER_SIZE = (40, 60)
OBSTACLE_SIZE_MAP = {"tree": (50, 70), "phone": (25, 25), "accident": (70, 40), "bill": (50, 35)}
BOOSTER_SIZE = (40, 40)

# Цвета объектов (замена картинок)
POLICY_COLORS = {"kasko": GREEN, "dms": CYAN, "property": YELLOW, "travel": MAGENTA}
RISK_COLORS = {"tree": (139, 69, 19), "phone": GREY, "accident": RED, "bill": ORANGE}

# Данные игры <m-document-mention>{"documentId":"9be9eba6-11b5-457a-a6e9-d3f713bbddbc","blockName":"pdf","documentName":"","blockParams":{"pdf_page_number":"1","pdf_page_y":"66.11185","pdf_page_x":"5.5208373","pdf_width":"91.82204","pdf_height":"62.306915"},"collapsed":true}</m-document-mention> (Основные элементы, Механика)
POLICY_TYPES = list(POLICY_COLORS.keys())
RISK_TYPES = list(RISK_COLORS.keys())
RISK_PROTECTION = {"tree": "property", "phone": "property", "accident": "kasko", "bill": "dms"}
RISK_COSTS = {"tree": 30000, "phone": 15000, "accident": 50000, "bill": 25000}
TIPS_DATA = {
    # <m-document-mention>{"documentId":"9be9eba6-11b5-457a-a6e9-d3f713bbddbc","blockName":"pdf","documentName":"","blockParams":{"pdf_page_number":"1","pdf_page_y":"66.11185","pdf_page_x":"5.5208373","pdf_width":"91.82204","pdf_height":"62.306915"},"collapsed":true}</m-document-mention> (Обучающий слой)
    "tree": f"Имущество от дерева! Экономия: {RISK_COSTS['tree']:,}₽",
    "phone": f"Имущество за телефон! Экономия: {RISK_COSTS['phone']:,}₽",
    "accident": f"КАСКО от аварии! Экономия: {RISK_COSTS['accident']:,}₽",
    "bill": f"ДМС за счет! Экономия: {RISK_COSTS['bill']:,}₽"
}


# --- Вспомогательные функции ---
def create_rect_surface(size, color, text="", text_color=BLACK, border_color=None, border_width=1):
    surface = pygame.Surface(size).convert_alpha()
    surface.fill(color)
    if border_color:
        pygame.draw.rect(surface, border_color, (0, 0, size[0], size[1]), border_width)
    if text:
        try:
            font_name = pygame.font.match_font('arial, consolas, sansserif')  # Ищем подходящий шрифт
            font_size = int(min(size) * 0.55)  # Размер шрифта чуть меньше
            if font_size < 10: font_size = 10  # Минимальный размер шрифта
            font = pygame.font.Font(font_name, font_size)
            text_surf = font.render(text, True, text_color)
            surface.blit(text_surf, text_surf.get_rect(center=(size[0] / 2, size[1] / 2)))
        except Exception as e:
            # print(f"Font error for text '{text}': {e}") # Для отладки, если шрифты не рисуются
            pass  # Не страшно, если текст не нарисовался на плейсхолдере
    return surface


def draw_text(surface, text, size, x, y, color, font_name_hint=None, anchor="topleft"):
    font_name = pygame.font.match_font(font_name_hint if font_name_hint else 'arial, consolas, sansserif')
    try:
        font = pygame.font.Font(font_name, size)
    except Exception:
        font = pygame.font.Font(None, size)  # Pygame default font
    text_surface = font.render(text, True, color)
    rect_params = {anchor: (x, y)}
    text_rect = text_surface.get_rect(**rect_params)
    surface.blit(text_surface, text_rect)


# --- Классы Игровых Объектов ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = create_rect_surface(PLAYER_SIZE, BLUE, "Бот", WHITE)  # "Полис-бот"
        self.rect = self.image.get_rect(midbottom=(PLAYER_START_X, LANE_YS[1]))
        self.current_lane_index = 1
        self.is_jumping = False;
        self.jump_power = -17;
        self.gravity = 0.8;
        self.y_velocity = 0
        self.base_y = LANE_YS[self.current_lane_index]

    def update(self):
        if self.is_jumping:
            self.y_velocity += self.gravity
            self.rect.y += self.y_velocity
            if self.rect.bottom >= self.base_y:
                self.rect.bottom = self.base_y;
                self.is_jumping = False;
                self.y_velocity = 0
        self.rect.top = max(0, self.rect.top)  # Не выходить за верх экрана
        self.rect.bottom = min(SCREEN_HEIGHT, self.rect.bottom)  # И за низ (хотя это делает дорога)

    def change_lane(self,
                    direction):  # <m-document-mention>{"documentId":"9be9eba6-11b5-457a-a6e9-d3f713bbddbc","blockName":"pdf","documentName":"","blockParams":{"pdf_page_number":"1","pdf_page_y":"66.11185","pdf_page_x":"5.5208373","pdf_width":"91.82204","pdf_height":"62.306915"},"collapsed":true}</m-document-mention> Механика: ← / → смена полосы
        if not self.is_jumping:
            self.current_lane_index = max(0, min(len(LANE_YS) - 1, self.current_lane_index + direction))
            self.base_y = LANE_YS[self.current_lane_index]
            # Плавный переход можно сделать через target_y и lerp в update, но для простоты - мгновенно
            self.rect.midbottom = (self.rect.midbottom[0], self.base_y)

    def jump(
            self):  # <m-document-mention>{"documentId":"9be9eba6-11b5-457a-a6e9-d3f713bbddbc","blockName":"pdf","documentName":"","blockParams":{"pdf_page_number":"1","pdf_page_y":"66.11185","pdf_page_x":"5.5208373","pdf_width":"91.82204","pdf_height":"62.306915"},"collapsed":true}</m-document-mention> Механика: пробел — прыжок
        if not self.is_jumping:
            self.is_jumping = True;
            self.y_velocity = self.jump_power


class MovingObject(pygame.sprite.Sprite):
    def __init__(self, image, world_speed, lane_y):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(midleft=(SCREEN_WIDTH + random.randint(30, 100), lane_y))
        self.current_world_speed = world_speed  # Сохраняем скорость мира на момент создания

    def update(self, world_speed_param):  # Принимаем текущую скорость мира для движения
        self.rect.x -= world_speed_param  # Двигаемся с актуальной скоростью мира
        if self.rect.right < 0: self.kill()


class Obstacle(MovingObject):  # Препятствия-риски
    def __init__(self, world_speed, risk_type):
        self.risk_type = risk_type
        size = OBSTACLE_SIZE_MAP.get(risk_type, (50, 50))
        color = RISK_COLORS.get(risk_type, RED)
        image = create_rect_surface(size, color, risk_type[0].upper(), WHITE, BLACK)
        super().__init__(image, world_speed, random.choice(LANE_YS))


class Booster(MovingObject):  # Бустеры-полисы
    def __init__(self, world_speed, policy_type):
        self.policy_type = policy_type
        color = POLICY_COLORS.get(policy_type, GREEN)
        image = create_rect_surface(BOOSTER_SIZE, color, policy_type[0].upper(), BLACK, WHITE)
        super().__init__(image, world_speed, random.choice(LANE_YS))


class BackgroundElement:  # <m-document-mention>{"documentId":"9be9eba6-11b5-457a-a6e9-d3f713bbddbc","blockName":"pdf","documentName":"","blockParams":{"pdf_page_number":"1","pdf_page_y":"66.11185","pdf_page_x":"5.5208373","pdf_width":"91.82204","pdf_height":"62.306915"},"collapsed":true}</m-document-mention> Сетап: Город-low-poly
    def __init__(self, y, height, min_width, max_width, color, speed_factor):
        self.rect = pygame.Rect(random.randint(0, SCREEN_WIDTH), y, random.randint(min_width, max_width), height)
        self.color = color
        self.speed_factor = speed_factor

    def update(self, world_speed_param):
        self.rect.x -= world_speed_param * self.speed_factor
        if self.rect.right < 0:
            self.rect.left = SCREEN_WIDTH
            self.rect.width = random.randint(self.rect.width // 2 if self.rect.width // 2 > 30 else 30,
                                             self.rect.width * 2 if self.rect.width * 2 < 200 else 200)  # Меняем ширину

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)


# --- Основной Игровой Цикл ---
def game():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Risk Rush - ЭНЕРГОГАРАНТ (No Assets Edition)")
    clock = pygame.time.Clock()

    world_speed = INITIAL_SPEED
    score = 0;
    health = INITIAL_HEALTH;
    active_policy = None  # <m-document-mention>{"documentId":"9be9eba6-11b5-457a-a6e9-d3f713bbddbc","blockName":"pdf","documentName":"","blockParams":{"pdf_page_number":"1","pdf_page_y":"66.11185","pdf_page_x":"5.5208373","pdf_width":"91.82204","pdf_height":"62.306915"},"collapsed":true}</m-document-mention> Счёт, Здоровье бюджета
    game_start_time = time.time();
    last_speed_up_time = game_start_time
    toast_message = None;
    toast_end_time = 0
    shown_first_collision_tips = set()

    player = Player()
    all_sprites = pygame.sprite.Group(player)
    obstacles_group = pygame.sprite.Group()
    boosters_group = pygame.sprite.Group()

    background_elements = []  # "Город-low-poly"
    for _ in range(8):  # Дальние, медленные здания
        color = random.choice(BUILDING_COLORS)
        background_elements.append(BackgroundElement(LANE_YS[0] - 200, 180, 60, 120, color, 0.25))
    for _ in range(6):  # Средние здания/элементы
        color = random.choice(BUILDING_COLORS)
        background_elements.append(BackgroundElement(LANE_YS[0] - 120, 100, 40, 80, color, 0.5))

    base_obstacle_spawn_delay = 2.0  # Начальная задержка для препятствий
    obstacle_spawn_delay = base_obstacle_spawn_delay
    obstacle_spawn_timer = obstacle_spawn_delay  # Чтобы первое препятствие появилось почти сразу

    base_booster_spawn_delay = base_obstacle_spawn_delay * 2.5
    booster_spawn_delay = base_booster_spawn_delay
    booster_spawn_timer = booster_spawn_delay / 2  # Бустеры тоже не сразу

    game_state = "playing"
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # Дельта времени (в секундах)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if game_state == "playing":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP or event.key == pygame.K_LEFT: player.change_lane(-1)
                    if event.key == pygame.K_DOWN or event.key == pygame.K_RIGHT: player.change_lane(1)
                    if event.key == pygame.K_SPACE: player.jump()
            elif game_state in ["win",
                                "game_over"]:  # <m-document-mention>{"documentId":"9be9eba6-11b5-457a-a6e9-d3f713bbddbc","blockName":"pdf","documentName":"","blockParams":{"pdf_page_number":"1","pdf_page_y":"66.11185","pdf_page_x":"5.5208373","pdf_width":"91.82204","pdf_height":"62.306915"},"collapsed":true}</m-document-mention> Победа / поражение
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r: game(); return  # Рестарт
                    if event.key == pygame.K_q: running = False

        if game_state == "playing":
            current_game_time = time.time()
            # <m-document-mention>{"documentId":"9be9eba6-11b5-457a-a6e9-d3f713bbddbc","blockName":"pdf","documentName":"","blockParams":{"pdf_page_number":"1","pdf_page_y":"66.11185","pdf_page_x":"5.5208373","pdf_width":"91.82204","pdf_height":"62.306915"},"collapsed":true}</m-document-mention> Игровой цикл: +скорость каждые 20 с (у нас 10)
            if current_game_time - last_speed_up_time > SPEED_INCREMENT_INTERVAL_SEC:
                world_speed += SPEED_INCREMENT;
                last_speed_up_time = current_game_time
                obstacle_spawn_delay = max(0.6, (INITIAL_SPEED / world_speed) * base_obstacle_spawn_delay)
                booster_spawn_delay = max(1.2, obstacle_spawn_delay * 2.2)
                print(f"Speed: {world_speed:.1f}, ObstD: {obstacle_spawn_delay:.2f}")

            # <m-document-mention>{"documentId":"9be9eba6-11b5-457a-a6e9-d3f713bbddbc","blockName":"pdf","documentName":"","blockParams":{"pdf_page_number":"1","pdf_page_y":"66.11185","pdf_page_x":"5.5208373","pdf_width":"91.82204","pdf_height":"62.306915"},"collapsed":true}</m-document-mention> Игровой цикл: Спавн препятствия
            obstacle_spawn_timer += dt
            if obstacle_spawn_timer >= obstacle_spawn_delay:
                obs = Obstacle(world_speed, random.choice(RISK_TYPES))
                all_sprites.add(obs);
                obstacles_group.add(obs)
                obstacle_spawn_timer = 0  # random.uniform(-0.2, 0.2) # Небольшой рандом

            booster_spawn_timer += dt
            if booster_spawn_timer >= booster_spawn_delay:
                boost = Booster(world_speed, random.choice(POLICY_TYPES))
                all_sprites.add(boost);
                boosters_group.add(boost)
                booster_spawn_timer = 0  # random.uniform(-0.3, 0.3)

            # Обновление всех спрайтов и фоновых элементов
            # Передаем world_speed в update для MovingObject и BackgroundElement
            for sprite in all_sprites:  # Обновление спрайтов, если им нужна скорость
                if hasattr(sprite, 'update') and callable(getattr(sprite, 'update')):
                    if isinstance(sprite, (MovingObject)):
                        sprite.update(world_speed)
                    else:  # Для игрока
                        sprite.update()

            for bg_el in background_elements: bg_el.update(world_speed)

            # <m-document-mention>{"documentId":"9be9eba6-11b5-457a-a6e9-d3f713bbddbc","blockName":"pdf","documentName":"","blockParams":{"pdf_page_number":"1","pdf_page_y":"66.11185","pdf_page_x":"5.5208373","pdf_width":"91.82204","pdf_height":"62.306915"},"collapsed":true}</m-document-mention> Игровой цикл: Проверка полиса
            for booster in pygame.sprite.spritecollide(player, boosters_group, True):  # True удаляет спрайт
                active_policy = booster.policy_type
                toast_message = f"{active_policy.upper()} АКТИВИРОВАН!"
                toast_end_time = current_game_time + 2.0

            for obstacle in pygame.sprite.spritecollide(player, obstacles_group, True):
                risk = obstacle.risk_type;
                cost = RISK_COSTS.get(risk, 0)
                protection = RISK_PROTECTION.get(risk)

                if active_policy == protection:  # Полис сработал
                    score += cost;
                    active_policy = None  # Полис использован
                    toast_message = f"{protection.upper() if protection else ''} спас! Экономия: {cost:,}₽"
                    toast_end_time = current_game_time + 2.5
                else:  # Нет нужного полиса или нет вообще
                    health -= 1
                    base_toast = TIPS_DATA.get(risk, f"Ой! Риск: {risk}")
                    if risk not in shown_first_collision_tips:  # <m-document-mention>{"documentId":"9be9eba6-11b5-457a-a6e9-d3f713bbddbc","blockName":"pdf","documentName":"","blockParams":{"pdf_page_number":"1","pdf_page_y":"66.11185","pdf_page_x":"5.5208373","pdf_width":"91.82204","pdf_height":"62.306915"},"collapsed":true}</m-document-mention> Обучающий слой
                        toast_message = base_toast  # Показываем полную подсказку первый раз
                        shown_first_collision_tips.add(risk)
                        toast_end_time = current_game_time + 3.5  # Длиннее для первой подсказки
                    else:
                        toast_message = f"Убыток! Здоровье -1"
                        toast_end_time = current_game_time + 2.0

                if health <= 0: game_state = "game_over"; break  # <m-document-mention>{"documentId":"9be9eba6-11b5-457a-a6e9-d3f713bbddbc","blockName":"pdf","documentName":"","blockParams":{"pdf_page_number":"1","pdf_page_y":"66.11185","pdf_page_x":"5.5208373","pdf_width":"91.82204","pdf_height":"62.306915"},"collapsed":true}</m-document-mention> Поражение

            if current_game_time - game_start_time >= GAME_DURATION_SEC:  # <m-document-mention>{"documentId":"9be9eba6-11b5-457a-a6e9-d3f713bbddbc","blockName":"pdf","documentName":"","blockParams":{"pdf_page_number":"1","pdf_page_y":"66.11185","pdf_page_x":"5.5208373","pdf_width":"91.82204","pdf_height":"62.306915"},"collapsed":true}</m-document-mention> Цель, Сессия
                game_state = "win"

                # --- Отрисовка ---
        screen.fill(SKY_COLOR)
        for bg_el in background_elements: bg_el.draw(screen)  # Фон "Город-low-poly"

        road_y = LANE_YS[0] - 50  # Верхняя граница дороги
        pygame.draw.rect(screen, ROAD_COLOR, (0, road_y, SCREEN_WIDTH, SCREEN_HEIGHT - road_y))
        # ...
        # Движущаяся разметка дороги
        line_y = road_y + (LANE_YS[-1] - road_y + PLAYER_SIZE[1]) / 2
        start_x_offset = int(((time.time() * world_speed * 7) % 100) * -1)
        for x_pos in range(start_x_offset, SCREEN_WIDTH, 100): # Шаг 100 для более длинных тире. Переменная x_pos
             pygame.draw.line(screen, ROAD_LINE_COLOR, (x_pos, line_y), (x_pos + 50, line_y), 5) # Используем x_pos
        # ...
        all_sprites.draw(screen)  # Игрок, препятствия, бустеры

        # UI (Счет, Здоровье, Таймер)
        elapsed_time = time.time() - game_start_time
        time_left = max(0, GAME_DURATION_SEC - elapsed_time)
        mins, secs = divmod(int(time_left), 60)
        draw_text(screen, f"{mins:02}:{secs:02}", 30, SCREEN_WIDTH / 2, 15, DARK_GREY,
                  font_name_hint='digital, consolas', anchor="midtop")
        draw_text(screen, f"Экономия: {score:,} ₽", 28, SCREEN_WIDTH - 20, 15, DARK_GREY, font_name_hint='verdana',
                  anchor="topright")
        health_display = "❤️" * health + "🖤" * (INITIAL_HEALTH - health)
        draw_text(screen, health_display, 32, 20, 15, RED if health <= 1 else DARK_GREY)  # Красный если мало здоровья

        if active_policy:
            policy_color = POLICY_COLORS.get(active_policy, GREEN)
            draw_text(screen, f"АКТИВЕН: {active_policy.upper()}", 22, SCREEN_WIDTH / 2, 55, policy_color,
                      font_name_hint='impact, arialblack', anchor="midtop")

        # Toast сообщение
        if toast_message and time.time() < toast_end_time:
            text_lines = toast_message.split("! ")  # Грубое разделение по "!" для переноса
            max_line_width = 0
            rendered_lines = []
            line_height_total = 0
            try:
                # Пытаемся получить реальный шрифт для расчета высоты
                font_name = pygame.font.match_font('arial, sansserif')
                toast_font = pygame.font.Font(font_name, 20) if font_name else pygame.font.Font(None, 20)

                for i, line in enumerate(text_lines):
                    if i > 0: line = "! " + line  # Возвращаем "!" если он был разделителем
                    rendered_line = toast_font.render(line, True, TOAST_TEXT_COLOR)
                    rendered_lines.append(rendered_line)
                    max_line_width = max(max_line_width, rendered_line.get_width())
                    line_height_total += rendered_line.get_height() + (
                        5 if i > 0 else 0)  # +5 для межстрочного интервала

                toast_surf_width = max_line_width + 40  # + отступы
                toast_surf_height = line_height_total + 20  # + отступы

                toast_s = pygame.Surface((toast_surf_width, toast_surf_height)).convert_alpha()
                toast_s.fill(TOAST_BG_COLOR)

                current_y_offset = 10
                for rl in rendered_lines:
                    toast_s.blit(rl, rl.get_rect(centerx=toast_surf_width / 2, top=current_y_offset))
                    current_y_offset += rl.get_height() + 5

                screen.blit(toast_s, toast_s.get_rect(midbottom=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 20)))
            except Exception as e:
                # print(f"Toast rendering error: {e}") # Для отладки
                # Если что-то пошло не так с многострочным, рисуем как раньше
                old_toast_s = create_rect_surface((SCREEN_WIDTH * 0.8, 50), TOAST_BG_COLOR, toast_message,
                                                  TOAST_TEXT_COLOR, WHITE)
                screen.blit(old_toast_s, old_toast_s.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 40)))

        elif time.time() >= toast_end_time:  # Сбрасываем сообщение
            toast_message = None

        # Экран Победы / Поражения
        if game_state in ["win", "game_over"]:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200));
            screen.blit(overlay, (0, 0))  # Более темный оверлей

            title = "ПОБЕДА!" if game_state == "win" else "КОНЕЦ ИГРЫ"
            title_color = GREEN if game_state == "win" else RED
            draw_text(screen, title, 70, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3, title_color,
                      font_name_hint='impact, arialblack', anchor="center")
            draw_text(screen, f"Итоговая экономия: {score:,} ₽", 40, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, WHITE,
                      font_name_hint='verdana', anchor="center")

            if game_state == "win":  # CTA «Рассчитать полис»
                draw_text(screen, "Задача выполнена! Узнайте о полисах ЭНЕРГОГАРАНТ!", 22, SCREEN_WIDTH / 2,
                          SCREEN_HEIGHT / 2 + 60, SKY_COLOR, anchor="center")

            draw_text(screen, "Нажмите [R] для Рестарта или [Q] для Выхода", 25, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.75,
                      WHITE, anchor="center")

            # Mock Leaderboard <m-document-mention>{"documentId":"9be9eba6-11b5-457a-a6e9-d3f713bbddbc","blockName":"pdf","documentName":"","blockParams":{"pdf_page_number":"1","pdf_page_y":"66.11185","pdf_page_x":"5.5208373","pdf_width":"91.82204","pdf_height":"62.306915"},"collapsed":true}</m-document-mention>
            draw_text(screen, "--- Таблица Лидеров (Мок) ---", 20, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.75 + 50, GREY,
                      anchor="center")
            mock_scores = sorted([
                ("СуперИгрок", random.randint(max(10000, score), max(20000, score * 2))),
                ("Вы", score),
                ("Новичок", random.randint(0, max(5000, score // 2)))
            ], key=lambda x: x[1], reverse=True)
            for i, (name, s_val) in enumerate(mock_scores[:3]):
                draw_text(screen, f"{i + 1}. {name} ..... {s_val:,} ₽", 18, SCREEN_WIDTH / 2,
                          SCREEN_HEIGHT * 0.75 + 80 + i * 25, WHITE, anchor="center")

        pygame.display.flip()  # Обновляем экран
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    print("Запуск Risk Rush - Финальная версия (без Asset-ов)...")
    game()