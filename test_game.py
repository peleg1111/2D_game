from const import *
from const_class import *

def main():
    manager = GameManager()
    t = Tank(manager.screen, 300, 400, 25, 25, (0, 255, 0), 0.1, 1000)
    manager.Add_player(t)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

        manager.main_loop()


if __name__ == '__main__':
    main()
