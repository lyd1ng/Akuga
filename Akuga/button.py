import pygame


class button(pygame.sprite.Sprite):
    """
    The button class is a not animated gui element and invokes
    a callback function when clicked with the left mouse
    button
    """
    def __init__(self, img_path, position, callback, on_release=True):
        super().__init__()
        self.image = pygame.image.load(img_path)
        self.image_path = img_path
        self.rect = self.image.get_rect()
        self.rect.topleft = position
        self.callback = callback
        self.toggle = False
        self.on_release = on_release

    def update(self, args):
        """
        The update function accepts the args tupel as parameter
        and uses the mouse_pos and mouse_keys to determine if this button
        is clicked.
        The callback function is invoked with a reference to this instance
        and every element from args except the first five parameters.
        This first five parameters are user inputs and game events
        and usually not needed by buttons
        """
        mouse_keys = args[0]
        mouse_pos = args[1]
        # pressed_keys = args[2]
        # timing_factor = args[3]
        # events = args[4]
        if mouse_keys[0] and not self.toggle:
            if self.rect.collidepoint(mouse_pos):
                if not self.on_release:
                    self.callback((self, args[5:]))
                self.toggle = True

        if not mouse_keys[0] and self.toggle:
            if self.on_release:
                self.callback((self, args[5:]))
            self.toggle = False

    def draw(self, screen):
        """
        Just draw the button
        """
        screen.blit(self.image, self.rect)
