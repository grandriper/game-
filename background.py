import pygame
import random

# Initialize
pygame.init()

WIDTH = 1280
HEIGHT = 720

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Create stars
stars = []

for _ in range(300):
    stars.append({
        "x": random.randint(0, WIDTH),
        "y": random.randint(0, HEIGHT),
        "speed": random.choice([1, 2, 3])
    })

running = True

while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Black space background
    screen.fill((0, 0, 0))

    # Update and draw stars
    for star in stars:

        star["y"] += star["speed"]

        if star["y"] > HEIGHT:
            star["y"] = 0
            star["x"] = random.randint(0, WIDTH)

        size = star["speed"]

        pygame.draw.rect(
            screen,
            (255, 255, 255),
            (star["x"], star["y"], size, size)
        )

    pygame.display.flip()
    clock.tick(60)

pygame.quit()