import pygame
from typing import Dict, List, Callable, Optional
from enum import Enum

class MenuState(Enum):
    MAIN = "main"
    PAUSE = "pause"
    GAME_OVER = "game_over"
    SETTINGS = "settings"

class Button:
    def __init__(self, x: int, y: int, width: int, height: int, text: str, 
                 action: Callable[[], None], color: tuple = (200, 200, 200)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.color = color
        self.hover_color = (min(color[0] + 30, 255), 
                          min(color[1] + 30, 255), 
                          min(color[2] + 30, 255))
        self.is_hovered = False
        self.font = pygame.font.Font(None, 36)

    def draw(self, surface: pygame.Surface) -> None:
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2)
        
        text_surface = self.font.render(self.text, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                self.action()
                return True
        return False

class Menu:
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.current_state = MenuState.MAIN
        self.buttons: Dict[MenuState, List[Button]] = {
            MenuState.MAIN: [],
            MenuState.PAUSE: [],
            MenuState.GAME_OVER: [],
            MenuState.SETTINGS: []
        }
        self._create_buttons()

    def _create_buttons(self) -> None:
        """Создание кнопок для всех меню"""
        # Главное меню
        self.buttons[MenuState.MAIN].extend([
            Button(self.screen_width//2 - 100, 200, 200, 50, "Играть", 
                  lambda: self.set_state(MenuState.MAIN)),
            Button(self.screen_width//2 - 100, 300, 200, 50, "Настройки", 
                  lambda: self.set_state(MenuState.SETTINGS)),
            Button(self.screen_width//2 - 100, 400, 200, 50, "Выход", 
                  lambda: pygame.quit())
        ])

        # Меню паузы
        self.buttons[MenuState.PAUSE].extend([
            Button(self.screen_width//2 - 100, 200, 200, 50, "Продолжить", 
                  lambda: self.set_state(MenuState.MAIN)),
            Button(self.screen_width//2 - 100, 300, 200, 50, "Настройки", 
                  lambda: self.set_state(MenuState.SETTINGS)),
            Button(self.screen_width//2 - 100, 400, 200, 50, "Выход в меню", 
                  lambda: self.set_state(MenuState.MAIN))
        ])

        # Меню окончания игры
        self.buttons[MenuState.GAME_OVER].extend([
            Button(self.screen_width//2 - 100, 200, 200, 50, "Играть снова", 
                  lambda: self.set_state(MenuState.MAIN)),
            Button(self.screen_width//2 - 100, 300, 200, 50, "Главное меню", 
                  lambda: self.set_state(MenuState.MAIN))
        ])

        # Меню настроек
        self.buttons[MenuState.SETTINGS].extend([
            Button(self.screen_width//2 - 100, 200, 200, 50, "Звук: Вкл", 
                  lambda: None),  # Добавить переключение звука
            Button(self.screen_width//2 - 100, 300, 200, 50, "Назад", 
                  lambda: self.set_state(MenuState.MAIN))
        ])

    def set_state(self, state: MenuState) -> None:
        """Установка текущего состояния меню"""
        self.current_state = state

    def handle_event(self, event: pygame.event.Event) -> None:
        """Обработка событий меню"""
        for button in self.buttons[self.current_state]:
            if button.handle_event(event):
                break

    def draw(self, surface: pygame.Surface) -> None:
        """Отрисовка текущего меню"""
        # Полупрозрачный фон
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        surface.blit(overlay, (0, 0))

        # Отрисовка кнопок
        for button in self.buttons[self.current_state]:
            button.draw(surface)

        # Заголовок меню
        font = pygame.font.Font(None, 74)
        title = {
            MenuState.MAIN: "Полис-Бот",
            MenuState.PAUSE: "Пауза",
            MenuState.GAME_OVER: "Игра окончена",
            MenuState.SETTINGS: "Настройки"
        }[self.current_state]
        
        title_surface = font.render(title, True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(self.screen_width//2, 100))
        surface.blit(title_surface, title_rect) 