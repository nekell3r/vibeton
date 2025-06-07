import pygame
import sys
import time
import random
import math

from config import *
from sprites.player import Player
from sprites.obstacles import Obstacle, Booster
from sprites.background import BackgroundElement, WeatherSystem, draw_ground
from utils.particles import create_explosion, apply_screen_shake, update_screen_shake
from utils.ui import (draw_timer, draw_score, draw_health, draw_active_policy,
                     draw_toast, draw_game_over_screen)

def game():
    # Инициализация Pygame
    pygame.init()
    pygame.font.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Risk Rush Deluxe - ЭНЕРГОГАРАНТ (No Assets Edition)")
    clock = pygame.time.Clock()

    # Игровые переменные
    world_speed = INITIAL_SPEED
    score = 0
    health = INITIAL_HEALTH
    active_policies = []
    game_start_time = time.time()
    last_speed_up_time = game_start_time
    toast_message = None
    toast_end_time = 0
    toast_alpha = 0
    shown_first_collision_tips = set()
    particles = []

    # Создание спрайтов
    player = Player()
    all_sprites = pygame.sprite.Group(player)
    obstacles_group = pygame.sprite.Group()
    boosters_group = pygame.sprite.Group()

    # Создание фоновых элементов
    background_elements = []
    # Дальние здания (маленькие)
    for _ in range(10):
        background_elements.append(BackgroundElement(LANE_YS[0] * 0.55, 143, 30, 80, BUILDING_COLORS, 0.2, 0))
    # Средние здания
    for _ in range(8):
        background_elements.append(BackgroundElement(LANE_YS[0] * 0.6, 176, 40, 120, BUILDING_COLORS, 0.4, 1))
    # Ближние здания (большие)
    for _ in range(6):
        background_elements.append(BackgroundElement(LANE_YS[0] * 0.65, 187, 50, 100, BUILDING_COLORS, 0.7, 2))

    background_elements.sort(key=lambda el: el.z_order)

    # Создание звезд
    stars = []
    for _ in range(100):
        stars.append({
            'x': random.randint(0, SCREEN_WIDTH),
            'y': random.randint(0, int(LANE_YS[0] * 0.8)),
            'size': random.uniform(0.5, 1.5),
            'speed_factor': random.uniform(0.05, 0.15)
        })

    # Таймеры спавна
    base_obstacle_spawn_delay = 1.8
    obstacle_spawn_delay = base_obstacle_spawn_delay
    obstacle_spawn_timer = obstacle_spawn_delay * 0.8

    base_booster_spawn_delay = base_obstacle_spawn_delay * 2.2
    booster_spawn_delay = base_booster_spawn_delay
    booster_spawn_timer = booster_spawn_delay * 0.5

    game_state = "playing"
    running = True

    # Создание погодной системы
    weather_system = WeatherSystem()

    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)

        current_offset_x, current_offset_y = update_screen_shake(dt)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

            if game_state == "playing":
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_UP, pygame.K_w]:
                        player.change_lane(-1)
                    if event.key in [pygame.K_DOWN, pygame.K_s]:
                        player.change_lane(1)
                    if event.key in [pygame.K_LEFT, pygame.K_a]:
                        player.change_lane(-1)
                    if event.key in [pygame.K_RIGHT, pygame.K_d]:
                        player.change_lane(1)
                    if event.key == pygame.K_SPACE:
                        particles.extend(player.jump())
            elif game_state in ["win", "game_over"]:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        game()
                        return
                    if event.key == pygame.K_q:
                        running = False
                        pygame.quit()
                        sys.exit()

        if not running:
            break

        if game_state == "playing":
            current_game_time = time.time()

            # Обновление скорости игры
            if current_game_time - last_speed_up_time > SPEED_INCREMENT_INTERVAL_SEC:
                world_speed += SPEED_INCREMENT
                last_speed_up_time = current_game_time
                obstacle_spawn_delay = max(0.5, (INITIAL_SPEED / world_speed) * base_obstacle_spawn_delay)
                booster_spawn_delay = max(1.0, obstacle_spawn_delay * 2.0)

            # Спавн препятствий
            obstacle_spawn_timer += dt
            if obstacle_spawn_timer >= obstacle_spawn_delay:
                risk_type = random.choice(RISK_TYPES)
                obs = Obstacle(world_speed, risk_type)
                all_sprites.add(obs)
                obstacles_group.add(obs)
                obstacle_spawn_timer = random.uniform(-0.1, 0.1)

            # Спавн бустеров
            booster_spawn_timer += dt
            if booster_spawn_timer >= booster_spawn_delay:
                policy_type = random.choice(POLICY_TYPES)
                boost = Booster(world_speed, policy_type)
                all_sprites.add(boost)
                boosters_group.add(boost)
                booster_spawn_timer = random.uniform(-0.2, 0.2)

            # Обновление игрока и создание частиц
            new_particles = player.update(dt)
            if new_particles:
                particles.extend(new_particles)

            # Обновление остальных спрайтов
            for sprite in all_sprites:
                if sprite != player:
                    sprite.update(world_speed, dt)

            # Обновление фона
            for bg_el in background_elements:
                bg_el.update(world_speed, dt)
            for star in stars:
                star['x'] -= world_speed * star['speed_factor']
                if star['x'] < 0:
                    star['x'] = SCREEN_WIDTH
                    star['y'] = random.randint(0, int(LANE_YS[0] * 0.8))

            # Проверка коллизий с бустерами
            for booster in pygame.sprite.spritecollide(player, boosters_group, True):
                if booster.policy_type not in active_policies:
                    active_policies.append(booster.policy_type)
                    toast_message = f"{booster.policy_type.upper()} АКТИВИРОВАН!"
                    toast_end_time = time.time() + 2.0
                    toast_alpha = 255
                    particles.extend(create_explosion(booster.rect.centerx, booster.rect.centery,
                                                   POLICY_COLORS.get(booster.policy_type, GREEN), 30, 120, 0.6))

            # Проверка коллизий с препятствиями
            for obstacle in pygame.sprite.spritecollide(player, obstacles_group, True):
                risk = obstacle.risk_type
                cost = RISK_COSTS.get(risk, 0)
                protection = RISK_PROTECTION.get(risk)

                if protection in active_policies:
                    score += cost
                    active_policies.remove(protection)
                    toast_message = f"{protection.upper() if protection else ''} спас! Экономия: {cost:,}₽"
                    toast_end_time = time.time() + 2.5
                    toast_alpha = 255
                    particles.extend(create_explosion(obstacle.rect.centerx, obstacle.rect.centery, GREEN, 25, 100, 0.7))
                else:
                    health -= 1
                    apply_screen_shake(0.3, 8)
                    particles.extend(create_explosion(player.rect.centerx, player.rect.centery, RED, 40, 150, 0.8, gravity=200))

                    base_toast = TIPS_DATA.get(risk, f"Ой! Риск: {risk}")
                    if risk not in shown_first_collision_tips:
                        toast_message = base_toast
                        shown_first_collision_tips.add(risk)
                        toast_end_time = time.time() + 3.5
                    else:
                        toast_message = f"Убыток! Бюджет -1"
                        toast_end_time = time.time() + 2.0
                    toast_alpha = 255

                if health <= 0:
                    game_state = "game_over"
                    break

            if current_game_time - game_start_time >= GAME_DURATION_SEC and game_state == "playing":
                game_state = "win"

            # Обновление погоды
            weather_system.update(dt)

        # Отрисовка
        # Получаем текущие цвета неба из погодной системы
        sky_color_top, sky_color_bottom = weather_system.get_current_sky_colors()
        
        # Вычисляем позицию дороги
        road_rect_y = LANE_YS[0] - PLAYER_SIZE[1] * 0.8
        
        # Градиент неба (только до дороги)
        for y_grad in range(int(road_rect_y)):
            ratio = y_grad / road_rect_y
            color = (
                int(sky_color_top[0] * (1 - ratio) + sky_color_bottom[0] * ratio),
                int(sky_color_top[1] * (1 - ratio) + sky_color_bottom[1] * ratio),
                int(sky_color_top[2] * (1 - ratio) + sky_color_bottom[2] * ratio)
            )
            pygame.draw.line(screen, color, (0 + current_offset_x, y_grad + current_offset_y),
                           (SCREEN_WIDTH + current_offset_x, y_grad + current_offset_y))

        # Солнце (только если оно видимо в текущую погоду и нет перехода, и не рассвет)
        current_weather = WEATHER_TYPES[weather_system.current_weather]
        if weather_system.next_weather is None and current_weather["sun_visible"] and weather_system.current_weather != "sunrise":
            # Вычисляем позицию солнца с учетом прогресса текущей погоды
            base_sun_position = current_weather["sun_position"]
            progress = weather_system.weather_timer / weather_system.weather_duration
            if weather_system.current_weather == "clear":
                arc_radius = SCREEN_WIDTH * 0.35
                cx = SCREEN_WIDTH // 2
                cy = road_rect_y * 0.8
                theta = math.pi - progress * math.pi
                sun_x = cx + arc_radius * math.cos(theta)
                sun_y = cy - arc_radius * math.sin(theta)
                sun_alpha = 255
            elif weather_system.current_weather == "sunset":
                if progress < 0.8:
                    sun_x = SCREEN_WIDTH * 0.95
                    sun_y = road_rect_y * 0.85
                    sun_alpha = 255
                else:
                    final_progress = (progress - 0.8) / 0.2
                    sun_x = SCREEN_WIDTH * 0.95
                    sun_y = road_rect_y * (0.85 + final_progress * 0.15)
                    sun_alpha = int(255 * (1 - final_progress))
            else:
                sun_x = SCREEN_WIDTH * 0.8
                sun_y = road_rect_y * base_sun_position
                sun_alpha = 255

            sun_radius = 40
            # Свечение
            for r in range(int(sun_radius * 1.5), int(sun_radius * 0.8), -2):
                alpha = int((255 * (1 - (r - sun_radius * 0.8) / (sun_radius * 0.7)) * sun_alpha) / 255)
                alpha = max(0, min(255, alpha))
                glow_surface = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, (*YELLOW, alpha), (r, r), r)
                screen.blit(glow_surface, 
                          (sun_x - r + current_offset_x, 
                           sun_y - r + current_offset_y))
            # Само солнце (теперь с поддержкой альфы)
            sun_surf_size = int(sun_radius * 1.6)
            sun_alpha = max(0, min(255, sun_alpha))
            sun_surface = pygame.Surface((sun_surf_size, sun_surf_size), pygame.SRCALPHA)
            pygame.draw.circle(
                sun_surface,
                (*YELLOW, sun_alpha),
                (sun_surf_size // 2, sun_surf_size // 2),
                int(sun_radius * 0.8)
            )
            screen.blit(
                sun_surface,
                (int(sun_x + current_offset_x - sun_surf_size // 2), int(sun_y + current_offset_y - sun_surf_size // 2))
            )

        # Звезды (только если они видимы в текущую погоду)
        if WEATHER_TYPES[weather_system.current_weather]["stars_visible"]:
            for star in stars:
                if star['y'] < road_rect_y:  # Рисуем звезды только в небе
                    pygame.draw.circle(screen, WHITE, (int(star['x'] + current_offset_x), int(star['y'] + current_offset_y)),
                                     int(star['size']))

        # Земля (рисуем до зданий)
        draw_ground(screen, current_offset_x, current_offset_y, weather_system)

        # Фоновые здания
        for bg_el in background_elements:
            bg_el.draw(screen, current_offset_x, current_offset_y, weather_system)

        # Дорога
        pygame.draw.rect(screen, ROAD_COLOR, (
            0 + current_offset_x, road_rect_y + current_offset_y, SCREEN_WIDTH, SCREEN_HEIGHT - road_rect_y))

        # Разметка
        line_y_center = (LANE_YS[0] + LANE_YS[1]) / 2 + current_offset_y
        line_y_bottom = (LANE_YS[1] + LANE_YS[2]) / 2 + current_offset_y

        segment_length = 60
        gap_length = 40
        total_pattern_length = segment_length + gap_length
        start_x_offset = int(((time.time() * world_speed * 10) % total_pattern_length) * -1)

        for x_pos in range(start_x_offset, SCREEN_WIDTH, total_pattern_length):
            pygame.draw.line(screen, ROAD_LINE_COLOR, (x_pos + current_offset_x, line_y_center),
                           (x_pos + segment_length + current_offset_x, line_y_center), 5)
            pygame.draw.line(screen, ROAD_LINE_COLOR, (x_pos + current_offset_x, line_y_bottom),
                           (x_pos + segment_length + current_offset_x, line_y_bottom), 5)

        # Границы дороги
        pygame.draw.rect(screen, (150, 150, 150),
                        (0 + current_offset_x, road_rect_y + current_offset_y - 5, SCREEN_WIDTH, 5))
        pygame.draw.rect(screen, (150, 150, 150),
                        (0 + current_offset_x, LANE_YS[-1] + PLAYER_SIZE[1] * 0.2 + current_offset_y, SCREEN_WIDTH, 5))

        # Спрайты
        for sprite in all_sprites:
            screen.blit(sprite.image, sprite.rect.move(current_offset_x, current_offset_y))

        # Частицы
        active_particles = []
        for p in particles:
            if p.update(dt):
                p.draw(screen, current_offset_x, current_offset_y)
                active_particles.append(p)
        particles = active_particles

        # Погодные эффекты
        weather_system.draw_weather(screen, current_offset_x, current_offset_y)

        # UI
        elapsed_time = time.time() - game_start_time
        time_left = max(0, GAME_DURATION_SEC - elapsed_time)
        draw_timer(screen, time_left)
        draw_score(screen, score)
        draw_health(screen, health, INITIAL_HEALTH)
        if active_policies:
            y_offset = 0
            for policy in active_policies:
                draw_active_policy(screen, policy, POLICY_COLORS, ui_padding=10, ui_element_height=40, y_offset=y_offset)
                y_offset += 45
        toast_alpha = draw_toast(screen, toast_message, toast_end_time, toast_alpha, time.time())

        if game_state in ["win", "game_over"]:
            draw_game_over_screen(screen, game_state, score, sky_color_bottom)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    print("Запуск Risk Rush Deluxe - Финальная версия (без Asset-ов)...")
    game() 