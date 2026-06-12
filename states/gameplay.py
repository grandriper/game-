# Main Gameplay State
import pygame
import random
import threading
import os
import math
from settings import *
from entities.player import Player
from entities.boss import Boss
from entities.rock import Rock
from network.client import submit_score, get_leaderboard, get_my_score
from save import save_game, load_game
from config import asset_path, resource_path
import display

def load_sprite(path, size=None):
    """Safe sprite loader."""
    path = asset_path(path)
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            if size:
                img = pygame.transform.scale(img, size)
            return img
        except Exception as e:
            print(f"ERROR loading {path}: {e}")
    return None

def play_music(track):
    """Switch music track safely."""
    if not pygame.mixer.music.get_busy():
        pygame.mixer.init()
    filename = None
    
    if track == "menu":
        filename = random.choice(MUSIC_MENU)  # Random menu music
    elif track == "game":
        filename = MUSIC_GAME
    elif isinstance(track, int):  # Boss number
        filename = MUSIC_BOSS.get(track, MUSIC_BOSS[1])
    
    filename = resource_path(filename) if filename else None
    if filename and os.path.exists(filename):
        try:
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play(-1)
        except:
            pass

def play_sfx(sfx_file):
    """Play a sound effect (non-blocking)."""
    try:
        sound = pygame.mixer.Sound(resource_path(sfx_file))
        sound.play()
    except:
        pass

def pixel_perfect_collision(player, enemy_rect, player_mask, enemy_mask=None):
    """Pixel-perfect collision detection."""
    if not player_mask:
        return player.rect.colliderect(enemy_rect)
    
    sprite_x, sprite_y = player.get_sprite_pos()
    
    if enemy_mask:
        offset_x = enemy_rect.x - sprite_x
        offset_y = enemy_rect.y - sprite_y
        return player_mask.overlap(enemy_mask, (offset_x, offset_y)) is not None
    else:
        temp_surf = pygame.Surface((enemy_rect.width, enemy_rect.height), pygame.SRCALPHA)
        temp_surf.fill((255, 255, 255, 255))
        temp_mask = pygame.mask.from_surface(temp_surf)
        offset_x = enemy_rect.x - sprite_x
        offset_y = enemy_rect.y - sprite_y
        return player_mask.overlap(temp_mask, (offset_x, offset_y)) is not None

def gameplay_state(screen, clock, font, username, token):
    """Main game loop with all logic."""

    # ─── Load Assets ───
    rock_img = load_sprite("rock.png", (20, 32))
    boss_img = load_sprite("boss1.png", (80, 60))
    bullet2_img = load_sprite("bullet2.png", (12, 24))
    player_bullet_img = load_sprite("bullet.png", (8, 16))
    start_bg = load_sprite("start.png", (WIDTH, HEIGHT))

    # ─── Starfield ───
    stars = []
    for _ in range(300):
        speed = random.choice([1, 2, 3])
        brightness = 150 if speed == 1 else (220 if speed == 2 else 255)
        stars.append({
            "x": random.randint(0, WIDTH),
            "y": random.randint(0, HEIGHT),
            "speed": speed,
            "brightness": brightness
        })

    # ─── Player Setup ───
    ships = [
        {"name": "Alpha", "file": "alpha1.png", "base": "alpha.png"},
        {"name": "Beta",  "file": "beta1.png", "base": "beta.png"},
        {"name": "Pie",   "file": "pie1.png", "base": "pie.png"},
    ]

    # Ship selection
    chosen_ship = 0
    choosing = True
    while choosing:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            display.handle_window_event(event)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: chosen_ship = 0; choosing = False
                if event.key == pygame.K_2: chosen_ship = 1; choosing = False
                if event.key == pygame.K_3: chosen_ship = 2; choosing = False

        if start_bg:
            screen.blit(start_bg, (0, 0))
        else:
            screen.fill(BG)
        title = font.render("CHOOSE YOUR SHIP", True, WHITE)
        screen.blit(title, (WIDTH//2 - 120, HEIGHT//2 - 100))
        for i, ship in enumerate(ships):
            txt = font.render(f"Press {i+1} for {ship['name']}", True, WHITE)
            screen.blit(txt, (WIDTH//2 - 120, HEIGHT//2 + i*40))
        display.present()
        clock.tick(FPS)

    # Load player sprites
    ship = ships[chosen_ship]
    player = Player(0, 0)
    player.rect.center = (WIDTH//2, HEIGHT - 100)

    player.img = load_sprite(ship["base"], (160, 120))
    player.shield_img = load_sprite(ship["file"], (200, 160))
    if player.img:
        player.mask = pygame.mask.from_surface(player.img)
    if player.shield_img:
        player.shield_mask = pygame.mask.from_surface(player.shield_img)

    # ─── Load Progress ───
    progress = load_game(username)
    player_speed = 8 + progress["upgrades"]["speed"]["level"] * progress["upgrades"]["speed"]["effect"]
    shoot_delay = 12 + progress["upgrades"]["fire_rate"]["level"] * progress["upgrades"]["fire_rate"]["effect"]
    player.shield_hp = progress["upgrades"]["shield"]["level"]
    player.shield_max = player.shield_hp

    # ─── Gold: server as source of truth ───
    try:
        s, g = get_my_score(token)
        server_gold = g if s is not None else progress.get("gold", 0)
    except:
        server_gold = progress.get("gold", 0)

    gold = server_gold
    last_synced_gold = [gold]
    gold_sync_timer = 0
    GOLD_SYNC_INTERVAL = 180   # ~3 seconds at 60 FPS

    def sync_gold_to_server():
        if gold != last_synced_gold[0]:
            s, g = score, gold
            threading.Thread(
                target=lambda s=s, g=g: submit_score(token, s, g),
                daemon=True
            ).start()
            last_synced_gold[0] = g

    # ─── Game State ───
    bullets = []
    rocks = []
    boss = None
    boss_bullets = []
    score = 0
    spawn_timer = 0
    game_over = False
    show_hitboxes = False
    show_leaderboard = False
    shoot_cooldown = 0
    next_boss_idx = 0
    leaderboard_data = []
    my_score_data = {"score": 0, "gold": 0}

    # ─── Threading for network ───
    def fetch_leaderboard_thread():
        nonlocal leaderboard_data
        try:
            data = get_leaderboard()
            if data:
                leaderboard_data = data
        except:
            pass

    def fetch_my_score_thread():
        nonlocal my_score_data
        try:
            s, g = get_my_score(token)
            my_score_data = {"score": s or 0, "gold": g or 0}
        except:
            pass

    play_music("game")
    threading.Thread(target=fetch_leaderboard_thread, daemon=True).start()
    threading.Thread(target=fetch_my_score_thread, daemon=True).start()

    # ─── Main Game Loop ───
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sync_gold_to_server()
                progress["gold"] = gold
                progress["high_score"] = max(progress.get("high_score", 0), score)
                save_game(progress, username)
                return
            display.handle_window_event(event)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_h:
                    show_hitboxes = not show_hitboxes
                if event.key == pygame.K_l:
                    show_leaderboard = not show_leaderboard
                    if show_leaderboard:
                        threading.Thread(target=fetch_leaderboard_thread, daemon=True).start()
                        threading.Thread(target=fetch_my_score_thread, daemon=True).start()
                if event.key == pygame.K_b and not boss and not game_over:
                    level = 1 + score // 300
                    if level in BOSS_LEVELS:
                        boss = Boss(level)
                        boss.rect.center = (WIDTH//2, 50)
                        boss.img = boss_img
                        if boss.img:
                            boss.mask = pygame.mask.from_surface(boss.img)
                        boss_num = (level - 3) // 3 + 1
                        play_music(boss_num)
                # Hidden Ctrl+B instant boss spawn
                mods = pygame.key.get_mods()
                if event.key == pygame.K_b and (mods & pygame.KMOD_CTRL) and not boss and not game_over:
                    level = 5
                    boss = Boss(level)
                    boss.rect.center = (WIDTH//2, 50)
                    boss.img = boss_img
                    if boss.img:
                        boss.mask = pygame.mask.from_surface(boss.img)
                    boss_num = (level - 3) // 3 + 1
                    play_music(boss_num)
                if event.key == pygame.K_SPACE and shoot_cooldown == 0 and not game_over:
                    bullets.append(pygame.Rect(player.rect.centerx - 4, player.rect.top - 16, 8, 16))
                    shoot_cooldown = shoot_delay
                    play_sfx(SFX_BULLET)
                if game_over and event.key == pygame.K_r:
                    # Save progress before restarting
                    sync_gold_to_server()
                    progress["gold"] = gold
                    progress["high_score"] = max(progress.get("high_score", 0), score)
                    save_game(progress, username)

                    rocks.clear()
                    bullets.clear()
                    boss = None
                    boss_bullets.clear()
                    score = 0
                    game_over = False
                    next_boss_idx = 0
                    player.rect.center = (WIDTH//2, HEIGHT - 100)
                    player.shield_hp = player.shield_max
                    shoot_cooldown = 0
                    gold_sync_timer = 0
                    last_synced_gold[0] = gold
                    threading.Thread(target=fetch_leaderboard_thread, daemon=True).start()
                    threading.Thread(target=fetch_my_score_thread, daemon=True).start()

        if not game_over and not show_leaderboard:
            # Update player
            keys = pygame.key.get_pressed()
            player.update(keys, WIDTH)

            if shoot_cooldown > 0:
                shoot_cooldown -= 1

            # Spawn rocks
            spawn_timer += 1
            if spawn_timer > max(15, 40 - (score // 300) * 5):
                rocks.append(Rock(random.randint(20, WIDTH - 20), score))
                rocks[-1].img = rock_img
                if rock_img:
                    rocks[-1].mask = pygame.mask.from_surface(rock_img)
                spawn_timer = 0

            # Update rocks
            for rock in rocks[:]:
                rock.update()
                if rock.is_offscreen(HEIGHT):
                    rocks.remove(rock)
                    score += 1
                elif pixel_perfect_collision(player, rock.rect, player.get_mask(), rock.mask):
                    if player.take_damage():
                        game_over = True
                        # Sync gold + score on death
                        threading.Thread(
                            target=lambda s=score, g=gold: submit_score(token, s, g),
                            daemon=True
                        ).start()
                        last_synced_gold[0] = gold
                        progress["gold"] = gold
                        progress["high_score"] = max(progress.get("high_score", 0), score)
                        save_game(progress, username)
                        threading.Thread(target=fetch_leaderboard_thread, daemon=True).start()
                        threading.Thread(target=fetch_my_score_thread, daemon=True).start()
                    else:
                        rocks.remove(rock)

            # Boss spawning
            level = 1 + score // 300
            if not boss and next_boss_idx < len(BOSS_LEVELS) and level >= BOSS_LEVELS[next_boss_idx]:
                boss = Boss(level)
                boss.rect.center = (WIDTH//2, 50)
                boss.img = boss_img
                if boss.img:
                    boss.mask = pygame.mask.from_surface(boss.img)
                boss_num = (level - 3) // 3 + 1
                play_music(boss_num)
                next_boss_idx += 1

            # Boss logic
            if boss:
                boss.update(WIDTH)

                if boss.should_shoot():
                    new_bullets = boss.shoot()
                    boss_bullets.extend(new_bullets)
                    boss.reset_shoot_timer()

                # Boss bullet updates
                for b in boss_bullets[:]:
                    b["rect"].x += b["vx"]
                    b["rect"].y += b["vy"]
                    if b["rect"].top > HEIGHT or b["rect"].right < 0 or b["rect"].left > WIDTH:
                        boss_bullets.remove(b)
                        continue
                    if pixel_perfect_collision(player, b["rect"], player.get_mask()):
                        if player.take_damage():
                            game_over = True
                            threading.Thread(
                            target=lambda s=score, g=gold: submit_score(token, s, g),
                            daemon=True
                        ).start()
                            last_synced_gold[0] = gold
                            progress["gold"] = gold
                            progress["high_score"] = max(progress.get("high_score", 0), score)
                            save_game(progress, username)
                            threading.Thread(target=fetch_leaderboard_thread, daemon=True).start()
                            threading.Thread(target=fetch_my_score_thread, daemon=True).start()
                            break
                        else:
                            boss_bullets.remove(b)

                # Player bullets vs boss
                for bullet in bullets[:]:
                    if bullet.colliderect(boss.rect):
                        bullets.remove(bullet)
                        if boss.take_damage():
                            score += BOSS_DEFEATED_SCORE
                            gold += 100
                            boss = None
                            boss_bullets.clear()
                        break

                if boss and pixel_perfect_collision(player, boss.rect, player.get_mask(), boss.mask):
                    if player.take_damage():
                        game_over = True
                        threading.Thread(
                            target=lambda s=score, g=gold: submit_score(token, s, g),
                            daemon=True
                        ).start()
                        last_synced_gold[0] = gold
                        progress["gold"] = gold
                        progress["high_score"] = max(progress.get("high_score", 0), score)
                        save_game(progress, username)
                        threading.Thread(target=fetch_leaderboard_thread, daemon=True).start()
                        threading.Thread(target=fetch_my_score_thread, daemon=True).start()

            # Player bullets vs rocks
            for bullet in bullets[:]:
                bullet.y -= 7
                if bullet.bottom < 0:
                    bullets.remove(bullet)
                    continue
                for rock in rocks[:]:
                    if bullet.colliderect(rock.rect):
                        if bullet in bullets:
                            bullets.remove(bullet)
                        if rock.take_damage():
                            rocks.remove(rock)
                            score += 1
                            gold += 10
                        break

            # ─── Periodic gold sync ───
            gold_sync_timer += 1
            if gold_sync_timer >= GOLD_SYNC_INTERVAL:
                gold_sync_timer = 0
                sync_gold_to_server()

        # ─── Drawing ───
        screen.fill(BLACK)

        # Starfield
        for star in stars:
            star["y"] += star["speed"]
            if star["y"] > HEIGHT:
                star["y"] = 0
                star["x"] = random.randint(0, WIDTH)
            b = star["brightness"]
            size = star["speed"]
            pygame.draw.rect(screen, (b, b, b), (star["x"], star["y"], size, size))

        # Draw entities
        player.draw(screen)

        if show_hitboxes and player.shield_hp > 0:
            pygame.draw.circle(screen, (0, 100, 255), player.rect.center, 30, 3)

        for rock in rocks:
            rock.draw(screen, font)

        if boss:
            boss.draw(screen)

        for b in boss_bullets:
            if bullet2_img:
                screen.blit(bullet2_img, b["rect"])
            else:
                pygame.draw.rect(screen, (255, 100, 0), b["rect"])

        for bullet in bullets:
            if player_bullet_img:
                screen.blit(player_bullet_img, bullet)
            else:
                pygame.draw.rect(screen, BULLET, bullet)

        # Debug hitboxes
        if show_hitboxes:
            pygame.draw.rect(screen, GREEN, player.rect, 2)
            for rock in rocks:
                pygame.draw.rect(screen, RED, rock.rect, 2)
            if boss:
                pygame.draw.rect(screen, (255, 0, 255), boss.rect, 2)
            for b in boss_bullets:
                pygame.draw.rect(screen, (255, 100, 0), b["rect"], 2)

        # HUD
        score_surf = font.render(f"Score: {score}", True, COIN)
        screen.blit(score_surf, (10, 10))
        gold_surf = font.render(f"Gold: {gold}", True, COIN)
        screen.blit(gold_surf, (10, 50))
        level_surf = font.render(f"Level: {1 + score // 300}", True, WHITE)
        screen.blit(level_surf, (10, 90))
        user_surf = font.render(f"Player: {username}", True, WHITE)
        screen.blit(user_surf, (10, 130))
        if player.shield_hp > 0:
            shield_surf = font.render(f"Shield: {player.shield_hp}", True, (0, 100, 255))
            screen.blit(shield_surf, (10, 170))

        # Leaderboard
        if show_leaderboard:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))

            lb_title = font.render("GLOBAL TOP 10", True, COIN)
            screen.blit(lb_title, (WIDTH//2 - lb_title.get_width()//2, 50))

            header = font.render("Rank  Player          Score      Gold", True, WHITE)
            screen.blit(header, (WIDTH//2 - 250, 100))

            y = 140
            for i, entry in enumerate(leaderboard_data[:10]):
                text = font.render(
                    f"{i+1:<5} {entry['username']:<15} {entry['score']:<10} {entry.get('gold', 0)}",
                    True, WHITE
                )
                screen.blit(text, (WIDTH//2 - 250, y))
                y += 30

            y += 20
            my_header = font.render("Your Stats:", True, COIN)
            screen.blit(my_header, (WIDTH//2 - 250, y))
            y += 30
            my_text = font.render(
                f"Score: {my_score_data['score']}   Gold: {my_score_data['gold']}",
                True, WHITE
            )
            screen.blit(my_text, (WIDTH//2 - 250, y))
            y += 40

            hint = font.render("Press L to close", True, WHITE)
            screen.blit(hint, (WIDTH//2 - 80, y))

        if game_over:
            go = font.render("GAME OVER! Press R to restart", True, BALL)
            screen.blit(go, go.get_rect(center=(WIDTH//2, HEIGHT//2)))

        display.present()
        clock.tick(FPS)
    
    # Save gold when exiting gameplay back to menu
    progress = load_game(username)
    progress["gold"] = gold
    progress["high_score"] = max(progress.get("high_score", 0), score)
    save_game(progress, username)