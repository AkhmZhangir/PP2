import pygame
import datetime


pygame.init()
screen=pygame.display.set_mode((600,600))
a=pygame.image.load("mouce.png")
bg_image = pygame.transform.scale(a, (600, 600))
second=pygame.image.load("second.png")
minute=pygame.image.load("minute.png")
def background():
    screen.blit(bg_image,(0,0))
    pygame.display.flip()
while True:
    background()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        currenttime=datetime.datetime.now()
        print(currenttime.minute,currenttime.second)