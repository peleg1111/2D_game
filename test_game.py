from const import *
from const_class import *

def main():
    manager = GameManager()
    t = Tank(manager.screen, 300, 400, TANK_SIZE, TANK_SIZE, TANK_HIT_BOX__COLOR,
                                            TANK_SPEED, TANK_ATTACK_COOLDOWN, TANK_HP)
    manager.Add_player(t)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

        manager.main_loop()


if __name__ == '__main__':
    main()
