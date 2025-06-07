import pygame
import random
import math

class Particle:
    def __init__(self, x, y, color, size, speed_x, speed_y, gravity, lifetime):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.gravity = gravity
        self.lifetime = lifetime
        self.life = 0

    def update(self, dt):
        self.life += dt
        if self.life >= self.lifetime:
            return False

        self.speed_y += self.gravity * dt
        self.x += self.speed_x * dt
        self.y += self.speed_y * dt
        self.size = max(1, self.size - 2 * dt)
        return True

    def draw(self, surface, offset_x=0, offset_y=0):
        if self.size >= 1:
            pygame.draw.circle(surface, self.color, (int(self.x + offset_x), int(self.y + offset_y)), int(self.size))

def create_explosion(x, y, color, count=20, base_speed=100, lifetime=0.5, gravity=300):
    particles = []
    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(base_speed * 0.5, base_speed * 1.5)
        speed_x = math.cos(angle) * speed
        speed_y = math.sin(angle) * speed
        size = random.uniform(3, 7)
        p_color = (max(0, min(255, color[0] + random.randint(-20, 20))),
                   max(0, min(255, color[1] + random.randint(-20, 20))),
                   max(0, min(255, color[2] + random.randint(-20, 20))))
        particles.append(Particle(x, y, p_color, size, speed_x, speed_y, gravity, lifetime))
    return particles

# Глобальные переменные для эффектов
screen_shake_amount = 0
screen_shake_timer = 0

def apply_screen_shake(duration=0.2, intensity=5):
    global screen_shake_timer, screen_shake_amount
    screen_shake_timer = duration
    screen_shake_amount = intensity

def update_screen_shake(dt):
    global screen_shake_timer, screen_shake_amount
    if screen_shake_timer > 0:
        screen_shake_timer -= dt
        if screen_shake_timer <= 0:
            screen_shake_amount = 0
        return (random.randint(-screen_shake_amount, screen_shake_amount),
                random.randint(-screen_shake_amount, screen_shake_amount))
    return (0, 0) 