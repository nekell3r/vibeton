import pygame
from config import BLACK

def get_font(size, font_name_hint=None):
    preferred_fonts = ['Consolas', 'Arial', 'Verdana']
    if font_name_hint:
        preferred_fonts.insert(0, font_name_hint)

    for font_name in preferred_fonts:
        try:
            found_font_name = pygame.font.match_font(font_name)
            if found_font_name:
                return pygame.font.Font(found_font_name, size)
        except:  # noqa
            continue
    return pygame.font.Font(None, size)

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

    effective_rect_width = rect.width
    effective_rect_height = rect.height

    if effective_rect_width < 1 or effective_rect_height < 1:
        return

    if corner_radius > min(effective_rect_width, effective_rect_height) / 2:
        corner_radius = min(effective_rect_width, effective_rect_height) / 2

    corner_radius = max(0, corner_radius)

    surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    fill_color_rgb = color[:3]

    pygame.draw.rect(surf, fill_color_rgb,
                     (0, corner_radius, effective_rect_width, effective_rect_height - 2 * corner_radius))
    pygame.draw.rect(surf, fill_color_rgb,
                     (corner_radius, 0, effective_rect_width - 2 * corner_radius, effective_rect_height))

    pygame.draw.circle(surf, fill_color_rgb, (corner_radius, corner_radius), corner_radius)
    pygame.draw.circle(surf, fill_color_rgb, (effective_rect_width - corner_radius, corner_radius), corner_radius)
    pygame.draw.circle(surf, fill_color_rgb, (corner_radius, effective_rect_height - corner_radius), corner_radius)
    pygame.draw.circle(surf, fill_color_rgb,
                       (effective_rect_width - corner_radius, effective_rect_height - corner_radius), corner_radius)

    surf.set_alpha(alpha if len(color) == 3 else color[3])
    surface.blit(surf, rect.topleft) 