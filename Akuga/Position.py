class Position():
    """
    Just a small abstraction for an integer 2d vector
    This is superior to tupels as the components are alterable
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        """
        Just compare x and y coords
        """
        return self.x == other.x and self.y == other.y

    def __add__(self, other):
        """
        Just add both positions componentwise
        """
        return Position(self.x + other.x, self.y + other.y)


if __name__ == "__main__":
    result = Position(1, 1) + Position(1, 1)
    print(result.x)
    print(result.y)
