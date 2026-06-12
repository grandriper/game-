# Tutorial State
import pygame
import display
from settings import *
from save import load_game, save_game

def tutorial_state(screen, clock, font, username, token):
    """Tutorial/instructions screen."""
    
    tutorial_steps = [
        "🎮 MOVEMENT",
        "Use LEFT/RIGHT arrow keys to move",
        "",
        "🔫 SHOOTING",
        "Press SPACE to shoot at incoming rocks",
        "",
        "⬆️ ROCKS & LEVELS",
        "Destroy rocks to earn points",
        "Every 300 points = new level (harder!)",
        "",
        "🛡️ SHIELD SYSTEM",
        "Shield absorbs one hit (buy in shop)",
        "",
        "👹 BOSS BATTLES",
        "Bosses appear at levels 3, 6, 9, 12, 15",
        "Destroy them for big rewards!",
        "",
        "💰 GOLD & UPGRADES",
        "Earn gold from rocks and bosses",
        "Spend it in shop for Speed/Fire/Shield",
        "",
        "🏆 LEADERBOARD",
        "Press L during game to see top scores",
        "",
        "Press ENTER to start your adventure!"
    ]
    
    tutorial_done = False
    waiting = True
    
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            display.handle_window_event(event)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    waiting = False
                    tutorial_done = True
        
        screen.fill(BG)
        
        # Title
        title = font.render("📖 TUTORIAL - HOW TO PLAY", True, COIN)
        screen.blit(title, title.get_rect(center=(WIDTH//2, 20)))
        
        # Instructions
        y = 70
        for line in tutorial_steps:
            if line == "":
                y += 15
            else:
                # Highlight section headers
                if line.startswith("🎮") or line.startswith("🔫") or line.startswith("⬆️") or \
                   line.startswith("🛡️") or line.startswith("👹") or line.startswith("💰") or \
                   line.startswith("🏆") or line.startswith("⚙️"):
                    txt = font.render(line, True, YELLOW)
                else:
                    txt = font.render(line, True, WHITE)
                
                screen.blit(txt, (50, y))
                y += 30
        
        # Footer
        hint = font.render("Press ENTER to continue", True, GREEN)
        screen.blit(hint, hint.get_rect(center=(WIDTH//2, HEIGHT - 40)))
        
        display.present()
        clock.tick(FPS)
    
    # Save that tutorial is done
    if tutorial_done:
        progress = load_game(username)
        progress["tutorial_done"] = True
        save_game(progress, username)
