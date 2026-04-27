import pygame
import math

pygame.init()



screen = pygame.display.set_mode((1500,600))
pygame.display.set_caption("Mini Paint")

font = pygame.font.SysFont("Arial", 20)
clock = pygame.time.Clock()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 200, 0)
BLUE = (0, 0, 255)
GRAY = (200, 200, 200)
DARK_GRAY = (140, 140, 140)

canvas = pygame.Surface((1500,600))
canvas.fill(WHITE)

drawing = False
start_pos = (0, 0)
current_pos = (0, 0)
last_pos = None
current_rect = None

current_color = BLUE
tool = "brush"

red_btn = pygame.Rect(20, 20, 60, 40)
green_btn = pygame.Rect(90, 20, 60, 40)
blue_btn = pygame.Rect(160, 20, 60, 40)

brush_btn = pygame.Rect(260, 20, 90, 40)
eraser_btn = pygame.Rect(360, 20, 90, 40)
line_btn = pygame.Rect(460, 20, 90, 40)
rect_btn = pygame.Rect(560, 20, 90, 40)
circle_btn = pygame.Rect(660, 20, 90, 40)
square_btn = pygame.Rect(760, 20, 90, 40)

rtriangle_btn = pygame.Rect(860, 20, 130, 40)
etriangle_btn = pygame.Rect(1000, 20, 130, 40)
rhombus_btn = pygame.Rect(1140, 20, 110, 40)
clear_btn = pygame.Rect(1260, 20, 90, 40)

def draw_button(rect, text, bg_color, active=False):
    color = DARK_GRAY if active else bg_color
    pygame.draw.rect(screen, color, rect)
    pygame.draw.rect(screen, BLACK, rect, 2)
    txt = font.render(text, True, BLACK)
    txt_rect = txt.get_rect(center=rect.center)
    screen.blit(txt, txt_rect)

def draw_ui():
    pygame.draw.rect(screen, (230, 230, 230), (0, 0, 1400, 80))

    draw_button(red_btn, "Red", RED, current_color == RED)
    draw_button(green_btn, "Green", GREEN, current_color == GREEN)
    draw_button(blue_btn, "Blue", BLUE, current_color == BLUE)

    draw_button(brush_btn, "Brush", GRAY, tool == "brush")
    draw_button(eraser_btn, "Eraser", GRAY, tool == "eraser")
    draw_button(line_btn, "Line", GRAY, tool == "line")
    draw_button(rect_btn, "Rect", GRAY, tool == "rect")
    draw_button(circle_btn, "Circle", GRAY, tool == "circle")
    draw_button(square_btn, "Square", GRAY, tool == "square")
    draw_button(rtriangle_btn, "R-Tri", GRAY, tool == "rtriangle")
    draw_button(etriangle_btn, "E-Tri", GRAY, tool == "etriangle")
    draw_button(rhombus_btn, "Rhombus", GRAY, tool == "rhombus")
    draw_button(clear_btn, "Clear", GRAY, False)

while True:
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

            elif brush_btn.collidepoint(pos):

                tool = "brush"

            elif eraser_btn.collidepoint(pos):

                tool = "eraser"

            elif line_btn.collidepoint(pos):

                tool = "line"

            elif rect_btn.collidepoint(pos):

                tool = "rect"

            elif circle_btn.collidepoint(pos):

                tool = "circle"

            elif square_btn.collidepoint(pos):

                tool = "square"

            elif rtriangle_btn.collidepoint(pos):

                tool = "rtriangle"

            elif etriangle_btn.collidepoint(pos):

                tool = "etriangle"

            elif rhombus_btn.collidepoint(pos):

                tool = "rhombus"

            elif clear_btn.collidepoint(pos):

                canvas.fill(WHITE)

            elif pos[1] > 80:

                drawing = True

                start_pos = pos

                current_pos = pos

                last_pos = pos

                current_rect = None

        elif event.type == pygame.MOUSEMOTION and drawing:
            current_pos = event.pos

            if tool == "brush":
                pygame.draw.line(canvas, current_color, last_pos, current_pos, 5)
                last_pos = current_pos

            elif tool == "eraser":
                pygame.draw.line(canvas, WHITE, last_pos, current_pos, 12)
                last_pos = current_pos

            elif tool == "rect":
                width = current_pos[0] - start_pos[0]
                height = current_pos[1] - start_pos[1]
                current_rect = pygame.Rect(start_pos, (width, height))
                current_rect.normalize()


        elif event.type == pygame.MOUSEBUTTONUP:

            if drawing:

                end_pos = event.pos

                if tool == "line":

                    pygame.draw.line(canvas, current_color, start_pos, end_pos, 3)


                elif tool == "rect":

                    width = end_pos[0] - start_pos[0]

                    height = end_pos[1] - start_pos[1]

                    final_rect = pygame.Rect(start_pos, (width, height))

                    final_rect.normalize()

                    pygame.draw.rect(canvas, current_color, final_rect, 2)


                elif tool == "square":

                    side = max(abs(end_pos[0] - start_pos[0]), abs(end_pos[1] - start_pos[1]))

                    x = start_pos[0] if end_pos[0] >= start_pos[0] else start_pos[0] - side

                    y = start_pos[1] if end_pos[1] >= start_pos[1] else start_pos[1] - side

                    square_rect = pygame.Rect(x, y, side, side)

                    pygame.draw.rect(canvas, current_color, square_rect, 2)


                elif tool == "circle":

                    radius = int(math.sqrt(

                        (end_pos[0] - start_pos[0]) ** 2 +

                        (end_pos[1] - start_pos[1]) ** 2

                    ))

                    pygame.draw.circle(canvas, current_color, start_pos, radius, 2)


                elif tool == "rtriangle":

                    points = [

                        start_pos,

                        (start_pos[0], end_pos[1]),

                        end_pos

                    ]

                    pygame.draw.polygon(canvas, current_color, points, 2)


                elif tool == "etriangle":

                    dx = end_pos[0] - start_pos[0]

                    side = abs(dx)

                    height = int((math.sqrt(3) / 2) * side)

                    if dx >= 0:

                        p1 = (start_pos[0], start_pos[1] + height)

                        p2 = (start_pos[0] + side, start_pos[1] + height)

                        p3 = (start_pos[0] + side // 2, start_pos[1])

                    else:

                        p1 = (start_pos[0], start_pos[1] + height)

                        p2 = (start_pos[0] - side, start_pos[1] + height)

                        p3 = (start_pos[0] - side // 2, start_pos[1])

                    pygame.draw.polygon(canvas, current_color, [p1, p2, p3], 2)


                elif tool == "rhombus":

                    cx = (start_pos[0] + end_pos[0]) // 2

                    cy = (start_pos[1] + end_pos[1]) // 2

                    half_w = abs(end_pos[0] - start_pos[0]) // 2

                    half_h = abs(end_pos[1] - start_pos[1]) // 2

                    points = [

                        (cx, cy - half_h),

                        (cx + half_w, cy),

                        (cx, cy + half_h),

                        (cx - half_w, cy)

                    ]

                    pygame.draw.polygon(canvas, current_color, points, 2)

                drawing = False

                last_pos = None

                current_rect = None

    screen.fill(WHITE)
    screen.blit(canvas, (0, 0))
    draw_ui()

    if drawing:
        if tool == "line":
            pygame.draw.line(screen, current_color, start_pos, current_pos, 3)

        elif tool == "rect" and current_rect:
            pygame.draw.rect(screen, current_color, current_rect, 2)

        elif tool == "square":
            side = max(abs(current_pos[0] - start_pos[0]), abs(current_pos[1] - start_pos[1]))
            x = start_pos[0] if current_pos[0] >= start_pos[0] else start_pos[0] - side
            y = start_pos[1] if current_pos[1] >= start_pos[1] else start_pos[1] - side
            preview_rect = pygame.Rect(x, y, side, side)
            pygame.draw.rect(screen, current_color, preview_rect, 2)

        elif tool == "circle":
            radius = int(math.sqrt(
                (current_pos[0] - start_pos[0]) ** 2 +
                (current_pos[1] - start_pos[1]) ** 2
            ))
            pygame.draw.circle(screen, current_color, start_pos, radius, 2)

        elif tool == "rtriangle":
            points = [
                start_pos,
                (start_pos[0], current_pos[1]),
                current_pos
            ]
            pygame.draw.polygon(screen, current_color, points, 2)

        elif tool == "etriangle":
            dx = current_pos[0] - start_pos[0]
            side = abs(dx)
            height = int((math.sqrt(3) / 2) * side)

            if dx >= 0:
                p1 = (start_pos[0], start_pos[1] + height)
                p2 = (start_pos[0] + side, start_pos[1] + height)
                p3 = (start_pos[0] + side // 2, start_pos[1])
            else:
                p1 = (start_pos[0], start_pos[1] + height)
                p2 = (start_pos[0] - side, start_pos[1] + height)
                p3 = (start_pos[0] - side // 2, start_pos[1])

            pygame.draw.polygon(screen, current_color, [p1, p2, p3], 2)

        elif tool == "rhombus":
            cx = (start_pos[0] + current_pos[0]) // 2
            cy = (start_pos[1] + current_pos[1]) // 2
            half_w = abs(current_pos[0] - start_pos[0]) // 2
            half_h = abs(current_pos[1] - start_pos[1]) // 2

            points = [
                (cx, cy - half_h),
                (cx + half_w, cy),
                (cx, cy + half_h),
                (cx - half_w, cy)
            ]
            pygame.draw.polygon(screen, current_color, points, 2)
    pygame.display.flip()
    clock.tick(60)