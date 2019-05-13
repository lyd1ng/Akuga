class Position():
    """
    Just a small abstraction for an integer 2d vector
    This is superior to tupels as the components are alterable
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
