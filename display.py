# Resizable window — game renders at fixed size, scales to fit the window
import pygame
from settings import WIDTH, HEIGHT, BG, TITLE

MIN_WIDTH = 800
MIN_HEIGHT = 600

_screen = None
_game_surface = None


def init_display():
    """Create resizable window and fixed-size game surface."""
    global _screen, _game_surface
    pygame.display.set_caption(TITLE)
    _screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    _game_surface = pygame.Surface((WIDTH, HEIGHT))
    return _screen, _game_surface


def get_game_surface():
    return _game_surface


def handle_resize(event=None):
    """Keep window resizable above a minimum size."""
    global _screen
    if event and hasattr(event, "w") and hasattr(event, "h"):
        w, h = event.w, event.h
    else:
        w, h = _screen.get_size()
    w = max(MIN_WIDTH, w)
    h = max(MIN_HEIGHT, h)
    _screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)


def _scale_info():
    sw, sh = _screen.get_size()
    scale = min(sw / WIDTH, sh / HEIGHT)
    scaled_w = int(WIDTH * scale)
    scaled_h = int(HEIGHT * scale)
    offset_x = (sw - scaled_w) // 2
    offset_y = (sh - scaled_h) // 2
    return scale, offset_x, offset_y, scaled_w, scaled_h


def present():
    """Scale game surface to window (letterboxed) and flip."""
    scale, ox, oy, sw, sh = _scale_info()
    scaled = pygame.transform.scale(_game_surface, (sw, sh))
    _screen.fill(BG)
    _screen.blit(scaled, (ox, oy))
    pygame.display.flip()


def map_mouse(pos):
    """Map window mouse coordinates to game coordinates."""
    scale, ox, oy, _, _ = _scale_info()
    return (
        int((pos[0] - ox) / scale),
        int((pos[1] - oy) / scale),
    )


def _resize_event_types():
    """Resize events differ between pygame and pygame-ce."""
    types = {pygame.VIDEORESIZE}
    for name in ("WINDOWRESIZED", "WINDOWSIZECHANGED"):
        if hasattr(pygame, name):
            types.add(getattr(pygame, name))
    return types


def handle_window_event(event):
    """Call from state event loops. Returns True if event was consumed."""
    if event.type in _resize_event_types():
        handle_resize(event)
        return True
    return False
