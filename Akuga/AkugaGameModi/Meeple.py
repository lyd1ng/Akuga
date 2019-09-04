class Artefact():
    """
    The abstraction around an equipment or artifact
    """
    def __init__(self, name, _id, position):
        self.name = name
        self._id = self.id
        self.position = position

    def attach_to(self, jumon):
        """
        Attach the artefact to jumon
        """
        self.position = jumon.get_position()
        jumon.equipment = self

    def detach_from(self, jumon):
        """
        Detach the artefact from jumon
        """
        self.position = jumon.get_position()
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

    def get_position(self):
        """
        Get the position of this artefact
        """
        return self.position


class Jumon():
    """
    The abstraction class around the Jumon,
    which is the unit to summon by a player
    """
    def __init__(self, name, _id, color, attack, defense, movement,
                 equipment=None, owned_by=None):
        super().__init__()
        self.name = name
        self.id = _id
        self.color = color
        self.attack = attack
        self.defense = defense
        self.movement = movement
        self.equipment = equipment
        self.owned_by = owned_by
        self.position = None
        # Two dictionaries of the form
        # interfering_jumon_name: (attack_intf, defense_int, movement_int)
        # The nonpersisten interferences are cleared in the turn_begin
        # state of the rule building fsm while the persisten interferences
        # have to be cleared manually
        # These interferences will be used to get the total attack, defense
        # an movement value of the jumon
        self.persistent_interf = {}
        self.nonpersistent_interf = {}

    def set_position(self, position):
        """
        Just set the position of the jumon,
        set the position of its equipment as well
        """
        self.position = position
        if self.equipment is not None:
            self.equipment.set_position(position)

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

    def is_special_move_legal(self, arena, current_position, target_position):
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

    def get_total_movement(self):
        """
        Sum up the movement and all movement interferences
        """
        total_movement = self.movement
        for interf in self.nonpersistent_interf.values():
            total_movement += interf[2]
        for interf in self.persistent_interf.values():
            total_movement += interf[2]
        return total_movement
