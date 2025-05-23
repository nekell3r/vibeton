from enum import Enum
from typing import Dict, Any
import pygame

class RiskType(Enum):
    ROBBERY = "robbery"  # Ограбление
    ACCIDENT = "accident"  # Авария
    FIRE = "fire"  # Пожар
    CYBER = "cyber"  # Кибер-атака
    NATURAL = "natural"  # Природный риск

    @property
    def description(self) -> str:
        descriptions = {
            self.ROBBERY: "Ограбление",
            self.ACCIDENT: "Авария",
            self.FIRE: "Пожар",
            self.CYBER: "Кибер-атака",
            self.NATURAL: "Стихия"
        }
        return descriptions[self]

class Risk:
    def __init__(self, risk_type: RiskType, x: int, y: int):
        self.risk_type = risk_type
        self.x = x
        self.y = y
        self.speed = 5
        self.width = 40
        self.height = 40
        self.rect = pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)
        self.properties = {}
        self._set_properties()
        self.label = risk_type.description
        self.label_surface = None
        self._create_label_surface()
        
    def _create_label_surface(self):
        """Создание поверхности с подписью риска"""
        font = pygame.font.Font(None, 24)
        self.label_surface = font.render(self.label, True, (255, 255, 255))
        # Добавляем тень для лучшей читаемости
        shadow = font.render(self.label, True, (0, 0, 0))
        shadow_surface = pygame.Surface(shadow.get_size(), pygame.SRCALPHA)
        shadow_surface.blit(shadow, (1, 1))
        shadow_surface.set_alpha(128)
        self.label_surface.blit(shadow_surface, (0, 0))
        
    def _set_properties(self):
        """Установка свойств риска в зависимости от типа"""
        self.properties = {
            RiskType.ROBBERY: {
                "damage": 30,
                "score_value": 100,
                "required_policy": "basic_policy"
            },
            RiskType.ACCIDENT: {
                "damage": 20,
                "score_value": 80,
                "required_policy": "basic_policy"
            },
            RiskType.FIRE: {
                "damage": 40,
                "score_value": 150,
                "required_policy": "fire_policy"
            },
            RiskType.CYBER: {
                "damage": 35,
                "score_value": 120,
                "required_policy": "cyber_policy"
            },
            RiskType.NATURAL: {
                "damage": 50,
                "score_value": 200,
                "required_policy": "gold_policy"
            }
        }
        
    def update(self):
        """Обновление позиции риска"""
        self.x -= self.speed
        self.rect.centerx = self.x
        self.y += self.speed
        self.rect.x = self.x
        self.rect.y = self.y
        
    def is_off_screen(self, screen_height: int) -> bool:
        """Проверка, вышел ли риск за пределы экрана"""
        return self.y > screen_height
        
    def get_damage(self) -> int:
        """Получить урон от риска"""
        return self.properties[self.risk_type]["damage"]
        
    def get_score_value(self) -> int:
        """Получить очки за риск"""
        return self.properties[self.risk_type]["score_value"]
        
    def get_required_policy(self) -> str:
        """Получить требуемый полис для защиты от риска"""
        return self.properties[self.risk_type]["required_policy"]
        
    def draw(self, surface: pygame.Surface, sprite_manager):
        """Отрисовка риска и его подписи"""
        # Отрисовка спрайта риска
        sprite_manager.draw_sprite(surface, self.risk_type.value, 
                                 (self.rect.centerx, self.rect.centery))
        
        # Отрисовка подписи
        if self.label_surface:
            label_x = self.rect.centerx - self.label_surface.get_width() // 2
            label_y = self.rect.bottom + 5
            surface.blit(self.label_surface, (label_x, label_y)) 