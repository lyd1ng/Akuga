class Artifact():
    """
    The abstraction around an equipment or artifact
    """
    def __init__(self, name, color, ability_script):
        self.name = name
        self.color = color
        self.ability_script = ability_script

    def run_ability_script(self):
        """
        Run the ability script of the artifact if its not None, which
        it never should be
        """
        if self.ability_script is not None:
            exec(self.ability_script)


class Jumon():
    """
    The abstraction class around the Jumon,
    which is the unit to summon by a player
    """
    def __init__(self, name, color, base_level, movement,
                 equipment, ability_script, owned_by):
        super().__init__()
        self.name = name
        self.color = color
        self.base_level = base_level
        self.level_offset = 0
        self.movement = movement
        self.equipment = equipment
        self.ability_script = ability_script
        self.owned_by = owned_by
        self.blocking = False

    def run_ability_script(self):
        """
        Invoke the ability script of the jumon and the ability
        scripts of the equipment attached to the jumon
        """
        if self.ability_script is not None:
            exec(self.ability_script)
        if self.equipment is not None:
            self.equipment.run_ability_script()
