"""
from Akuga.AkugaStates import (
        idle_state,
        summon_state,
        check_move_state,
        check_special_move_state,
        summon_check_state,
        change_player_state,
        equip_artefact_to_jumon_state,
        one_tile_battle_begin_state,
        one_tile_battle_flip_state,
        one_tile_battle_boni_evaluation_state,
        one_tile_battle_fight_state,
        one_tile_battle_aftermath_state,
        two_tile_battle_begin_state,
        two_tile_battle_flip_state,
        two_tile_battle_boni_evaluation_state,
        two_tile_battle_fight_state,
        two_tile_battle_aftermath_state)
"""
from Akuga import AkugaStates
from Akuga.Position import Position


class Artefact():
    """
    The abstraction around an equipment or artifact
    """
    def __init__(self, name, blocking):
        self.name = name
        self.blocking = blocking

    def attach_to(self, jumon):
        """
        Attach the artefact to jumon
        """
        jumon.equipment = self

    def detach_from(self, jumon):
        """
        Detach the artefact from jumon
        """
        jumon.equipment = None

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


class TestArtefact(Artefact):
    """
    Change the name of the jumon
    """
    def __init__(self):
        super().__init__("A1", False)
        self.saved_jumon_name = ""

    def attach_to(self, jumon):
        self.saved_jumon_name = jumon.name
        jumon.name += " A1"
        jumon.level_offset += 150
        super().attach_to(jumon)

    def detach_from(self, jumon):
        jumon.name = self.saved_jumon_name
        jumon.level_offset -= 150
        super().detach_from(jumon)

    def special_ability(self, jumon, current_state, next_state_and_variables):
        print(jumon.name + " is active in state " + current_state.name)
        return next_state_and_variables


class Test2Artefact(Artefact):
    """
    Change the name of the jumon
    """
    def __init__(self):
        super().__init__("A2", False)
        self.saved_jumon_name = ""

    def attach_to(self, jumon):
        self.saved_jumon_name = jumon.name
        jumon.name += " equiped2"
        super().attach_to(jumon)

    def detach_from(self, jumon):
        jumon.name = self.saved_jumon_name
        super().detach_from(jumon)


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
