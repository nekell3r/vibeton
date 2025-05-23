import pygame
from typing import Dict, List, Tuple, Optional
from enum import Enum
import math
import random

class SpriteType(Enum):
    PLAYER = "player"
    RISK = "risk"
    POLICY = "policy"
    EFFECT = "effect"
    JUMP_TRAIL = "jump_trail"
    SHADOW = "shadow"
    BACKGROUND = "background"

class SpriteManager:
    def __init__(self):
        self.sprites: Dict[str, pygame.Surface] = {}
        self.animations: Dict[str, List[pygame.Surface]] = {}
        self.background_objects: List[Dict] = []
        self._create_temp_sprites()
        self._init_background_objects()
        
    def _init_background_objects(self):
        """Инициализация фоновых объектов"""
        # Создаем разные типы фоновых объектов
        for _ in range(20):  # 20 фоновых объектов
            obj_type = random.choice(['building', 'tree', 'cloud'])
            lane = random.randint(0, 3)
            y = random.randint(-1000, 0)  # Начинаем выше экрана
            speed = random.uniform(1, 3)  # Разная скорость движения
            scale = random.uniform(0.5, 1.5)  # Разный размер
            
            self.background_objects.append({
                'type': obj_type,
                'lane': lane,
                'y': y,
                'speed': speed,
                'scale': scale
            })
            
    def _create_temp_sprites(self):
        """Создание временных спрайтов для прототипа"""
        # Создаем спрайт игрока (робот)
        player = pygame.Surface((40, 60), pygame.SRCALPHA)
        # Тело робота
        pygame.draw.rect(player, (100, 100, 100), (10, 10, 20, 30))
        # Голова
        pygame.draw.rect(player, (150, 150, 150), (12, 5, 16, 10))
        # Глаза
        pygame.draw.circle(player, (0, 255, 0), (16, 10), 2)
        pygame.draw.circle(player, (0, 255, 0), (24, 10), 2)
        # Руки
        pygame.draw.line(player, (100, 100, 100), (10, 15), (5, 25), 3)
        pygame.draw.line(player, (100, 100, 100), (30, 15), (35, 25), 3)
        # Ноги
        pygame.draw.line(player, (100, 100, 100), (15, 40), (15, 50), 3)
        pygame.draw.line(player, (100, 100, 100), (25, 40), (25, 50), 3)
        self.sprites["player"] = player
        
        # Создаем спрайт тени
        shadow = pygame.Surface((40, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 128), (0, 0, 40, 20))
        self.sprites["shadow"] = shadow
        
        # Создаем спрайты рисков
        risk_colors = {
            "robbery": (255, 0, 0),    # Красный
            "accident": (255, 165, 0),  # Оранжевый
            "fire": (255, 69, 0),      # Оранжево-красный
            "cyber": (0, 191, 255),    # Глубокий голубой
            "natural": (34, 139, 34)   # Лесной зеленый
        }
        
        for risk_type, color in risk_colors.items():
            risk = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.polygon(risk, color, [(20, 0), (40, 20), (20, 40), (0, 20)])
            self.sprites[risk_type] = risk
            
        # Создаем спрайты полисов
        policy_colors = {
            "basic_policy": (0, 0, 255),    # Синий
            "fire_policy": (255, 69, 0),    # Оранжево-красный
            "cyber_policy": (0, 191, 255),  # Глубокий голубой
            "gold_policy": (255, 215, 0)    # Золотой
        }
        
        for policy_type, color in policy_colors.items():
            policy = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(policy, color, (20, 20), 20)
            pygame.draw.circle(policy, (255, 255, 255), (20, 20), 15)
            pygame.draw.circle(policy, color, (20, 20), 10)
            self.sprites[policy_type] = policy
            
        # Создаем спрайт эффекта (щит)
        effect = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.circle(effect, (0, 255, 255, 128), (30, 30), 30)
        self.sprites["effect"] = effect
        
        # Создаем спрайт следа от прыжка
        trail = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(trail, (255, 255, 255, 128), (10, 10), 10)
        self.sprites["jump_trail"] = trail
        
        # Создаем спрайты фоновых объектов
        # Здание
        building = pygame.Surface((100, 150), pygame.SRCALPHA)
        pygame.draw.rect(building, (70, 70, 70), (0, 0, 100, 150))
        pygame.draw.rect(building, (100, 100, 100), (10, 10, 20, 20))
        pygame.draw.rect(building, (100, 100, 100), (70, 10, 20, 20))
        pygame.draw.rect(building, (100, 100, 100), (10, 130, 20, 20))
        pygame.draw.rect(building, (100, 100, 100), (70, 130, 20, 20))
        self.sprites["building"] = building
        
        # Дерево
        tree = pygame.Surface((60, 100), pygame.SRCALPHA)
        pygame.draw.rect(tree, (139, 69, 19), (25, 50, 10, 50))  # Ствол
        pygame.draw.circle(tree, (34, 139, 34), (30, 30), 30)    # Крона
        self.sprites["tree"] = tree
        
        # Облако
        cloud = pygame.Surface((80, 40), pygame.SRCALPHA)
        pygame.draw.ellipse(cloud, (255, 255, 255), (0, 0, 80, 40))
        self.sprites["cloud"] = cloud
        
    def update_background(self, screen_height: int):
        """Обновление позиций фоновых объектов"""
        for obj in self.background_objects:
            obj['y'] += obj['speed']
            if obj['y'] > screen_height:
                obj['y'] = -100
                obj['lane'] = random.randint(0, 3)
                
    def draw_background(self, surface: pygame.Surface):
        """Отрисовка фоновых объектов"""
        for obj in self.background_objects:
            sprite = self.sprites[obj['type']]
            scaled_sprite = pygame.transform.scale(
                sprite,
                (int(sprite.get_width() * obj['scale']),
                 int(sprite.get_height() * obj['scale']))
            )
            x = obj['lane'] * 200 + 100 - scaled_sprite.get_width() // 2
            surface.blit(scaled_sprite, (x, obj['y']))
            
    def draw_sprite(self, surface: pygame.Surface, sprite_type: str, 
                   position: Tuple[int, int], rotation: float = 0, 
                   scale: float = 1.0, shadow: bool = True):
        """Отрисовка спрайта с тенью и поворотом"""
        if sprite_type not in self.sprites:
            return
            
        sprite = self.sprites[sprite_type]
        
        # Отрисовка тени
        if shadow and sprite_type != "shadow":
            shadow_sprite = self.sprites["shadow"]
            shadow_pos = (position[0] - shadow_sprite.get_width()//2,
                         position[1] + sprite.get_height()//2)
            surface.blit(shadow_sprite, shadow_pos)
            
        # Поворот и масштабирование спрайта
        if rotation != 0 or scale != 1.0:
            sprite = pygame.transform.rotozoom(sprite, rotation, scale)
            
        # Отрисовка спрайта
        pos = (position[0] - sprite.get_width()//2,
               position[1] - sprite.get_height()//2)
        surface.blit(sprite, pos)
        
    def draw_jump_trail(self, surface: pygame.Surface, trail_points: List[Tuple[int, int, int]]):
        """Отрисовка следа от прыжка"""
        for x, y, alpha in trail_points:
            trail = self.sprites["jump_trail"].copy()
            trail.set_alpha(alpha)
            pos = (x - trail.get_width()//2, y - trail.get_height()//2)
            surface.blit(trail, pos)
            
    def draw_text(self, surface: pygame.Surface, text: str, 
                 position: Tuple[int, int], size: int = 36, 
                 color: Tuple[int, int, int] = (255, 255, 255)):
        """Отрисовка текста с тенью"""
        font = pygame.font.Font(None, size)
        
        # Тень
        shadow = font.render(text, True, (0, 0, 0))
        surface.blit(shadow, (position[0] + 2, position[1] + 2))
        
        # Основной текст
        text_surface = font.render(text, True, color)
        surface.blit(text_surface, position)
        
    def draw_progress_bar(self, surface: pygame.Surface, 
                         position: Tuple[int, int], size: Tuple[int, int],
                         progress: float, color: Tuple[int, int, int]):
        """Отрисовка прогресс-бара"""
        x, y = position
        width, height = size
        
        # Фон
        pygame.draw.rect(surface, (50, 50, 50), (x, y, width, height))
        # Прогресс
        progress_width = int(width * progress)
        pygame.draw.rect(surface, color, (x, y, progress_width, height))
        # Рамка
        pygame.draw.rect(surface, (200, 200, 200), (x, y, width, height), 2) 