import pygame
from Akuga import button


class sub_menu(pygame.sprite.Group):
    """
    A sub_menu is just an extended sprite group, transparent specifies
    if the next sub_menu should also be rendered
    """
    def __init__(self, sprites=[], transparent=False):
        super().__init__(sprites)
        self.transparent = transparent

    def draw(self, screen):
        """
        This extension is needed as many gui elements will inherite
        von pygame.Sprite but contain more than one image to render
        """
        for sprite in self.sprites():
            sprite.draw(screen)


class menu_list(list):
    """
    A menu_list is an extendet list including an update and a draw
    function. Every element menu_list hast to provide an update and a
    draw function.
    """
    def __init__(self):
        pass

    def update(self, args=None):
        # As a menu_list will only contain menus (sprite groups)
        # or game scenes a update function will be provided
        self[-1].update(args)

    def draw(self, screen):
        # A stack is a fifo structure so it will be drawn from the end
        # in decreasing order till the first non transparent menu.
        # This sublist has to be drawn in increasing order to assure
        # that the lastmost menu wont be overdrawn
        index = len(self) - 1
        while self[index].transparent and index > 0:
            index = index - 1
        # As a menu_list will only contain menus (sprite groups)
        # a draw function is provided
        for m in self[index:]:
            m.draw(screen)


def cb(args):
    print(args[0].position[0])
    print(args[0].position[1])
    print(args[1])


if __name__ == "__main__":
    # pygame init
    pygame.init()
    screen = pygame.display.set_mode((512, 512))
    running = True

    sub_menu1 = sub_menu([], True)
    sub_menu2 = sub_menu([], True)
    menu = menu_list()
    for i in range(0, 2):
        sub_menu1.add(button.button("test.png", (60 * i, 10), cb))
        sub_menu2.add(button.button("test.png", (60 * i, 60), cb))

    menu.append(sub_menu1)
    menu.append(sub_menu2)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        menu.update()

        screen.fill((0, 0, 0))
        menu.draw(screen)
        pygame.display.flip()
