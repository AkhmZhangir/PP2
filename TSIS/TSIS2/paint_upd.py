import pygame
import math
from datetime import datetime

pygame.init()

TOOLBAR_HEIGHT = 100
WIDTH, HEIGHT = 1500, 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mini Paint")

font = pygame.font.SysFont("Arial", 17)
clock = pygame.time.Clock()

WHITE   = (255, 255, 255)
BLACK   = (0,   0,   0)
RED     = (255, 0,   0)
GREEN   = (0,   200, 0)
BLUE    = (0,   0,   255)
GRAY    = (200, 200, 200)
DARK_GRAY = (140, 140, 140)

canvas = pygame.Surface((WIDTH, HEIGHT))
canvas.fill(WHITE)

drawing     = False
start_pos   = (0, 0)
current_pos = (0, 0)
last_pos    = None
current_rect = None

current_color = BLUE
tool          = "brush"
brush_size    = 5          # default: medium

# Text-tool state
text_active = False
text_pos    = (0, 0)
text_str    = ""
text_font   = pygame.font.SysFont("Arial", 24)

# ── Row 1 (y=8, h=35): colours + sizes ─────────────────────────────────────
red_btn    = pygame.Rect(20,  8, 55, 35)
green_btn  = pygame.Rect(85,  8, 55, 35)
blue_btn   = pygame.Rect(150, 8, 55, 35)

size_s_btn = pygame.Rect(230, 8, 45, 35)
size_m_btn = pygame.Rect(285, 8, 45, 35)
size_l_btn = pygame.Rect(340, 8, 45, 35)

# ── Row 2 (y=55, h=35): tools ───────────────────────────────────────────────
pencil_btn    = pygame.Rect(20,   55, 70, 35)
brush_btn     = pygame.Rect(100,  55, 70, 35)
eraser_btn    = pygame.Rect(180,  55, 70, 35)
fill_btn      = pygame.Rect(260,  55, 70, 35)
text_btn      = pygame.Rect(340,  55, 70, 35)
line_btn      = pygame.Rect(420,  55, 70, 35)
rect_btn      = pygame.Rect(500,  55, 70, 35)
circle_btn    = pygame.Rect(580,  55, 70, 35)
square_btn    = pygame.Rect(660,  55, 70, 35)
rtriangle_btn = pygame.Rect(740,  55, 85, 35)
etriangle_btn = pygame.Rect(835,  55, 85, 35)
rhombus_btn   = pygame.Rect(930,  55, 85, 35)
clear_btn     = pygame.Rect(1025, 55, 75, 35)


# ── Helpers ──────────────────────────────────────────────────────────────────

def draw_button(rect, text, bg_color, active=False):
    color = DARK_GRAY if active else bg_color
    pygame.draw.rect(screen, color, rect, border_radius=4)
    pygame.draw.rect(screen, BLACK, rect, 2, border_radius=4)
    lbl = font.render(text, True, BLACK)
    screen.blit(lbl, lbl.get_rect(center=rect.center))


def draw_ui():
    pygame.draw.rect(screen, (220, 220, 220), (0, 0, WIDTH, TOOLBAR_HEIGHT))
    pygame.draw.line(screen, DARK_GRAY, (0, TOOLBAR_HEIGHT), (WIDTH, TOOLBAR_HEIGHT), 2)

    # Row 1 — colours
    draw_button(red_btn,   "Red",   RED,   current_color == RED)
    draw_button(green_btn, "Green", GREEN, current_color == GREEN)
    draw_button(blue_btn,  "Blue",  BLUE,  current_color == BLUE)

    # Row 1 — sizes
    draw_button(size_s_btn, "S [1]", GRAY, brush_size == 2)
    draw_button(size_m_btn, "M [2]", GRAY, brush_size == 5)
    draw_button(size_l_btn, "L [3]", GRAY, brush_size == 10)

    # Brush-size preview dot
    dot_r = max(brush_size // 2, 1)
    pygame.draw.circle(screen, current_color, (405, 26), dot_r)

    # Hint text
    hint = font.render("Ctrl+S = Save as PNG", True, (80, 80, 80))
    screen.blit(hint, (430, 18))

    # Row 2 — tools
    draw_button(pencil_btn,    "Pencil",  GRAY, tool == "pencil")
    draw_button(brush_btn,     "Brush",   GRAY, tool == "brush")
    draw_button(eraser_btn,    "Eraser",  GRAY, tool == "eraser")
    draw_button(fill_btn,      "Fill",    GRAY, tool == "fill")
    draw_button(text_btn,      "Text",    GRAY, tool == "text")
    draw_button(line_btn,      "Line",    GRAY, tool == "line")
    draw_button(rect_btn,      "Rect",    GRAY, tool == "rect")
    draw_button(circle_btn,    "Circle",  GRAY, tool == "circle")
    draw_button(square_btn,    "Square",  GRAY, tool == "square")
    draw_button(rtriangle_btn, "R-Tri",   GRAY, tool == "rtriangle")
    draw_button(etriangle_btn, "E-Tri",   GRAY, tool == "etriangle")
    draw_button(rhombus_btn,   "Rhombus", GRAY, tool == "rhombus")
    draw_button(clear_btn,     "Clear",   GRAY, False)


def flood_fill(surface, x, y, fill_color):
    """BFS flood-fill using get_at / set_at (no extra libraries)."""
    w, h = surface.get_size()
    if not (0 <= x < w and 0 <= y < h):
        return
    target = surface.get_at((x, y))[:3]
    new    = tuple(fill_color[:3])
    if target == new:
        return

    surface.lock()
    stack = [(x, y)]
    seen  = {(x, y)}
    while stack:
        cx, cy = stack.pop()
        if surface.get_at((cx, cy))[:3] != target:
            continue
        surface.set_at((cx, cy), new)
        for nx, ny in ((cx-1, cy), (cx+1, cy), (cx, cy-1), (cx, cy+1)):
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen:
                seen.add((nx, ny))
                stack.append((nx, ny))
    surface.unlock()


# ── Main loop ────────────────────────────────────────────────────────────────

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

        # ── Keyboard ──────────────────────────────────────────────────────
        elif event.type == pygame.KEYDOWN:

            if text_active:
                # Text-tool input handling
                if event.key == pygame.K_RETURN:
                    if text_str:
                        rendered = text_font.render(text_str, True, current_color)
                        canvas.blit(rendered, text_pos)
                    text_active = False
                    text_str    = ""
                elif event.key == pygame.K_ESCAPE:
                    text_active = False
                    text_str    = ""
                elif event.key == pygame.K_BACKSPACE:
                    text_str = text_str[:-1]
                else:
                    if event.unicode and event.unicode.isprintable():
                        text_str += event.unicode

            else:
                # Brush-size shortcuts
                if event.key == pygame.K_1:
                    brush_size = 2
                elif event.key == pygame.K_2:
                    brush_size = 5
                elif event.key == pygame.K_3:
                    brush_size = 10
                # Ctrl+S  →  save timestamped PNG
                elif event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"canvas_{ts}.png"
                    pygame.image.save(canvas, filename)
                    pygame.display.set_caption(f"Mini Paint  —  saved {filename}")

        # ── Mouse button down ─────────────────────────────────────────────
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos

            if   red_btn.collidepoint(pos):    current_color = RED
            elif green_btn.collidepoint(pos):  current_color = GREEN
            elif blue_btn.collidepoint(pos):   current_color = BLUE

            elif size_s_btn.collidepoint(pos): brush_size = 2
            elif size_m_btn.collidepoint(pos): brush_size = 5
            elif size_l_btn.collidepoint(pos): brush_size = 10

            elif pencil_btn.collidepoint(pos):    tool = "pencil"
            elif brush_btn.collidepoint(pos):     tool = "brush"
            elif eraser_btn.collidepoint(pos):    tool = "eraser"
            elif fill_btn.collidepoint(pos):      tool = "fill"
            elif text_btn.collidepoint(pos):      tool = "text"
            elif line_btn.collidepoint(pos):      tool = "line"
            elif rect_btn.collidepoint(pos):      tool = "rect"
            elif circle_btn.collidepoint(pos):    tool = "circle"
            elif square_btn.collidepoint(pos):    tool = "square"
            elif rtriangle_btn.collidepoint(pos): tool = "rtriangle"
            elif etriangle_btn.collidepoint(pos): tool = "etriangle"
            elif rhombus_btn.collidepoint(pos):   tool = "rhombus"
            elif clear_btn.collidepoint(pos):
                canvas.fill(WHITE)
                text_active = False
                text_str    = ""

            elif pos[1] > TOOLBAR_HEIGHT:
                if tool == "fill":
                    flood_fill(canvas, pos[0], pos[1], current_color)
                elif tool == "text":
                    # Confirm any previous unfinished text first
                    if text_active and text_str:
                        canvas.blit(text_font.render(text_str, True, current_color), text_pos)
                    text_active = True
                    text_pos    = pos
                    text_str    = ""
                else:
                    drawing      = True
                    start_pos    = pos
                    current_pos  = pos
                    last_pos     = pos
                    current_rect = None

        # ── Mouse motion ──────────────────────────────────────────────────
        elif event.type == pygame.MOUSEMOTION and drawing:
            current_pos = event.pos

            if tool in ("pencil", "brush"):
                pygame.draw.line(canvas, current_color, last_pos, current_pos, brush_size)
                last_pos = current_pos
            elif tool == "eraser":
                erase_w = max(brush_size * 2, 10)
                pygame.draw.line(canvas, WHITE, last_pos, current_pos, erase_w)
                last_pos = current_pos
            elif tool == "rect":
                w = current_pos[0] - start_pos[0]
                h = current_pos[1] - start_pos[1]
                current_rect = pygame.Rect(start_pos, (w, h))
                current_rect.normalize()

        # ── Mouse button up ───────────────────────────────────────────────
        elif event.type == pygame.MOUSEBUTTONUP:
            if drawing:
                ep = event.pos   # end point

                if tool == "line":
                    pygame.draw.line(canvas, current_color, start_pos, ep, brush_size)

                elif tool == "rect":
                    r = pygame.Rect(start_pos, (ep[0]-start_pos[0], ep[1]-start_pos[1]))
                    r.normalize()
                    pygame.draw.rect(canvas, current_color, r, brush_size)

                elif tool == "square":
                    side = max(abs(ep[0]-start_pos[0]), abs(ep[1]-start_pos[1]))
                    x = start_pos[0] if ep[0] >= start_pos[0] else start_pos[0] - side
                    y = start_pos[1] if ep[1] >= start_pos[1] else start_pos[1] - side
                    pygame.draw.rect(canvas, current_color, pygame.Rect(x, y, side, side), brush_size)

                elif tool == "circle":
                    radius = int(math.hypot(ep[0]-start_pos[0], ep[1]-start_pos[1]))
                    pygame.draw.circle(canvas, current_color, start_pos, radius, brush_size)

                elif tool == "rtriangle":
                    pts = [start_pos, (start_pos[0], ep[1]), ep]
                    pygame.draw.polygon(canvas, current_color, pts, brush_size)

                elif tool == "etriangle":
                    dx   = ep[0] - start_pos[0]
                    side = abs(dx)
                    h    = int((math.sqrt(3)/2) * side)
                    if dx >= 0:
                        p1=(start_pos[0],       start_pos[1]+h)
                        p2=(start_pos[0]+side,   start_pos[1]+h)
                        p3=(start_pos[0]+side//2, start_pos[1])
                    else:
                        p1=(start_pos[0],       start_pos[1]+h)
                        p2=(start_pos[0]-side,   start_pos[1]+h)
                        p3=(start_pos[0]-side//2, start_pos[1])
                    pygame.draw.polygon(canvas, current_color, [p1,p2,p3], brush_size)

                elif tool == "rhombus":
                    cx = (start_pos[0]+ep[0])//2
                    cy = (start_pos[1]+ep[1])//2
                    hw = abs(ep[0]-start_pos[0])//2
                    hh = abs(ep[1]-start_pos[1])//2
                    pts = [(cx,cy-hh),(cx+hw,cy),(cx,cy+hh),(cx-hw,cy)]
                    pygame.draw.polygon(canvas, current_color, pts, brush_size)

                drawing      = False
                last_pos     = None
                current_rect = None

    # ── Render ───────────────────────────────────────────────────────────────
    screen.fill(WHITE)
    screen.blit(canvas, (0, 0))
    draw_ui()

    # Live shape preview while dragging
    if drawing:
        ep = current_pos
        if tool == "line":
            pygame.draw.line(screen, current_color, start_pos, ep, brush_size)
        elif tool == "rect" and current_rect:
            pygame.draw.rect(screen, current_color, current_rect, brush_size)
        elif tool == "square":
            side = max(abs(ep[0]-start_pos[0]), abs(ep[1]-start_pos[1]))
            x = start_pos[0] if ep[0] >= start_pos[0] else start_pos[0] - side
            y = start_pos[1] if ep[1] >= start_pos[1] else start_pos[1] - side
            pygame.draw.rect(screen, current_color, pygame.Rect(x,y,side,side), brush_size)
        elif tool == "circle":
            radius = int(math.hypot(ep[0]-start_pos[0], ep[1]-start_pos[1]))
            pygame.draw.circle(screen, current_color, start_pos, radius, brush_size)
        elif tool == "rtriangle":
            pts = [start_pos, (start_pos[0], ep[1]), ep]
            pygame.draw.polygon(screen, current_color, pts, brush_size)
        elif tool == "etriangle":
            dx   = ep[0]-start_pos[0]
            side = abs(dx)
            h    = int((math.sqrt(3)/2)*side)
            if dx >= 0:
                p1=(start_pos[0],       start_pos[1]+h)
                p2=(start_pos[0]+side,   start_pos[1]+h)
                p3=(start_pos[0]+side//2, start_pos[1])
            else:
                p1=(start_pos[0],       start_pos[1]+h)
                p2=(start_pos[0]-side,   start_pos[1]+h)
                p3=(start_pos[0]-side//2, start_pos[1])
            pygame.draw.polygon(screen, current_color, [p1,p2,p3], brush_size)
        elif tool == "rhombus":
            cx = (start_pos[0]+ep[0])//2
            cy = (start_pos[1]+ep[1])//2x
            hw = abs(ep[0]-start_pos[0])//2
            hh = abs(ep[1]-start_pos[1])//2
            pts = [(cx,cy-hh),(cx+hw,cy),(cx,cy+hh),(cx-hw,cy)]
            pygame.draw.polygon(screen, current_color, pts, brush_size)

    # Text-tool live cursor / typing preview
    if text_active:
        preview = text_font.render(text_str + "|", True, current_color)
        screen.blit(preview, text_pos)

    pygame.display.flip()
    clock.tick(60)
