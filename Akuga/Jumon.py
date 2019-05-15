from Akuga import AkugaStates
from Akuga.Position import Position


class Artifact():
    """
    The abstraction around an equipment or artifact
    """
    def __init__(self, name, color, blocking):
        self.name = name
        self.color = color
        self.blocking = blocking

    def special_ability(self, jumon, current_state, next_state_and_variables):
        """
        The very basic ability script which doesnt do anything
        just returns the next_state_and_variables tuple
        state_and_variables: [next_state_to_jump_to, variables_to_pass]
        """
        return next_state_and_variables


class Jumon():
    """
    The abstraction class around the Jumon,
    which is the unit to summon by a player
    """
    def __init__(self, name, color, base_level, movement,
                 equipment, owned_by):
        super().__init__()
        self.name = name
        self.color = color
        self.base_level = base_level
        self.level_offset = 0
        self.movement = movement
        self.equipment = equipment
        self.owned_by = owned_by
        self.blocking = False

    def special_ability(self, current_state, next_state_and_variables):
        """
        The very basic ability script which doesnt do anything
        just returns the next_state_and_variables tuple
        state_and_variables: [next_state_to_jump_to, variables_to_pass]
        """
        state_change = next_state_and_variables
        # If the jumon has an equipment invoke its ability script also
        if self.equipment is not None:
            state_change = self.equipment.special_ability(self,
                    current_state, next_state_and_variables)
        return state_change

    def is_special_move_legal(self, current_position, target_position):
        """
        Returns whether a special move is legal or not
        """
        return False

    def do_special_move(self, current_position, target_position):
        """
        Do the special move and return the state change made by the fsm
        after finishing the check_special_move state
        Normaly the turn ends after a special move
        """
        return (AkugaStates.change_player_state, {})


class TestJumon(Jumon):
    def __init__(self, color, base_level, movement,
                 equipment, owned_by):
        super().__init__("TestJumon", color, base_level, movement, equipment, owned_by)

    def special_ability(self, current_state, next_state_and_variables):
        """
        The very basic ability script which doesnt do anything
        just returns the next_state_and_variables tuple
        state_and_variables: [next_state_to_jump_to, variables_to_pass]
        """
        if current_state is AkugaStates.summon_state:
            next_state_and_variables[1]["summon_position"] = Position(0, 0)
        return next_state_and_variables


class Test2Jumon(Jumon):
    def __init__(self, color, base_level, movement,
                 equipment, owned_by):
        super().__init__("Test2Jumon", color, base_level, movement, equipment, owned_by)

    def special_ability(self, current_state, next_state_and_variables):
        """
        Try a state change if this jumon is summoned so the player has
        a second turn
        """
        if current_state is AkugaStates.summon_check_state\
                or current_state is AkugaStates.one_tile_battle_aftermath_state:
            print("Jump to idle state for an extra turn")
            return (AkugaStates.idle_state, {})
        return next_state_and_variables
