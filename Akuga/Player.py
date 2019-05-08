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

    def HandleSummoning(self, jumon):
        """
        This function changes the internal representation of the player
        when a jumon is summoned. That means the jumon is moved from
        the jumon_to_summon list to the summone_jumons list and switches
        the phase this player is in if there are no jummons to summon left
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
        """
        If there are no more jumons to summon left the player changes into
        the move phase
        """
        if len(self.jumons_to_summon) < 1:
            self.SetToMovePhase()

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
        self.has_won = True
