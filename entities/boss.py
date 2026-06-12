# Boss Entity
import pygame
import math

class Boss:
    def __init__(self, level):
        boss_num = (level - 3) // 3 + 1
        self.hp = 10 + (boss_num - 1) * 5
        self.max_hp = self.hp
        self.speed = 2 + boss_num
        self.shoot_delay = max(30, 60 - boss_num * 5)
        self.shoot_timer = 0
        self.direction = 1
        self.spread_count = 3 + boss_num - 1
        self.rect = pygame.Rect(0, 0, 80, 60)  # Will be set by caller
        
        self.img = None
        self.mask = None
    
    def update(self, width):
        """Update boss position."""
        self.rect.x += self.speed * self.direction
        if self.rect.right >= width or self.rect.left <= 0:
            self.direction *= -1
        
        self.shoot_timer += 1
    
    def should_shoot(self):
        """Check if boss should shoot."""
        return self.shoot_timer >= self.shoot_delay
    
    def reset_shoot_timer(self):
        """Reset shoot timer after firing."""
        self.shoot_timer = 0
    
    def shoot(self):
        """Generate bullets. Returns list of bullet dicts."""
        bullets = []
        cx = self.rect.centerx
        cy = self.rect.bottom
        spread_angle = 30
        for i in range(self.spread_count):
            angle = -spread_angle/2 + i * spread_angle / max(1, self.spread_count-1)
            rad = math.radians(angle)
            vx = math.sin(rad) * 4
            vy = math.cos(rad) * 5
            bullets.append({
                "rect": pygame.Rect(cx - 6, cy, 12, 24),
                "vx": vx,
                "vy": vy
            })
        return bullets
    
    def draw(self, screen):
        """Draw the boss."""
        if self.img:
            screen.blit(self.img, self.rect)
        else:
            pygame.draw.rect(screen, (255, 0, 0), self.rect)
        
        # Health bar
        bar_width = 80
        bar_height = 6
        health_ratio = self.hp / self.max_hp
        pygame.draw.rect(screen, (255, 0, 0), (self.rect.x, self.rect.top - 10, bar_width, bar_height))
        pygame.draw.rect(screen, (80, 255, 80), (self.rect.x, self.rect.top - 10, bar_width * health_ratio, bar_height))
    
    def take_damage(self, dmg=1):
        """Take damage."""
        self.hp -= dmg
        return self.hp <= 0
