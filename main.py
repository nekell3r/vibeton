import pygame
import sys
import time
import random
import math

from config import *
from sprites.player import Player
from sprites.obstacles import Obstacle, Booster
from sprites.background import BackgroundElement
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
    active_policy = None
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
    for _ in range(10):
        background_elements.append(BackgroundElement(LANE_YS[0] - 150, 100, 30, 80, BUILDING_COLORS, 0.2, 0))
    for _ in range(8):
        background_elements.append(BackgroundElement(LANE_YS[0] - 80, 150, 40, 120, BUILDING_COLORS, 0.4, 1))
    for _ in range(6):
        background_elements.append(BackgroundElement(LANE_YS[0] - 20, 80, 50, 100, BUILDING_COLORS, 0.7, 2))

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
                active_policy = booster.policy_type
                toast_message = f"{active_policy.upper()} АКТИВИРОВАН!"
                toast_end_time = current_game_time + 2.0
                toast_alpha = 255
                particles.extend(create_explosion(booster.rect.centerx, booster.rect.centery,
                                               POLICY_COLORS.get(booster.policy_type, GREEN), 30, 120, 0.6))

            # Проверка коллизий с препятствиями
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
                    particles.extend(create_explosion(obstacle.rect.centerx, obstacle.rect.centery, GREEN, 25, 100, 0.7))
                else:
                    health -= 1
                    apply_screen_shake(0.3, 8)
                    particles.extend(create_explosion(player.rect.centerx, player.rect.centery, RED, 40, 150, 0.8, gravity=200))

                    base_toast = TIPS_DATA.get(risk, f"Ой! Риск: {risk}")
                    if risk not in shown_first_collision_tips:
                        toast_message = base_toast
                        shown_first_collision_tips.add(risk)
                        toast_end_time = current_game_time + 3.5
                    else:
                        toast_message = f"Убыток! Бюджет -1"
                        toast_end_time = current_game_time + 2.0
                    toast_alpha = 255

                if health <= 0:
                    game_state = "game_over"
                    break

            if current_game_time - game_start_time >= GAME_DURATION_SEC and game_state == "playing":
                game_state = "win"

        # Отрисовка
        # Градиент неба
        for y_grad in range(int(LANE_YS[0])):
            ratio = y_grad / LANE_YS[0]
            color = (
                int(SKY_COLOR_TOP[0] * (1 - ratio) + SKY_COLOR_BOTTOM[0] * ratio),
                int(SKY_COLOR_TOP[1] * (1 - ratio) + SKY_COLOR_BOTTOM[1] * ratio),
                int(SKY_COLOR_TOP[2] * (1 - ratio) + SKY_COLOR_BOTTOM[2] * ratio)
            )
            pygame.draw.line(screen, color, (0 + current_offset_x, y_grad + current_offset_y),
                           (SCREEN_WIDTH + current_offset_x, y_grad + current_offset_y))

        # Звезды
        for star in stars:
            pygame.draw.circle(screen, WHITE, (int(star['x'] + current_offset_x), int(star['y'] + current_offset_y)),
                             int(star['size']))

        # Фоновые здания
        for bg_el in background_elements:
            bg_el.draw(screen, current_offset_x, current_offset_y)

        # Дорога
        road_rect_y = LANE_YS[0] - PLAYER_SIZE[1] * 0.8
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

        # UI
        elapsed_time = time.time() - game_start_time
        time_left = max(0, GAME_DURATION_SEC - elapsed_time)
        draw_timer(screen, time_left)
        draw_score(screen, score)
        draw_health(screen, health, INITIAL_HEALTH)
        draw_active_policy(screen, active_policy, POLICY_COLORS)
        toast_alpha = draw_toast(screen, toast_message, toast_end_time, toast_alpha, time.time())

        if game_state in ["win", "game_over"]:
            draw_game_over_screen(screen, game_state, score, SKY_COLOR_BOTTOM)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    print("Запуск Risk Rush Deluxe - Финальная версия (без Asset-ов)...")
    game() 