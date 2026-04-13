import pygame
import math

pygame.init()

screen = pygame.display.set_mode((800, 600))
font = pygame.font.SysFont("Arial", 20)
clock = pygame.time.Clock()

sf26 = pygame.image.load("SF26.png").convert_alpha()
sf26 = pygame.transform.scale(
    sf26,
    (int(sf26.get_width() * 0.1), int(sf26.get_height() * 0.1))
)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 200, 0)
BLUE = (0, 0, 255)
GRAY = (200, 200, 200)

canvas = pygame.Surface((800, 600))
canvas.fill(WHITE)

drawing = False
last_pos = None
start_pos = None
current_pos = None
dragging_shape = False

current_color = BLUE
tool = "brush"
shape = "line"

red_btn = pygame.Rect(20, 20, 60, 40)
green_btn = pygame.Rect(90, 20, 60, 40)
blue_btn = pygame.Rect(160, 20, 60, 40)

eraser_btn = pygame.Rect(250, 20, 100, 40)
brush_btn = pygame.Rect(360, 20, 100, 40)

line_btn = pygame.Rect(490, 20, 80, 40)
circle_btn = pygame.Rect(580, 20, 90, 40)
rect_btn = pygame.Rect(680, 20, 80, 40)

def ui():
    pygame.draw.rect(screen, RED, red_btn)
    pygame.draw.rect(screen, GREEN, green_btn)
    pygame.draw.rect(screen, BLUE, blue_btn)

    pygame.draw.rect(screen, GRAY, eraser_btn)
    pygame.draw.rect(screen, GRAY, brush_btn)
    pygame.draw.rect(screen, GRAY, line_btn)
    pygame.draw.rect(screen, GRAY, circle_btn)
    pygame.draw.rect(screen, GRAY, rect_btn)

    screen.blit(font.render('Red', True, BLACK), (35, 25))
    screen.blit(font.render('Green', True, BLACK), (105, 25))
    screen.blit(font.render('Blue', True, BLACK), (180, 25))

    screen.blit(font.render("erase", True, BLACK), (270, 30))
    screen.blit(font.render("brush", True, BLACK), (380, 30))
    screen.blit(font.render("line", True, BLACK), (510, 30))
    screen.blit(font.render("circle", True, BLACK), (595, 30))
    screen.blit(font.render("rect", True, BLACK), (700, 30))

while True:
    screen.blit(canvas, (0, 0))
    ui()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos

            if red_btn.collidepoint(pos):
                current_color = RED
            elif green_btn.collidepoint(pos):
                current_color = GREEN
            elif blue_btn.collidepoint(pos):
                current_color = BLUE
            elif eraser_btn.collidepoint(pos):
                tool = "eraser"
                print("eraser")
            elif brush_btn.collidepoint(pos):
                tool = "brush"
                print("brush")
            elif line_btn.collidepoint(pos):
                shape = "line"
                print("line")
            elif circle_btn.collidepoint(pos):
                shape = "circle"
                print("circle")
            elif rect_btn.collidepoint(pos):
                shape = "rect"
                print("rect")
            else:
                if tool == "brush" or tool == "eraser":
                    drawing = True
                    last_pos = pos
                else:
                    dragging_shape = True
                    start_pos = pos
                    current_pos = pos

        elif event.type == pygame.MOUSEBUTTONUP:
            if drawing:
                drawing = False
                last_pos = None

            if dragging_shape:
                x1, y1 = start_pos
                x2, y2 = event.pos
                draw_color = WHITE if tool == "eraser" else current_color

                if shape == "rect":
                    left = min(x1, x2)
                    top = min(y1, y2)
                    width = abs(x2 - x1)
                    height = abs(y2 - y1)
                    pygame.draw.rect(canvas, draw_color, (left, top, width, height), 2)

                elif shape == "circle":
                    radius = int(math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2))
                    pygame.draw.circle(canvas, draw_color, start_pos, radius, 2)

                dragging_shape = False
                start_pos = None
                current_pos = None

        elif event.type == pygame.MOUSEMOTION:
            if drawing:
                current_mouse = event.pos
                draw_color = WHITE if tool == "eraser" else current_color

                if last_pos is not None:
                    pygame.draw.line(canvas, draw_color, last_pos, current_mouse, 5)

                last_pos = current_mouse

            elif dragging_shape:
                current_pos = event.pos

    screen.blit(canvas, (0, 0))
    ui()

    if dragging_shape and start_pos and current_pos:
        x1, y1 = start_pos
        x2, y2 = current_pos
        draw_color = WHITE if tool == "eraser" else current_color

        if shape == "rect":
            left = min(x1, x2)
            top = min(y1, y2)
            width = abs(x2 - x1)
            height = abs(y2 - y1)
            pygame.draw.rect(screen, draw_color, (left, top, width, height), 2)

        elif shape == "circle":
            radius = int(math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2))
            pygame.draw.circle(screen, draw_color, start_pos, radius, 2)

    pygame.display.update()
    clock.tick(60)