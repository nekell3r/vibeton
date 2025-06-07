import pygame
from config import (UI_BG_COLOR, UI_TEXT_COLOR, GREEN, YELLOW, RED, WHITE, BLACK,
                   TOAST_BG_COLOR, TOAST_TEXT_COLOR, LIGHT_GREY)
from utils.drawing import draw_text, draw_rounded_rect, get_font

def draw_timer(screen, time_left, ui_padding=10, ui_element_height=40, ui_corner_radius=8):
    mins, secs = divmod(int(time_left), 60)
    timer_text = f"{mins:02}:{secs:02}"
    timer_font = get_font(28, 'Digital-7, Consolas')
    timer_text_size = timer_font.size(timer_text)
    timer_bg_rect = pygame.Rect(screen.get_width() / 2 - timer_text_size[0] / 2 - ui_padding, ui_padding,
                                timer_text_size[0] + ui_padding * 2, ui_element_height)
    draw_rounded_rect(screen, timer_bg_rect, UI_BG_COLOR, ui_corner_radius)
    draw_text(screen, timer_text, 28, screen.get_width() / 2, ui_padding + (ui_element_height - timer_text_size[1]) / 2,
              UI_TEXT_COLOR, font_name_hint='Digital-7, Consolas', anchor="midtop", shadow=True,
              shadow_color=(0, 0, 0, 100))

def draw_score(screen, score, ui_padding=10, ui_element_height=40, ui_corner_radius=8):
    score_text = f"Экономия: {score:,} ₽"
    score_font = get_font(24, 'Verdana')
    score_text_size = score_font.size(score_text)
    score_bg_rect = pygame.Rect(screen.get_width() - score_text_size[0] - ui_padding * 3, ui_padding,
                                score_text_size[0] + ui_padding * 2, ui_element_height)
    draw_rounded_rect(screen, score_bg_rect, UI_BG_COLOR, ui_corner_radius)
    draw_text(screen, score_text, 24, screen.get_width() - ui_padding * 2,
              ui_padding + (ui_element_height - score_text_size[1]) / 2, GREEN, font_name_hint='Verdana',
              anchor="topright", shadow=True)

def draw_health(screen, health, initial_health, ui_padding=10, ui_element_height=40, ui_corner_radius=8):
    health_text = "Бюджет: " + "❤️" * health + "🖤" * (initial_health - health)
    health_font = get_font(24)
    health_text_size = health_font.size(health_text)
    health_bg_rect = pygame.Rect(ui_padding, ui_padding, health_text_size[0] + ui_padding * 2, ui_element_height)
    draw_rounded_rect(screen, health_bg_rect, UI_BG_COLOR, ui_corner_radius)
    health_color = RED if health <= 1 else (YELLOW if health == 2 else GREEN)
    draw_text(screen, health_text, 24, ui_padding * 2, ui_padding + (ui_element_height - health_text_size[1]) / 2,
              health_color, shadow=True)

def draw_active_policy(screen, active_policy, policy_colors, ui_padding=10, ui_element_height=40):
    if active_policy:
        policy_text = f"АКТИВЕН: {active_policy.upper()}"
        policy_font = get_font(20, 'Impact, Arial Black')
        policy_color = policy_colors.get(active_policy, WHITE)
        policy_text_size = policy_font.size(policy_text)
        policy_bg_rect = pygame.Rect(screen.get_width() / 2 - policy_text_size[0] / 2 - ui_padding,
                                     ui_padding * 2 + ui_element_height, policy_text_size[0] + ui_padding * 2,
                                     int(ui_element_height * 0.8))
        draw_rounded_rect(screen, policy_bg_rect, (*policy_color, 180), 6, alpha=200)
        draw_text(screen, policy_text, 20, screen.get_width() / 2,
                  ui_padding * 2 + ui_element_height + (int(ui_element_height * 0.8) - policy_text_size[1]) / 2,
                  WHITE, font_name_hint='Impact, Arial Black', anchor="midtop", shadow=True, shadow_color=BLACK)

def draw_toast(screen, message, end_time, alpha, current_time):
    if not message:
        return 0

    if current_time >= end_time:
        alpha = max(0, alpha - 255 * 0.2)
        if alpha <= 0:
            return 0
    elif alpha < 255:
        alpha = min(255, alpha + 255 * 0.2)

    toast_font = get_font(20)
    text_lines = message.split("! ")
    max_line_width = 0
    rendered_lines = []
    line_height_total = 0

    for i, line in enumerate(text_lines):
        if i > 0:
            line = "! " + line
        rendered_line = toast_font.render(line, True, TOAST_TEXT_COLOR)
        rendered_lines.append(rendered_line)
        max_line_width = max(max_line_width, rendered_line.get_width())
        line_height_total += rendered_line.get_height() + (5 if i > 0 else 0)

    toast_surf_width = max_line_width + 40
    toast_surf_height = line_height_total + 20

    toast_s = pygame.Surface((toast_surf_width, toast_surf_height), pygame.SRCALPHA)
    temp_toast_bg_color = (*TOAST_BG_COLOR[:3], int(TOAST_BG_COLOR[3] * (alpha / 255.0)))
    draw_rounded_rect(toast_s, toast_s.get_rect(), temp_toast_bg_color, 10)

    current_y_offset = 10
    for rendered_line in rendered_lines:
        rendered_line.set_alpha(int(alpha))
        toast_s.blit(rendered_line, rendered_line.get_rect(centerx=toast_surf_width / 2, top=current_y_offset))
        current_y_offset += rendered_line.get_height() + 5

    screen.blit(toast_s, toast_s.get_rect(midbottom=(screen.get_width() / 2, screen.get_height() - 20)))
    return alpha

def draw_game_over_screen(screen, game_state, score, sky_color_bottom):
    overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 220))
    screen.blit(overlay, (0, 0))

    title_text = "ПОБЕДА!" if game_state == "win" else "БЮДЖЕТ ИСЧЕРПАН"
    title_color = GREEN if game_state == "win" else RED
    draw_text(screen, title_text, 70, screen.get_width() / 2, screen.get_height() / 3, title_color,
              font_name_hint='Impact, Arial Black', anchor="center", shadow=True, shadow_color=(50, 50, 50))
    draw_text(screen, f"Итоговая экономия: {score:,} ₽", 45, screen.get_width() / 2, screen.get_height() / 2, WHITE,
              font_name_hint='Verdana', anchor="center", shadow=True)

    if game_state == "win":
        draw_text(screen, "Отличная работа! Узнайте больше о полисах ЭНЕРГОГАРАНТ!", 24, screen.get_width() / 2,
                  screen.get_height() / 2 + 70, sky_color_bottom, anchor="center", shadow=True)

    draw_text(screen, "Нажмите [R] для Рестарта или [Q] для Выхода", 28, screen.get_width() / 2, screen.get_height() * 0.72,
              WHITE, anchor="center", shadow=True)

    draw_text(screen, "--- Таблица Лидеров (Мок) ---", 22, screen.get_width() / 2, screen.get_height() * 0.72 + 60, (128, 128, 128),
              anchor="center")
    mock_scores = sorted([
        ("МегаПолисМен", max(10000, score + 5000)),
        ("Вы", score),
        ("ОсторожныйВодитель", max(5000, score // 2))
    ], key=lambda x: x[1], reverse=True)
    for i, (name, s) in enumerate(mock_scores[:3]):
        name_color = YELLOW if name == "Вы" else LIGHT_GREY
        draw_text(screen, f"{i + 1}. {name} ..... {s:,} ₽", 20, screen.get_width() / 2,
                  screen.get_height() * 0.72 + 95 + i * 28, name_color, anchor="center") 