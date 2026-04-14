import pygame
from pathlib import Path

pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 800, 420
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Music Player")
clock = pygame.time.Clock()

title_font = pygame.font.SysFont(None, 42)
text_font = pygame.font.SysFont(None, 30)
small_font = pygame.font.SysFont(None, 24)

MUSIC_END = pygame.USEREVENT + 1
pygame.mixer.music.set_endevent(MUSIC_END)

music_folder = Path("music")
if not music_folder.exists():
    music_folder.mkdir(exist_ok=True)

playlist = []
for file in sorted(music_folder.iterdir()):
    if file.suffix.lower() in [".mp3", ".wav", ".ogg"]:
        playlist.append(file)

current_index = 0
status = "Stopped"
track_length = 0
paused = False


def load_track():
    global track_length

    if len(playlist) == 0:
        track_length = 0
        return

    pygame.mixer.music.load(str(playlist[current_index]))
    track_length = pygame.mixer.Sound(str(playlist[current_index])).get_length()


def play_track():
    global status, paused

    if len(playlist) == 0:
        status = "No files"
        return

    if paused:
        pygame.mixer.music.unpause()
        paused = False
        status = "Playing"
    else:
        load_track()
        pygame.mixer.music.play()
        status = "Playing"


def stop_track():
    global status, paused

    pygame.mixer.music.stop()
    paused = False
    status = "Stopped"


def next_track():
    global current_index, paused

    if len(playlist) == 0:
        return

    current_index = (current_index + 1) % len(playlist)
    paused = False
    play_track()


def previous_track():
    global current_index, paused

    if len(playlist) == 0:
        return

    current_index = (current_index - 1) % len(playlist)
    paused = False
    play_track()


def pause_or_play():
    global status, paused

    if len(playlist) == 0:
        status = "No files"
        return

    if pygame.mixer.music.get_busy() and not paused:
        pygame.mixer.music.pause()
        paused = True
        status = "Paused"
    else:
        play_track()


def format_time(seconds):
    seconds = max(0, int(seconds))
    minutes = seconds // 60
    sec = seconds % 60
    return f"{minutes:02d}:{sec:02d}"


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                pause_or_play()
            elif event.key == pygame.K_s:
                stop_track()
            elif event.key == pygame.K_n:
                next_track()
            elif event.key == pygame.K_b:
                previous_track()
            elif event.key == pygame.K_q:
                running = False

        elif event.type == MUSIC_END:
            next_track()

    screen.fill((20, 20, 25))

    title = title_font.render("Music Player", True, (255, 255, 255))
    screen.blit(title, (30, 25))

    if len(playlist) > 0:
        current_track = playlist[current_index].name
    else:
        current_track = "No track"

    track_text = text_font.render(f"Track: {current_track}", True, (220, 220, 220))
    status_text = text_font.render(f"Status: {status}", True, (180, 220, 255))
    playlist_text = text_font.render(f"Playlist: {len(playlist)}", True, (220, 220, 220))

    screen.blit(track_text, (30, 100))
    screen.blit(status_text, (30, 140))
    screen.blit(playlist_text, (30, 180))

    elapsed_ms = pygame.mixer.music.get_pos()
    if elapsed_ms < 0:
        elapsed_ms = 0
    elapsed = elapsed_ms / 1000

    pygame.draw.line(screen, (100, 100, 100), (30, 255), (770, 255), 6)

    if track_length > 0:
        progress_x = 30 + int((elapsed / track_length) * 740)
        if progress_x > 770:
            progress_x = 770
    else:
        progress_x = 30

    pygame.draw.circle(screen, (0, 220, 140), (progress_x, 255), 10)

    time_text = small_font.render(
        f"{format_time(elapsed)} / {format_time(track_length)}",
        True,
        (255, 255, 255)
    )
    screen.blit(time_text, (30, 280))

    controls1 = small_font.render("P - Play/Pause    S - Stop    N - Next", True, (200, 200, 200))
    controls2 = small_font.render("B - Back          Q - Quit", True, (200, 200, 200))

    screen.blit(controls1, (30, 330))
    screen.blit(controls2, (30, 360))

    if len(playlist) == 0:
        info = small_font.render("Put MP3/WAV/OGG files into the music folder", True, (255, 190, 120))
        screen.blit(info, (30, 215))

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
exit()