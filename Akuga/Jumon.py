class Artifact():
    """
    The abstraction around an equipment or artifact
    """
    def __init__(self, name, color, blocking):
        self.name = name
        self.color = color
        self.blocking = blocking

    def special_ability(self, next_state_and_variables):
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

    def special_ability(self, next_state_and_variables):
        """
        The very basic ability script which doesnt do anything
        just returns the next_state_and_variables tuple
        state_and_variables: [next_state_to_jump_to, variables_to_pass]
        """
        return next_state_and_variables
