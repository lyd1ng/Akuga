from Akuga.MatchServer.Position import Position


class ArenaTile:
    """
    This represents one tile of an arena.
    It contains six values for six different
    colors and reference on the jumon or equipment
    which is placed on the tile.
    It also has a script which may add special effects on the tile.
    A tile is blocked if the unit occupying the tile is blocking
    """
    def __init__(self, boni, flip_effect_script):
        self.boni = boni
        self.flip_scripy = flip_effect_script
        self.occupied_by = None

    def occupied_by(self):
        """
        Returns the unit aka jumon, equipment ocuppying this tile
        """
        return self.occupied_by

    def is_blocked(self):
        """
        Returns whether the unit occupying this tile is blocking or not
        """
        if self.occupied_by is not None:
            return self.occupied_by.blocking
        return False

    def get_bonus_for_jumon(self, jumon):
        """
        Just returns the bonus value for the color of the jumon
        or 0 if ther jumon has an unknown color
        """
        try:
            return self.boni[jumon.color]
        except(KeyError):
            return 0

    def place_unit(self, unit):
        """
        Places a unit on this tile
        """
        self.occupied_by = unit

    def remove_unit(self):
        """
        Removes the unit from the tile if there is one
        """
        self.occupied_by = None


class Arena:
    """
    This represents the arena, which is made of BOARD_WIDTH * BOARD_HEIGHT
    many ArenaTiles
    """
    def __init__(self, tiles, board_width, board_height):
        """
        tiles is a 2d list of ArenaTiles
        """
        self.tiles = tiles
        self.board_width = board_width
        self.board_height = board_height

    def get_tile_at(self, position):
        """
        Returns the arena tile at the given position
        """
        return self.tiles[position.x][position.y]

    def is_blocked_at(self, position):
        """
        Return whether the tile at position is blocked or not
        """
        return self.tiles[position.x][position.y].is_blocked()

    def get_unit_at(self, position):
        """
        Get the Unit aka Jumon, Equipment or Trap at position
        """
        return self.tiles[position.x][position.y].occupied_by()

    def place_unit_at(self, unit, position):
        """
        Places unit at position
        """
        self.tiles[position.x][position.y].place_unit(unit)

    def print_out(self):
        for y in range(0, self.board_height):
            for x in range(0, self.board_width):
                print("|", end="")
                if self.get_unit_at(Position(x, y)) is not None:
                    print(self.get_unit_at(Position(x, y)).name, end=" ")
                print("\t", end="")
            print("")
