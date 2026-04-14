import pygame
import datetime

pygame.init()


screen = pygame.display.set_mode((800, 800))
pygame.display.set_caption("Mickey Clock")
clock = pygame.time.Clock()

mickey_hand_original = None
background = None
minute_hand_img = None
second_hand_img = None


def create_hand(image, length):
    w, h = image.get_size()
    scale = length / h
    new_size = (int(w * scale), int(h * scale))
    return pygame.transform.scale(image, new_size)


def load_images(screen_width, screen_height):
    global mickey_hand_original, background
    global minute_hand_img, second_hand_img

    mickey_hand_original = pygame.image.load("hand.png").convert_alpha()
    background = pygame.image.load("mouce.png").convert()
    background = pygame.transform.scale(background, (screen_width, screen_height))

    minute_hand_img = create_hand(mickey_hand_original, 150)
    second_hand_img = create_hand(mickey_hand_original, 200)


def blit_rotate(surface, image, pos, angle):
    rotated_image = pygame.transform.rotate(image, angle)
    rect = rotated_image.get_rect(center=pos)

    offset = pygame.math.Vector2(0, -image.get_height() // 2)
    offset = offset.rotate(-angle)

    rect.center = (pos[0] + offset.x, pos[1] + offset.y)
    surface.blit(rotated_image, rect)


def draw_clock(screen, cx, cy):
    global mickey_hand_original

    if mickey_hand_original is None:
        load_images(screen.get_width(), screen.get_height())

    screen.blit(background, (0, 0))

    now = datetime.datetime.now()
    minutes = now.minute
    seconds = now.second

    minute_angle = -(minutes * 6)
    second_angle = -(seconds * 6)

    blit_rotate(screen, minute_hand_img, (cx, cy), minute_angle)
    blit_rotate(screen, second_hand_img, (cx, cy), second_angle)


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

    draw_clock(screen, 800 // 2, 800 // 2)

    pygame.display.flip()
    clock.tick(60)