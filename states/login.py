# Login/Register Screen State
import pygame
import display
import threading
import time
from network.client import try_login, try_register, check_server_status
from settings import *
from config import BASE_URL

SERVER_CHECK_INTERVAL = 5  # seconds between background status checks

def is_password_strong(pwd):
    """Password must be at least 6 characters and contain upper, lower, and digit."""
    if len(pwd) < 6:
        return False
    has_upper = any(c.isupper() for c in pwd)
    has_lower = any(c.islower() for c in pwd)
    has_digit = any(c.isdigit() for c in pwd)
    return has_upper and has_lower and has_digit

def login_state(screen, clock, font):
    """Handle login/register screen."""
    username = ""
    password = ""
    confirm = ""
    mode = "login"  # 'login' or 'register'
    active_field = "username"
    message = ""

    server_status = {"online": None, "last_check": 0.0}
    status_checking = {"active": False}

    def refresh_server_status():
        if status_checking["active"]:
            return
        status_checking["active"] = True

        def worker():
            try:
                server_status["online"] = check_server_status()
            finally:
                server_status["last_check"] = time.time()
                status_checking["active"] = False

        threading.Thread(target=worker, daemon=True).start()

    refresh_server_status()

    static_cache = {}

    def static_text(key, text, color):
        if key not in static_cache:
            static_cache[key] = font.render(text, True, color)
        return static_cache[key]

    field_x = WIDTH // 2 - 110
    username_rect = pygame.Rect(field_x, 205, 220, 35)
    password_rect = pygame.Rect(field_x, 265, 220, 35)
    confirm_rect = pygame.Rect(field_x, 325, 220, 35)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None, None

            display.handle_window_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = display.map_mouse(event.pos)
                if username_rect.collidepoint(pos):
                    active_field = "username"
                elif password_rect.collidepoint(pos):
                    active_field = "password"
                elif mode == "register" and confirm_rect.collidepoint(pos):
                    active_field = "confirm"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:
                    mode = "register" if mode == "login" else "login"
                    message = ""
                    active_field = "username"
                    static_cache.clear()

                elif event.key == pygame.K_TAB:
                    if mode == "login":
                        active_field = "password" if active_field == "username" else "username"
                    else:
                        if active_field == "username":
                            active_field = "password"
                        elif active_field == "password":
                            active_field = "confirm"
                        else:
                            active_field = "username"

                elif event.key == pygame.K_RETURN:
                    if not username.strip():
                        message = "Username cannot be empty"
                    elif mode == "login":
                        if not password.strip():
                            message = "Password cannot be empty"
                        else:
                            token = try_login(username, password)
                            if token:
                                print(f"✅ Logged in as: {username}")
                                return username, token
                            else:
                                message = "Invalid credentials"
                    else:  # Register mode
                        if not password.strip():
                            message = "Password cannot be empty"
                        elif password != confirm:
                            message = "Passwords do not match"
                        elif not is_password_strong(password):
                            message = "Password: 6+ chars, upper, lower, digit"
                        else:
                            if try_register(username, password):
                                token = try_login(username, password)
                                if token:
                                    print(f"✅ Registered & logged in as: {username}")
                                    return username, token
                                else:
                                    message = "Registration ok, but login failed"
                            else:
                                message = "Username already taken"

                elif event.key == pygame.K_BACKSPACE:
                    if active_field == "username":
                        username = username[:-1]
                    elif active_field == "password":
                        password = password[:-1]
                    elif active_field == "confirm":
                        confirm = confirm[:-1]

                elif event.unicode.isprintable():
                    if active_field == "username":
                        username += event.unicode
                    elif active_field == "password":
                        password += event.unicode
                    elif active_field == "confirm":
                        confirm += event.unicode

        if time.time() - server_status["last_check"] >= SERVER_CHECK_INTERVAL:
            refresh_server_status()

        # Drawing
        screen.fill(BG)

        title_txt = "LOGIN" if mode == "login" else "REGISTER"
        title_surf = static_text(f"title_{mode}", title_txt, WHITE)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH//2, 100)))

        hint_surf = static_text("hint", "F1 switch mode | TAB/click change field", WHITE)
        screen.blit(hint_surf, hint_surf.get_rect(center=(WIDTH//2, 150)))

        if server_status["online"] is None:
            server_label, server_color = "checking...", YELLOW
        elif server_status["online"]:
            server_label, server_color = "online", GREEN
        else:
            server_label, server_color = "offline", RED
        server_txt = static_text(
            f"server_{server_label}",
            f"Server: {server_label} ({BASE_URL})",
            server_color,
        )
        screen.blit(server_txt, server_txt.get_rect(center=(WIDTH//2, 180)))

        ucol = ACTIVE if active_field == "username" else INACTIVE
        pygame.draw.rect(screen, ucol, username_rect, 3 if active_field == "username" else 1)
        screen.blit(
            static_text("user_label", "Username:", WHITE),
            (username_rect.x - 150, username_rect.y + 5),
        )
        screen.blit(font.render(username, True, WHITE), (username_rect.x + 5, username_rect.y + 5))

        pcol = ACTIVE if active_field == "password" else INACTIVE
        pygame.draw.rect(screen, pcol, password_rect, 3 if active_field == "password" else 1)
        screen.blit(
            static_text("pass_label", "Password:", WHITE),
            (password_rect.x - 150, password_rect.y + 5),
        )
        screen.blit(
            font.render("*" * len(password), True, WHITE),
            (password_rect.x + 5, password_rect.y + 5),
        )

        if mode == "register":
            ccol = ACTIVE if active_field == "confirm" else INACTIVE
            pygame.draw.rect(screen, ccol, confirm_rect, 3 if active_field == "confirm" else 1)
            screen.blit(
                static_text("conf_label", "Confirm:", WHITE),
                (confirm_rect.x - 150, confirm_rect.y + 5),
            )
            screen.blit(
                font.render("*" * len(confirm), True, WHITE),
                (confirm_rect.x + 5, confirm_rect.y + 5),
            )

        btn_text = "LOGIN" if mode == "login" else "REGISTER"
        btn = static_text(f"btn_{mode}", f"Press ENTER to {btn_text}", GREEN)
        screen.blit(btn, btn.get_rect(center=(WIDTH//2, 400)))

        if message:
            msg = font.render(message, True, YELLOW)
            screen.blit(msg, msg.get_rect(center=(WIDTH//2, 450)))

        display.present()
        clock.tick(FPS)
