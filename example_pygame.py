import pygame

from common import initialize_gl, display, paint_gl

if __name__ == '__main__':
    pygame.init()
    pygame.display.set_mode(display, pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
    initialize_gl()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        paint_gl()
        pygame.display.flip()
        pygame.time.wait(1000)
