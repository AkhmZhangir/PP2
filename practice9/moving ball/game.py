import pygame
import sys

pygame.init()

WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Moving Ball Game")

clock = pygame.time.Clock()

WHITE = (255, 255, 255)
RED = (255, 0, 0)

ball_radius = 25
ball_x = 100
ball_y = 100
step = 20

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                if ball_x - step - ball_radius >= 0:
                    ball_x -= step

            elif event.key == pygame.K_RIGHT:
                if ball_x + step + ball_radius <= WIDTH:
                    ball_x += step

            elif event.key == pygame.K_UP:
                if ball_y - step - ball_radius >= 0:
                    ball_y -= step

            elif event.key == pygame.K_DOWN:
                if ball_y + step + ball_radius <= HEIGHT:
                    ball_y += step

    screen.fill(WHITE)
    pygame.draw.circle(screen, RED, (ball_x, ball_y), ball_radius)
    pygame.display.update()
    clock.tick(60)

pygame.quit()
sys.exit()