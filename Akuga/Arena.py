class ArenaTile:
    """
    This represents one tile of an arena.
    It contains six values for six different
    colors and reference on the jumon or equipment
    or trap which is placed on the tile.
    It also has a script which may add special effects on the tile.
    A tile is blocked if the unit occupying the tile is blocking
    """
    def __init__(self, boni, flip_effect_script):
        self.boni = boni
        self.flip_scripy = flip_effect_script
        self.occupied_by = None

    def OccupiedBy(self):
        """
        Returns the unit aka jumon, equipment or trap ocuppying this tile
        """
        return self.occupied_by

    def IsBlocked(self):
        """
        Returns whether the unit occupying this tile is blocking or not
        """
        if self.occupied_by is not None:
            return self.occupied_by.blocking
        return False

    def GetBonusForJumon(self, jumon):
        """
        Just returns the bonus value for the color of the jumon
        or 0 if ther jumon has an unknown color
        """
        try:
            return self.boni[jumon.color]
        except(KeyError):
            return 0

    def PlaceUnit(self, unit):
        """
        Places a unit on this tile
        """
        self.occupied_by = unit

    def RemoveUnit(self):
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

    def GetTileAt(self, position):
        """
        Returns the arena tile at the given position
        """
        return self.tiles[position[0]][position[1]]

    def IsBlockedAt(self, position):
        """
        Return whether the tile at position is blocked or not
        """
        return self.tiles[position[0]][position[1]].IsBlocked()

    def GetUnitAt(self, position):
        """
        Get the Unit aka Jumon, Equipment or Trap at position
        """
        return self.tiles[position[0]][position[1]].OccupiedBy()

    def PlaceUnitAt(self, unit, position):
        """
        Places unit at position
        """
        self.tiles[position[0]][position[1]].PlaceUnit(unit)

    def PrintOut(self):
        for y in range(0, self.board_height):
            for x in range(0, self.board_width):
                print("|", end="")
                if self.GetUnitAt((x, y)) is not None:
                    print(self.GetUnitAt((x, y)).name, end=" ")
                print("\t", end="")
            print("")
