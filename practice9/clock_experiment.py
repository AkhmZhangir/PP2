import pygame
import datetime


pygame.init()
screen=pygame.display.set_mode((600,600))
a=pygame.image.load("mick.png")
bg_image = pygame.transform.scale(a, (600, 600))
second=pygame.image.load("hand.png").convert_alpha()
minute=pygame.image.load("hand.png").convert_alpha()
seconds=pygame.transform.scale(second, (100, 50))
minutes=pygame.transform.scale(minute, (100, 50))
pygame.display.set_caption("Clock")
clock = pygame.time.Clock()
back=pygame.image.load("line.png").convert_alpha()
image = pygame.transform.scale(back, (200, 40))
def background():
    screen.fill((255,255,255))
    screen.blit(bg_image,(0,0))
    seconds_rect=pygame.Rect(40,400,200,40)
    mins_rect = pygame.Rect(300, 400, 200, 40)
    screen.blit(image, (40, 400))
    screen.blit(image, (300, 400))
    pygame.draw.rect(screen, (0,0,0),seconds_rect,3)
    pygame.draw.rect(screen, (0, 0, 0), mins_rect, 3)
    pygame.display.flip()
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

    currenttime = datetime.datetime.now()
    sec = currenttime.second
    min = currenttime.minute

    BASE_X = -10
    WIDTH  = 200
    y = 400

    x_sec = BASE_X + WIDTH * sec / 60.0
    x_min = BASE_X + WIDTH * (min + sec / 60.0) / 60.0 +300

    background()  # рисует фон

    screen.blit(seconds, (x_sec, y+30))
    screen.blit(minutes, (x_min, y + 30))

    pygame.display.flip()
    clock.tick(60)