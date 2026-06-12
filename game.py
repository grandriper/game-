# Main Game Loop
import pygame
import sys
from settings import WIDTH, HEIGHT, FPS, BG, MUSIC_MENU
from states.login import login_state
from states.gameplay import gameplay_state
from states.shop import shop_state
from states.tutorial import tutorial_state
from save import migrate_legacy_save
from config import resource_path
import display
import random
import os

pygame.init()
pygame.mixer.init()

screen, game_surface = display.init_display()
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

def play_menu_music():
    """Play random menu music."""
    try:
        music_file = resource_path(random.choice(MUSIC_MENU))
        if os.path.exists(music_file):
            pygame.mixer.music.load(music_file)
            pygame.mixer.music.play(-1)
    except:
        pass

def main():
    """Main game loop."""
    username, token = None, None
    
    migrate_legacy_save()

    # Login state
    username, token = login_state(game_surface, clock, font)
    if not username or not token:
        print("❌ Login failed")
        pygame.quit()
        sys.exit()

    print(f"✅ Welcome, {username}!")
    
    # Main loop - keep returning to menu
    while True:
        current_state = "menu"
        
        play_menu_music()
        
        menu_running = True
        while menu_running and pygame.display.get_surface():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                display.handle_window_event(event)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        current_state = "gameplay"
                        menu_running = False
                    elif event.key == pygame.K_2:
                        current_state = "shop"
                        menu_running = False
                    elif event.key == pygame.K_3:
                        current_state = "tutorial"
                        menu_running = False
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
            
            game_surface.fill(BG)
            title = font.render("Main Menu", True, (255, 255, 255))
            game_surface.blit(title, title.get_rect(center=(WIDTH//2, 100)))
            
            opt1 = font.render("1 - Start Game", True, (0, 255, 0))
            opt2 = font.render("2 - Shop", True, (0, 255, 0))
            opt3 = font.render("3 - Tutorial", True, (0, 255, 0))
            opt4 = font.render("ESC - Quit", True, (255, 0, 0))
            
            game_surface.blit(opt1, opt1.get_rect(center=(WIDTH//2, 200)))
            game_surface.blit(opt2, opt2.get_rect(center=(WIDTH//2, 250)))
            game_surface.blit(opt3, opt3.get_rect(center=(WIDTH//2, 300)))
            game_surface.blit(opt4, opt4.get_rect(center=(WIDTH//2, 400)))
            
            display.present()
            clock.tick(FPS)
        
        # Run selected state
        if current_state == "gameplay":
            pygame.mixer.music.stop()
            gameplay_state(game_surface, clock, font, username, token)
        elif current_state == "shop":
            shop_state(game_surface, clock, font, username, token)
        elif current_state == "tutorial":
            tutorial_state(game_surface, clock, font, username, token)

if __name__ == '__main__':
    main()
