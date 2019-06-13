from Akuga.MatchServer.Meeple import Jumon
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
    def __init__(self, boni):
        self.boni = boni
        self._occupied_by = None
        self.wasted = False

    def occupied_by(self):
        """
        Returns the unit aka jumon, equipment ocuppying this tile
        """
        return self._occupied_by

    def is_blocked(self):
        """
        Returns whether the unit occupying this tile is blocking or not
        """
        if self._occupied_by is not None:
            return self._occupied_by.blocking
        return False

    def get_attack_bonus(self, jumon):
        """
        Return the attack bonus for the color of the jumon
        """
        try:
            return self.boni[jumon.color][0]
        except(KeyError):
            return 0

    def get_defense_bonus(self, jumon):
        """
        Return the defense bonus for the color of the jumon
        """
        try:
            return self.boni[jumon.color][1]
        except(KeyError):
            return 0


    def one_tile_special_ability(self, attacking_jumon, defending_jumon,
            current_state, next_state_and_variables):
        """
        The very basic ability script which doesnt do anything
        just returns the next_state_and_variables tuple
        state_and_variables: [next_state_to_jump_to, variables_to_pass]
        """
        return next_state_and_variables

    def two_tile_special_ability(self, jumon, current_state,
            next_state_and_variables):
        """
        The very basic ability script which doesnt do anything
        just returns the next_state_and_variables tuple
        state_and_variables: [next_state_to_jump_to, variables_to_pass]
        """
        return next_state_and_variables

    def set_wasted(self, wasted):
        """
        Set the wasted predicat of this tile
        """
        self.wasted = wasted

    def is_wasted(self):
        """
        Return the wasted predicat of this tile
        """
        return self.wasted


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
        Set unit to None to remove a unit from an arena tile
        """
        if unit is not None:
            """
            If a unit is placed set its position as well
            """
            unit.set_position(position)
            if type(unit) is Jumon and unit.equipment is not None:
                """
                If the unit is a jumon and it has an artefact equipped
                set its position as well
                """
                unit.equipped.set_position(position)
        # Set the unit to the position
        self.tiles[position.x][position.y]._occupied_by = unit

    def print_out(self):
        for y in range(0, self.board_height):
            for x in range(0, self.board_width):
                print("|", end="")
                if self.get_unit_at(Position(x, y)) is not None:
                    print(self.get_unit_at(Position(x, y)).name, end=" ")
                    print(str(self.get_unit_at(Position(x, y)).get_position()), end=' ')
                print("\t", end="")
            print("")
