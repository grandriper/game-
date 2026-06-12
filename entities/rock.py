# Rock/Projectile Entity
import pygame

class Rock:
    def __init__(self, x, score):
        import random
        from settings import BALL
        
        self.rect = pygame.Rect(x, -32, 20, 32)
        level_bonus = (score // 300) * 0.8
        
        if random.random() < 0.25:
            self.hp = 2
            self.color = BALL
            self.speed = random.uniform(2, 4) + level_bonus
        else:
            self.hp = 1
            self.color = (120, 220, 255)
            self.speed = random.uniform(4, 8) + level_bonus
        
        self.img = None
        self.mask = None
    
    def update(self):
        """Update rock position."""
        self.rect.y += self.speed
    
    def draw(self, screen, font=None):
        """Draw the rock."""
        if self.img:
            screen.blit(self.img, self.rect)
        else:
            pygame.draw.ellipse(screen, self.color, self.rect)
        
        if self.hp > 1 and font:
            hp_surf = font.render(str(self.hp), True, (255, 255, 255))
            screen.blit(hp_surf, hp_surf.get_rect(center=self.rect.center))
    
    def is_offscreen(self, height):
        """Check if rock is off-screen."""
        return self.rect.top > height
    
    def take_damage(self, dmg=1):
        """Take damage."""
        self.hp -= dmg
        return self.hp <= 0
