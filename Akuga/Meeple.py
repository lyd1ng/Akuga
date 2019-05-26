from random import randint
from Akuga.Position import Position
from Akuga import GlobalDefinitions


class Artefact():
    """
    The abstraction around an equipment or artifact
    """
    def __init__(self, name, blocking):
        self.name = name
        self.blocking = blocking

    def AttachTo(self, jumon):
        """
        Attach the artefact to jumon
        """
        jumon.equipment = self

    def DetachFrom(self, jumon):
        """
        Detach the artefact from jumon
        """
        jumon.equipment = None

    def SpecialAbility(self, jumon, current_state, next_state_and_variables):
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
        self.position = None

    def SetPosition(self, position):
        """
        Just set the position of the jumon
        """
        self.position = position

    def SetOwner(self, owner):
        """
        Set the owner of this meeple.
        Used in the pick state of the fsm if this jumon is picked
        by a player
        """
        self.owned_by = owner

    def SpecialAbility(self, current_state, next_state_and_variables):
        """
        The very basic ability script which doesnt do anything
        just returns the next_state_and_variables tuple
        state_and_variables: [next_state_to_jump_to, variables_to_pass]
        """
        state_change = next_state_and_variables
        # If the jumon has an equipment invoke its ability script also
        if self.equipment is not None:
            state_change = self.equipment.SpecialAbility(self,
                    current_state, next_state_and_variables)
        return state_change

    def IsSpecialMoveLegal(self, current_position, target_position):
        """
        Returns whether a special move is legal or not
        """
        return False

    def DoSpecialMove(self, fsm, current_position, target_position):
        """
        Do the special move and return the state change made by the fsm
        after finishing the check_special_move state
        Normaly the turn ends after a special move
        """
        return (fsm.change_player_state, {})


class TestArtefact(Artefact):
    """
    Change the name of the jumon
    """
    def __init__(self):
        super().__init__("A1", False)
        self.saved_jumon_name = ""

    def AttachTo(self, jumon):
        self.saved_jumon_name = jumon.name
        jumon.name += " A1"
        jumon.level_offset += 150
        super().AttachTo(jumon)

    def DetachFrom(self, jumon):
        jumon.name = self.saved_jumon_name
        jumon.level_offset -= 150
        super().DetachFrom(jumon)

    def SpecialAbility(self, jumon, current_state, next_state_and_variables):
        print(jumon.name + " is active in state " + current_state.name)
        return next_state_and_variables


class Test2Artefact(Artefact):
    """
    Change the name of the jumon
    """
    def __init__(self):
        super().__init__("A2", False)
        self.saved_jumon_name = ""

    def AttachTo(self, jumon):
        self.saved_jumon_name = jumon.name
        jumon.name += " equiped2"
        super().AttachTo(jumon)

    def DetachFrom(self, jumon):
        jumon.name = self.saved_jumon_name
        super().DetachFrom(jumon)


class TestJumon(Jumon):
    def __init__(self, color, base_level, movement,
                 equipment, owned_by):
        super().__init__("TestJumon", color, base_level, movement, equipment, owned_by)

    def SpecialAbility(self, current_state, next_state_and_variables):
        """
        The very basic ability script which doesnt do anything
        just returns the next_state_and_variables tuple
        state_and_variables: [next_state_to_jump_to, variables_to_pass]
        """
        if current_state is current_state.fsm.summon_state:
            next_state_and_variables[1]["summon_position"] = Position(0, 0)
        return next_state_and_variables


class Test2Jumon(Jumon):
    def __init__(self, color, base_level, movement,
                 equipment, owned_by):
        super().__init__("Test2Jumon", color, base_level, movement, equipment, owned_by)

    def SpecialAbility(self, current_state, next_state_and_variables):
        """
        Try a state change if this jumon is summoned so the player has
        a second turn
        """
        if current_state is current_state.fsm.summon_check_state\
                or current_state is current_state.fsm.one_tile_battle_aftermath_state:
            print("Jump to idle state for an extra turn")
            return (current_state.fsm.idle_state, {})
        return next_state_and_variables


class TestNeutralJumon(Jumon):
    def __init__(self, owned_by):
        super().__init__("N1", "red", 300, 2, None, owned_by)

    def wrap(self, x, min_value, max_value):
        """
        Wraps x to [min_value, max_value]
        """
        if x < min_value:
            x = min_value
        if x > max_value:
            x = max_value
        return x

    def SpecialAbility(self, current_state, next_state_and_variables):
        """
        Archieve a state change to the check move state
        """
        if current_state is current_state.fsm.idle_state:
            width = GlobalDefinitions.BOARD_WIDTH - 1
            height = GlobalDefinitions.BOARD_HEIGHT - 1
            random_target = self.position +\
                Position(randint(-1, 1), randint(-1, 1))
            random_target.x = self.wrap(random_target.x, 0, width)
            random_target.y = self.wrap(random_target.y, 0, height)
            return (current_state.fsm.check_move_state, {
                "jumon_to_move": self,
                "current_position": self.position,
                "target_position": random_target})
        return next_state_and_variables
