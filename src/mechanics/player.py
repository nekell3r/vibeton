import pygame
from typing import List, Tuple, Optional
import math

class Player:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 40
        self.rect = pygame.Rect(x - self.width//2, y - self.height//2, self.width, self.height)
        self.velocity_y = 0
        self.target_y = y  # Целевая позиция по Y
        self.move_speed = 10
        self.lane = 1
        self.lane_height = 150  # Высота одной полосы
        self.is_moving = False
        self.jump_trail = []
        self.is_jumping = False
        self.is_shielded = False
        
    def move(self, direction: int):
        """Перемещение между полосами (direction: -1 вверх, 1 вниз)"""
        new_lane = self.lane + direction
        if 0 <= new_lane <= 3:  # 4 полосы (0-3)
            self.lane = new_lane
            self.target_y = 100 + self.lane * self.lane_height  # 100px отступ сверху
            self.is_moving = True
            
    def set_lane(self, lane: int):
        """Установка полосы напрямую"""
        if 0 <= lane <= 3:
            self.lane = lane
            self.target_y = 100 + lane * self.lane_height
            self.is_moving = True
            
    def update(self):
        """Обновление состояния игрока"""
        # Плавное движение к целевой позиции
        if self.is_moving:
            dy = self.target_y - self.y
            if abs(dy) < self.move_speed:
                self.y = self.target_y
                self.is_moving = False
            else:
                self.y += math.copysign(self.move_speed, dy)
            
        # Обновление прямоугольника
        self.rect.center = (self.x, self.y)
        
        # Обновляем след от движения
        if self.is_moving:
            self.jump_trail.append((self.x, self.y, 255))
            if len(self.jump_trail) > 10:
                self.jump_trail.pop(0)
        
        # Уменьшаем прозрачность следа
        for i in range(len(self.jump_trail)):
            x, y, alpha = self.jump_trail[i]
            self.jump_trail[i] = (x, y, max(0, alpha - 25))
            
        # Удаляем невидимые точки следа
        self.jump_trail = [(x, y, a) for x, y, a in self.jump_trail if a > 0]
        
    def get_position(self) -> Tuple[int, int]:
        return self.rect.center
        
    def activate_shield(self):
        self.is_shielded = True
        
    def deactivate_shield(self):
        self.is_shielded = False 