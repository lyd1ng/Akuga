from random import randint
from Akuga.Position import Position
from Akuga import global_definitions


class Player:
    """
    Represents the player of the Akuga game
    A can either be in the summon phase where per is forced to summon
    a Jumon. If every jumon is set the player goes into move phase
    where per is allowed to move one of the jumons
    """
    def __init__(self, name, is_neutral=False):
        self.name = name
        self.phase = 0
        self.jumons_to_summon = []
        self.summoned_jumons = []
        self.is_dead = False
        self.has_won = False

    def SetJumonsToSummon(self, jumons):
        """
        Set the jumons to summon
        """
        self.jumons_to_summon = jumons

    def InSummonPhase(self):
        """
        Returns if the player is in the summon phase
        """
        return self.phase == 0

    def InMovePhase(self):
        """
        Represent if the player is in the move phase
        """
        return self.phase == 1

    def SetToSummonPhase(self):
        """
        Set the player in the summon phase
        """
        self.phase = 0

    def SetToMovePhase(self):
        """
        Set the player in the move phase
        """
        self.phase = 1

    def OwnsTile(self, arena, tile_position):
        """
        Returns if the tile of the arena is already owmed by the player
        Used to check if a move or a summoning is legal for instance
        """
        jumon = arena.GetUnitAt(tile_position)
        if jumon is None:
            """
            If the tile is free it cant be owned by the player
            """
            return False
        if jumon in self.summoned_jumons:
            """
            If the jumon at this tile is within the list of summoned jumons
            the player controls a jumon at this tile which means per owns it
            """
            return True
        """
        If the tile is neither empty nor the jumon at this tile is a jumon
        of the current player an other player has to own this field
        """
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

    def HandleSummoning(self, jumon):
        """
        This function is invoked from the state machiene and summons
        a jumon. That means the jumon is moved from
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
        print("To summon ", end="")
        print(self.jumons_to_summon if global_definitions.DEBUG else "")
        print("Summoned summon ", end="")
        print(self.summoned_jumons if global_definitions.DEBUG else "")
        print("Current Phase: ", end="")
        print(self.phase if global_definitions.DEBUG else "")

    def HandleJumonDeath(self, jumon):
        """
        Handles the death of a jumon, aka removes it from the summoned_jumons
        list an invoke UpdatePlayer
        """
        self.summoned_jumons.remove(jumon)
        self.UpdatePlayer()

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
        """
        Returns if the player is dead or not, dead players are removed
        from the player chain.
        """
        return self.is_dead

    def HasWon(self):
        """
        Returns if a player has won. If a player has won the match ends
        immediatly
        """
        return self.has_won

    def Kill(self):
        """
        Kill the player, a player is killed if per doesnt own a single jumon
        anymore
        """
        self.is_dead = True
        self.has_won = False

    def InstaWin(self):
        """
        Makes the player the winner, this might be usefull for alternative
        win conditions
        """
        self.is_dead = False
        self.has_won = True


class NeutralPlayer(Player):
    """
    Represents a neutral player which can never win nor loose.
    The neutral player is used to control neutral jumons which agains brings
    a random element to the game. Furthermore neutral jumons can be equiped
    with artefacts which can be stolen by the player bakugans by killing
    the neutral ones.
    """
    def __init__(self, arena):
        self.arena = arena
        super().__init__("neutral player", True)

    def SummonJumons(self):
        """
        This function has to be invoked before artefacts are placed on
        the arena, this way the summoning can be handeld without the akuga fsm
        THIS IS MAYBE HANDELD WITHIN AN EXTRA INIT STATE IN THE FUTURE
        """
        # Make sure is no summoning on an occupyied tile
        summon_positions = []
        width = global_definitions.BOARD_WIDTH - 1
        height = global_definitions.BOARD_HEIGHT - 1
        for jumon in self.jumons_to_summon:
            position = Position(randint(0, width), randint(0, height))
            if position not in summon_positions:
                """
                If there is no jumon at this position yet summon it there
                """
                self.HandleSummoning(jumon)
                self.arena.PlaceUnitAt(jumon, position)
                jumon.SetPosition(position)
                # Now add the position to positions to make this tile occupied
                summon_positions.append(position)

    def DoAMove(self, current_state, next_state_and_variables):
        """
        Do a move by selecting a random jumon and invoke its special
        ability. The special ability has to do the move by creating a state
        change. This way the fsm handels the move correctly and will end
        the turn of the neutral player.
        """
        random_index = randint(0, len(self.summoned_jumons) - 1)
        state_change = next_state_and_variables
        state_change = self.summoned_jumons[random_index].\
            SpecialAbility(current_state, next_state_and_variables)
        return state_change
