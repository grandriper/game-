# Shop/Store State
import pygame
import threading
import display
from settings import *
from save import load_game, save_game
from network.client import submit_score, get_my_score

def shop_state(screen, clock, font, username, token):
    """Shop screen for buying upgrades."""
    
    # Load progress
    progress = load_game(username)
    gold = progress["gold"]
    upgrades = progress["upgrades"]

    # Helper to send gold to server
    def sync_gold():
        g = gold
        threading.Thread(
            target=lambda g=g: submit_score(token, 0, g),
            daemon=True
        ).start()

    # On entering the shop, fetch the actual server gold (optional)
    # This ensures the shop shows the correct balance even if local is outdated.
    try:
        s, g = get_my_score(token)
        if s is not None:
            gold = g
    except:
        pass   # keep local gold if offline

    shopping = True
    while shopping:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            display.handle_window_event(event)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                    shopping = False
                
                # Buy upgrades
                if event.key == pygame.K_1:
                    upg = upgrades["speed"]
                    cost = upg["cost"] * (upg["level"] + 1)
                    if gold >= cost:
                        gold -= cost
                        upg["level"] += 1
                        sync_gold()            # <-- tell the server immediately
                
                if event.key == pygame.K_2:
                    upg = upgrades["fire_rate"]
                    cost = upg["cost"] * (upg["level"] + 1)
                    if gold >= cost:
                        gold -= cost
                        upg["level"] += 1
                        sync_gold()
                
                if event.key == pygame.K_3:
                    upg = upgrades["shield"]
                    cost = upg["cost"] * (upg["level"] + 1)
                    if gold >= cost:
                        gold -= cost
                        upg["level"] += 1
                        sync_gold()

        screen.fill(BG)
        
        # Title
        title = font.render("⭐ SHOP - BUY UPGRADES ⭐", True, COIN)
        screen.blit(title, (WIDTH//2 - 200, 30))
        
        # Gold display
        gold_text = font.render(f"💰 Gold: {gold}", True, COIN)
        screen.blit(gold_text, (WIDTH - 300, 30))
        
        # Upgrades list
        y = 120
        for i, (key, upg) in enumerate(upgrades.items(), 1):
            name = key.replace("_", " ").title()
            level = upg["level"]
            cost = upg["cost"] * (level + 1)
            
            upg_text = font.render(f"[{i}] {name}  Level: {level}", True, WHITE)
            screen.blit(upg_text, (100, y))
            
            cost_color = GREEN if gold >= cost else RED
            cost_text = font.render(f"Cost: {cost}", True, cost_color)
            screen.blit(cost_text, (700, y))
            
            y += 60
        
        controls = font.render("Press 1/2/3 to buy | ENTER/ESC to continue", True, YELLOW)
        screen.blit(controls, (WIDTH//2 - 280, HEIGHT - 80))
        
        info = font.render("Speed +1 | Fire Rate -2ms | Shield +1", True, WHITE)
        screen.blit(info, (WIDTH//2 - 250, HEIGHT - 40))
        
        display.present()
        clock.tick(FPS)
    
    # Save to local file as backup
    progress["gold"] = gold
    progress["upgrades"] = upgrades
    save_game(progress, username)
    sync_gold()   # final sync when leaving shop