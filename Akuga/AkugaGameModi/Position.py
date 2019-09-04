class Position():
    """
    Just a small abstraction for an integer 2d vector
    This is superior to tupels as the components are alterable
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @classmethod
    def copy(cls, position):
        """
        A copy constructor
        """
        return Position(position.x, position.y)

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

    def __sub__(self, other):
        """
        Just add both positions componentwise
        """
        return Position(self.x - other.x, self.y - other.y)

    def __str__(self):
        """
        Turn to string
        """
        return str(self.x) + "," + str(self.y)


if __name__ == "__main__":
    pos1 = Position(4, 4)
    pos2 = Position.copy(pos1)
    pos2.x += 1
    print(str(pos1))
    print(str(pos2))
