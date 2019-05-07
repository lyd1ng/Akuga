class Jumon():
    """
    The abstraction class around the Jumon,
    which is the unit to summon by a player
    """
    def __init__(self, base_level, movement, equipments, owned_by, ability_script):
        super().__init__()
        self.base_level = base_level
        self.base_level_offset = 0
        self.movement = movement
        self.equipments = equipments
        self.ability_script = ability_script
        self.owned_by = owned_by
