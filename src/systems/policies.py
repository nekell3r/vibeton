from enum import Enum
from typing import Dict, Any, List
import pygame

class PolicyType(Enum):
    BASIC = "basic_policy"  # Базовый полис
    FIRE = "fire_policy"    # Противопожарный
    CYBER = "cyber_policy"  # Кибер-страхование
    GOLD = "gold_policy"    # Золотой полис

    @property
    def description(self) -> str:
        descriptions = {
            self.BASIC: "Базовый",
            self.FIRE: "Противопожарный",
            self.CYBER: "Кибер-защита",
            self.GOLD: "Золотой"
        }
        return descriptions[self]

class Policy:
    def __init__(self, policy_type: PolicyType, x: int, y: int):
        self.policy_type = policy_type
        self.x = x
        self.y = y
        self.speed = 5
        self.width = 40
        self.height = 40
        self.rect = pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)
        self.properties = {}
        self._set_properties()
        self.label = policy_type.description
        self.label_surface = None
        self._create_label_surface()
        
    def _create_label_surface(self):
        """Создание поверхности с подписью полиса"""
        font = pygame.font.Font(None, 24)
        self.label_surface = font.render(self.label, True, (255, 255, 255))
        # Добавляем тень для лучшей читаемости
        shadow = font.render(self.label, True, (0, 0, 0))
        shadow_surface = pygame.Surface(shadow.get_size(), pygame.SRCALPHA)
        shadow_surface.blit(shadow, (1, 1))
        shadow_surface.set_alpha(128)
        self.label_surface.blit(shadow_surface, (0, 0))
        
    def _set_properties(self):
        """Установка свойств полиса в зависимости от типа"""
        self.properties = {
            PolicyType.BASIC: {
                "duration": 10,
                "score_value": 50,
                "protected_risks": ["robbery", "accident"],
                "cost": 100
            },
            PolicyType.FIRE: {
                "duration": 15,
                "score_value": 100,
                "protected_risks": ["fire"],
                "cost": 200
            },
            PolicyType.CYBER: {
                "duration": 20,
                "score_value": 150,
                "protected_risks": ["cyber"],
                "cost": 300
            },
            PolicyType.GOLD: {
                "duration": 30,
                "score_value": 300,
                "protected_risks": ["natural"],
                "cost": 500
            }
        }
        
    def update(self):
        """Обновление позиции полиса"""
        self.x -= self.speed
        self.rect.centerx = self.x
        self.rect.centery = self.y
        
    def is_off_screen(self, screen_height: int) -> bool:
        """Проверка, вышел ли полис за пределы экрана"""
        return self.y > screen_height
        
    def get_duration(self) -> int:
        """Получить длительность действия полиса"""
        return self.properties[self.policy_type]["duration"]
        
    def get_score_value(self) -> int:
        """Получить очки за полис"""
        return self.properties[self.policy_type]["score_value"]
        
    def get_protected_risks(self) -> List[str]:
        """Получить список защищаемых рисков"""
        return self.properties[self.policy_type]["protected_risks"]
        
    def get_cost(self) -> int:
        """Получить стоимость полиса"""
        return self.properties[self.policy_type]["cost"]
        
    def draw(self, surface: pygame.Surface, sprite_manager):
        """Отрисовка полиса и его подписи"""
        # Отрисовка спрайта полиса
        sprite_manager.draw_sprite(surface, self.policy_type.value, 
                                 (self.rect.centerx, self.rect.centery))
        
        # Отрисовка подписи
        if self.label_surface:
            label_x = self.rect.centerx - self.label_surface.get_width() // 2
            label_y = self.rect.bottom + 5
            surface.blit(self.label_surface, (label_x, label_y))

    def get_color(self) -> tuple:
        """Получить цвет полиса"""
        # Implementation needed
        return (255, 255, 255)  # Placeholder return, actual implementation needed

    def get_description(self) -> str:
        """Получить описание полиса"""
        return self.policy_type.description 