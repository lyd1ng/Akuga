from Akuga.MatchServer.Position import Position
from Akuga.MatchServer.Meeple import Jumon


class ArenaTile:
    """
    This represents one tile of an arena.
    It stores attack and defense values for the basic colors of jumons
    as a dictionary of the form {$color: ($attack, $defense)}
    as well as persistent and nonpersistent interferences.
    Both are a dict of dicts storing boni like the original boni dict
    under the name of the interference.
    An ArenaTile can have two different special functions for the one tile
    and the two tile battle phase.
    """
    def __init__(self, boni):
        self.boni = boni
        self.persistent_interf = {}
        self.nonpersistent_interf = {}
        self._occupied_by = None
        self.wasted = False

    def occupied_by(self):
        """
        Returns the unit aka jumon, equipment ocuppying this tile
        """
        return self._occupied_by

    def get_total_attack_bonus(self, jumon):
        """
        Sum up the attack bonus and all attack interference
        """
        color = jumon.color
        total_attack = self.boni[color][0]
        # Go through all interferences and add the
        # attack value of the interference for the color
        # of the jumon. If there is no attack_value for
        # this color do nothing (equally to add 0)
        for interf in self.nonpersistent_interf.values():
            try:
                total_attack += interf[color][0]
            except(KeyError):
                pass
        for interf in self.persistent_interf.values():
            try:
                total_attack += interf[color][0]
            except(KeyError):
                pass
        return total_attack

    def get_total_defense_bonus(self, jumon):
        """
        Sum up the defense bonus and all defense interference
        """
        color = jumon.color
        total_defense = self.boni[color][1]
        # Go through all interferences and add the
        # defense value of the interference for the color
        # of the jumon. If there is no defense value for
        # this color do nothing (equally to add 0)
        for interf in self.nonpersistent_interf.values():
            try:
                total_defense += interf[color][1]
            except(KeyError):
                pass
        for interf in self.persistent_interf.values():
            try:
                total_defense += interf[color][1]
            except(KeyError):
                pass
        return total_defense

    def reset_nonpersistent_interf(self):
        """
        Reset the nonpersistent interf,
        this will be used to reset the nonpersistent interf before
        the passive abilities of all jumons triggers.
        This way passive abilities can be implemented rather simple by
        adding a new interference to the nonpersistent interference
        dictionary.
        An interference is a dictionary on its own with an attack and defense
        value stored with a color as the key
        """
        self.nonpersistent_interf = {}

    def one_tile_special_ability(self, attacking_jumon, defending_jumon,
            current_state, next_state_and_variables):
        """
        The very basic ability script which doesnt do anything
        just returns the next_state_and_variables tuple
        state_and_variables: [next_state_to_jump_to, variables_to_pass]
        Invoked in the boni evaluation state of a one tile battle
        """
        return next_state_and_variables

    def two_tile_special_ability(self, jumon, current_state,
            next_state_and_variables):
        """
        The very basic ability script which doesnt do anything
        just returns the next_state_and_variables tuple
        state_and_variables: [next_state_to_jump_to, variables_to_pass]
        Invoked in the boni evaluation state of a two tile battle
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
    many ArenaTiles stored in a two dimensional array of the form [x][y]
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
        # Set the unit to the position
        self.tiles[position.x][position.y]._occupied_by = unit

    def print_out(self):
        for y in range(0, self.board_height):
            for x in range(0, self.board_width):
                print("|", end="")
                meeple = self.get_unit_at(Position(x, y))
                if meeple is not None:
                    print(meeple.name, end=" ")
                    print(meeple.get_position(), end=' ')
                    if type(meeple) is Jumon:
                        if self.get_unit_at(Position(x, y)).equipment is not None:
                            print(str(self.get_unit_at(Position(x, y)).
                                equipment.get_position()), end=' ')
                print("\t", end="")
            print("")
