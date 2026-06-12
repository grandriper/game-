# Player Entity
import pygame
from settings import (
    HITBOX_W, HITBOX_H,
    OFFSET_X, OFFSET_Y,
    SHIELD_OFFSET_X, SHIELD_OFFSET_Y,
)

class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, HITBOX_W, HITBOX_H)
        self.speed = 8
        self.shield_hp = 0
        self.shield_max = 0
        
        # Sprite management
        self.img = None
        self.shield_img = None
        self.mask = None
        self.shield_mask = None
        self.anim_frames = []
        self.shield_anim_frames = []
        self.anim_timer = 0
        self.anim_index = 0
    
    def update(self, keys, width):
        """Update player position."""
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < width:
            self.rect.x += self.speed
        
        if self.anim_frames or self.shield_anim_frames:
            self.anim_timer += 1
            if self.anim_timer >= 10:
                self.anim_timer = 0
                if self.shield_hp > 0 and self.shield_anim_frames:
                    self.anim_index = (self.anim_index + 1) % len(self.shield_anim_frames)
                elif self.anim_frames:
                    self.anim_index = (self.anim_index + 1) % len(self.anim_frames)
    
    def draw(self, screen):
        """Draw the player."""
        if self.shield_hp > 0 and self.shield_img:
            if self.shield_anim_frames:
                sprite = self.shield_anim_frames[self.anim_index % len(self.shield_anim_frames)]
            else:
                sprite = self.shield_img
            screen.blit(sprite, (self.rect.x + SHIELD_OFFSET_X, self.rect.y + SHIELD_OFFSET_Y))
        elif self.img:
            if self.anim_frames:
                sprite = self.anim_frames[self.anim_index % len(self.anim_frames)]
            else:
                sprite = self.img
            screen.blit(sprite, (self.rect.x + OFFSET_X, self.rect.y + OFFSET_Y))
        else:
            pygame.draw.rect(screen, (0, 220, 255), self.rect, border_radius=8)
    
    def get_sprite_pos(self):
        """Top-left draw position for the active sprite (matches collision)."""
        if self.shield_hp > 0 and self.shield_img:
            return self.rect.x + SHIELD_OFFSET_X, self.rect.y + SHIELD_OFFSET_Y
        return self.rect.x + OFFSET_X, self.rect.y + OFFSET_Y

    def get_mask(self):
        """Get current collision mask."""
        if self.shield_hp > 0 and self.shield_mask:
            return self.shield_mask
        return self.mask
    
    def take_damage(self):
        """Take damage. Returns True if dead."""
        if self.shield_hp > 0:
            self.shield_hp -= 1
            return False
        return True
