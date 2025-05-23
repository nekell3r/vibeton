import pygame
import sys
import random
import math
from typing import List, Dict, Tuple
from mechanics.player import Player
from systems.risks import Risk, RiskType
from systems.policies import Policy, PolicyType
from visuals.sprites import SpriteManager
from ui.menus import Menu, MenuState
import pygame.gfxdraw

class Game:
    def __init__(self):
        pygame.init()
        self.width = 800
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Полис-Бот: Минималка")
        
        # Инициализация менеджера спрайтов
        self.sprite_manager = SpriteManager()
        
        # Создание фона с градиентом
        self.background = pygame.Surface((self.width, self.height))
        self._create_gradient_background()
        
        # Инициализация игрока
        self.lane_count = 4
        self.lane_height = (self.height - 200) // self.lane_count  # Оставляем место сверху и снизу
        self.player = Player(100, 100 + self.lane_height * 1)  # Начинаем со второй полосы
        self.player.lane_height = self.lane_height
        self.player.lane = 1
        
        # Списки рисков и полисов
        self.risks: List[Risk] = []
        self.policies: List[Policy] = []
        
        # Активные полисы
        self.active_policies: Dict[str, int] = {}
        
        # Игровые параметры
        self.score = 0
        self.budget = 1000
        self.game_over = False
        self.clock = pygame.time.Clock()
        
        # Меню
        self.menu = Menu(self.width, self.height)
        self.menu_state = MenuState.MAIN
        
        # Шрифт для текста
        self.font = pygame.font.Font(None, 36)
        
    def _create_gradient_background(self):
        """Создание градиентного фона"""
        for y in range(self.height):
            # Более тёмный градиент сверху вниз
            color = (
                int(30 + (y / self.height) * 40),
                int(60 + (y / self.height) * 50),
                int(120 + (y / self.height) * 50)
            )
            pygame.draw.line(self.background, color, (0, y), (self.width, y))
    
    def handle_events(self):
        """Обработка событий"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.menu_state == MenuState.MAIN:
                        return False
                    else:
                        self.menu_state = MenuState.MAIN
                if event.key == pygame.K_UP:
                    self.player.move(-1)  # Движение вверх
                if event.key == pygame.K_DOWN:
                    self.player.move(1)   # Движение вниз
        return True
    
    def spawn_objects(self):
        """Создание новых рисков и полисов"""
        if random.random() < 0.02:
            risk_type = random.choice(list(RiskType))
            lane = random.randint(0, self.lane_count - 1)
            y = 100 + lane * self.lane_height + self.lane_height // 2
            risk = Risk(risk_type, self.width + 50, y)
            risk.lane = lane
            risk.speed = 5
            self.risks.append(risk)
            
        if random.random() < 0.01:
            policy_type = random.choice(list(PolicyType))
            lane = random.randint(0, self.lane_count - 1)
            y = 100 + lane * self.lane_height + self.lane_height // 2
            policy = Policy(policy_type, self.width + 50, y)
            policy.lane = lane
            policy.speed = 5
            self.policies.append(policy)
    
    def update_active_policies(self):
        """Обновление активных полисов"""
        for policy_type in list(self.active_policies.keys()):
            self.active_policies[policy_type] -= 1
            if self.active_policies[policy_type] <= 0:
                del self.active_policies[policy_type]
    
    def update(self):
        """Обновление состояния игры"""
        if self.menu_state != MenuState.MAIN:
            return
            
        self.player.update()
        self.sprite_manager.update_background(self.width)
        self.spawn_objects()
        
        # Обновление рисков
        for risk in self.risks[:]:
            risk.x -= risk.speed
            risk.rect.x = risk.x
            if risk.x < -50:
                self.risks.remove(risk)
            elif risk.rect.colliderect(self.player.rect):
                required_policy = risk.get_required_policy()
                if required_policy in self.active_policies:
                    self.score += risk.get_score_value()
                else:
                    self.budget -= risk.get_damage()
                    if self.budget <= 0:
                        self.game_over = True
                self.risks.remove(risk)
                
        # Обновление полисов
        for policy in self.policies[:]:
            policy.x -= policy.speed
            policy.rect.x = policy.x
            if policy.x < -50:
                self.policies.remove(policy)
            elif policy.rect.colliderect(self.player.rect):
                self.active_policies[policy.policy_type.value] = policy.get_duration()
                self.score += policy.get_score_value()
                self.policies.remove(policy)
                
        self.update_active_policies()
    
    def draw(self):
        """Отрисовка игры"""
        self.screen.blit(self.background, (0, 0))
        self.sprite_manager.draw_background(self.screen)
        
        # Отрисовка разделителей полос (мягкие линии)
        for i in range(self.lane_count + 1):
            y = 100 + i * self.lane_height
            # Основная линия
            pygame.gfxdraw.hline(self.screen, 0, self.width, y, (255, 255, 255, 40))
            # Мягкое свечение
            for offset in range(1, 3):
                alpha = 20 - offset * 5
                pygame.gfxdraw.hline(self.screen, 0, self.width, y + offset, (255, 255, 255, alpha))
                pygame.gfxdraw.hline(self.screen, 0, self.width, y - offset, (255, 255, 255, alpha))
        
        # Риски
        for risk in self.risks:
            risk.draw(self.screen, self.sprite_manager)
            
        # Полисы
        for policy in self.policies:
            policy.draw(self.screen, self.sprite_manager)
            
        # Игрок и его след
        if self.player.jump_trail:
            self.sprite_manager.draw_jump_trail(self.screen, self.player.jump_trail)
        self.sprite_manager.draw_sprite(
            self.screen,
            "player",
            (self.player.rect.centerx, self.player.rect.centery)
        )
        
        # HUD
        # Счёт
        score_text = self.font.render(f"Счет: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (20, 20))
        
        # Бюджет с цветовой индикацией
        budget_color = (0, 255, 0) if self.budget > 500 else (255, 165, 0) if self.budget > 200 else (255, 0, 0)
        budget_text = self.font.render(f"Бюджет: {self.budget}", True, budget_color)
        self.screen.blit(budget_text, (20, 60))
        
        # Прогресс-бар бюджета
        budget_progress = min(self.budget / 1000, 1.0)
        pygame.draw.rect(self.screen, (50, 50, 50), (20, 90, 150, 10))
        if budget_progress > 0:
            pygame.draw.rect(self.screen, budget_color, (20, 90, int(150 * budget_progress), 10))
        
        # Активные полисы
        y_offset = 120
        for policy_type, duration in self.active_policies.items():
            # Иконка полиса
            self.sprite_manager.draw_sprite(
                self.screen,
                policy_type,
                (40, y_offset),
                scale=0.5
            )
            # Прогресс-бар длительности
            max_duration = 30
            progress = duration / max_duration
            pygame.draw.rect(self.screen, (50, 50, 50), (60, y_offset - 5, 100, 10))
            if progress > 0:
                pygame.draw.rect(self.screen, (0, 255, 0), (60, y_offset - 5, int(100 * progress), 10))
            y_offset += 30
        
        if self.menu_state != MenuState.MAIN:
            self.menu.draw(self.screen)
            
        pygame.display.flip()
    
    def run(self):
        """Запуск игры"""
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run() 