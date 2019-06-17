from random import randint
from Akuga.MatchServer.Position import Position
from Akuga.MatchServer import GlobalDefinitions


class Artefact():
    """
    The abstraction around an equipment or artifact
    """
    def __init__(self, name, position):
        self.name = name
        self.position = position

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

    def set_position(self, position):
        """
        Set the position of this artefact
        """
        self.position = position

    def get_position(self, position):
        """
        Get the position of this artefact
        """
        return self.position


class Jumon():
    """
    The abstraction class around the Jumon,
    which is the unit to summon by a player
    """
    def __init__(self, name, color, attack, defense, movement,
                 equipment, owned_by):
        super().__init__()
        self.name = name
        self.color = color
        self.attack = attack
        self.defense = defense
        self.movement = movement
        self.equipment = equipment
        self.owned_by = owned_by
        self.position = None
        self.persistent_interf = {}
        self.nonpersistent_interf = {}

    def set_position(self, position):
        """
        Just set the position of the jumon
        """
        self.position = position

    def get_position(self):
        """
        Jus get the position of the jumon
        """
        return self.position

    def set_owner(self, owner):
        """
        Set the owner of this meeple.
        Used in the pick state of the fsm if this jumon is picked
        by a player
        """
        self.owned_by = owner

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

    def do_special_move(self, fsm, current_position, target_position):
        """
        Do the special move and return the state change made by the fsm
        after finishing the check_special_move state
        Normaly the turn ends after a special move
        """
        return (fsm.change_player_state, {})

    def reset_nonpersistent_interf(self):
        """
        Reset the nonpersistent interf,
        this will be used to reset the nonpersistent interf before
        the passive abilities of all jumons triggers.
        This way passive abilities can be implemented rather simple by
        adding an interference to the nonpersistent interference dictionary.
        An interference is just a tuple with the attack and the defense
        value
        """
        self.nonpersistent_interf = {}

    def get_total_attack(self):
        """
        Sum up the attack and all attack interference
        """
        total_attack = self.attack
        for interf in self.nonpersistent_interf.values():
            total_attack += interf[0]
        for interf in self.persistent_interf.values():
            total_attack += interf[0]
        return total_attack

    def get_total_defense(self):
        """
        Sum up the defense and all defense interference
        """
        total_defense = self.defense
        for interf in self.nonpersistent_interf.values():
            total_defense += interf[1]
        for interf in self.persistent_interf.values():
            total_defense += interf[1]
        return total_defense


class TestNeutralJumon(Jumon):
    def __init__(self, name, owned_by):
        super().__init__(name, "red", 300, 300, 2, None, owned_by)

    def wrap(self, x, min_value, max_value):
        """
        Wraps x to [min_value, max_value]
        """
        if x < min_value:
            x = min_value
        if x > max_value:
            x = max_value
        return x

    def special_ability(self, current_state, next_state_and_variables):
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
