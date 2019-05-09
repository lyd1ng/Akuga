from Akuga import global_definitions


class Player:
    """
    Represents the player of the Akuga game
    A can either be in the summon phase where per is forced to summon
    a Jumon. If every jumon is set the player goes into move phase
    where per is allowed to move one of the jumons
    """
    def __init__(self, name, jumons):
        self.name = name
        self.phase = 0
        self.jumons_to_summon = jumons
        self.summoned_jumons = []
        self.is_dead = False
        self.has_won = False
    """
    Set and get the phases to avoid dealing with the actual integer number
    """
    def InSummonPhase(self):
        return self.phase == 0

    def InMovePhase(self):
        return self.phase == 1

    def SetToSummonPhase(self):
        self.phase = 0

    def SetToMovePhase(self):
        self.phase = 1

    def OwnsTile(self, tile_position):
        """
        Returns if the tile of the arena is already owmed by
        """
        jumon = global_definitions.ARENA.GetUnitAt(tile_position)
        if jumon is None:
            return False
        if jumon in self.summoned_jumons:
            return True
        return False

    def CanSummon(self, jumon):
        """
        Returns if a player can summon a jumon
        aka if the jumon is within the jumons_to_summon list
        """
        return jumon in self.jumons_to_summon

    def ControlsJumon(self, jumon):
        """
        Returns wheter a player controls a jumon or not
        aka if the jumon is within the summoned_jumons list
        """
        return jumon in self.summoned_jumons

    def HandleSummoning(self, jumon, summon_position):
        """
        This function is invoked from the state machiene and summons
        a jumon. That means the jumon is moved from
        the jumon_to_summon list to the summone_jumons list and switches
        the phase this player is in if there are no jummons to summon left
        Also the jumon is placed on the target arena tile
        """
        if self.InSummonPhase() is False:
            """
            This should never happen but handle it anyway with a clear
            debug message
            """
            print("Invalid move, summoning a jumon is only allowed in summon phase")
            return None
        if jumon not in self.jumons_to_summon:
            """
            This should never happen but handle it anyway with a clear
            debug message
            """
            print("Invalid move, this jumon to summon is not within the")
            print("list of jumons to summon of the curret player")
            return None
        # Change the jumon from jumons_to_summon to summoned_jumons
        self.summoned_jumons.append(jumon)
        self.jumons_to_summon.remove(jumon)
        # Add the jumon to the arena at the given position
        global_definitions.ARENA.PlaceUnitAt(jumon, summon_position)
        """
        If there are no more jumons to summon left the player changes into
        the move phase
        """
        if len(self.jumons_to_summon) < 1:
            self.SetToMovePhase()
        print("To summon ", end="")
        print(self.jumons_to_summon if global_definitions.DEBUG else "")
        print("Summoned summon ", end="")
        print(self.summoned_jumons if global_definitions.DEBUG else "")
        print("Current Phase: ", end="")
        print(self.phase if global_definitions.DEBUG else "")

    def UpdatePlayer(self):
        """
        Updates if the player is dead or not and set the phase of the player
        """
        if len(self.jumons_to_summon) < 1 and len(self.summoned_jumons) < 1:
            self.Kill()
        """
        If there are no more jumons to summon left the player changes into
        the move phase
        """
        if len(self.jumons_to_summon) < 1:
            self.SetToMovePhase()

    def IsDead(self):
        return self.is_dead

    def HasWon(self):
        return self.has_won

    def Kill(self):
        self.is_dead = True
        self.has_won = False

    def InstaWin(self):
        self.is_dead = False
        self.has_won = True
