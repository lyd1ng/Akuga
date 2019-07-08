from random import randint
from Akuga.MatchServer.Position import Position
from Akuga.MatchServer import GlobalDefinitions


class Player:
    """
    Represents the player of the Akuga game
    A can either be in the summon phase where per is forced to summon
    a Jumon. If every jumon is set the player goes into move phase
    where per is allowed to move one of the jumons
    """
    def __init__(self, name, is_neutral=False):
        self.name = name
        self.phase = "pick_phase"
        self.jumons_to_summon = []
        self.summoned_jumons = []
        self._is_dead = False
        self._has_won = False
        self.timeout_counter = 0

    def set_jumons_to_summon(self, jumons):
        """
        Set the jumons to summon
        """
        self.jumons_to_summon = jumons
        # Set the owner of the jumons
        for j in self.jumons_to_summon:
            j.set_owner(self)

    def add_jumon_to_summon(self, jumon):
        """
        Add a jumon to summon
        """
        jumon.set_owner(self)
        self.jumons_to_summon.append(jumon)

    def in_pick_phase(self):
        """
        Returns if the player is in the pick phase
        """
        return self.phase == "pick_phase"

    def in_summon_phase(self):
        """
        Returns if the player is in the summon phase
        """
        return self.phase == "summon_phase"

    def in_move_phase(self):
        """
        Represent if the player is in the move phase
        """
        return self.phase == "move_phase"

    def set_to_summon_phase(self):
        """
        Set the player in the summon phase
        """
        self.phase = "summon_phase"

    def set_to_move_phase(self):
        """
        Set the player in the move phase
        """
        self.phase = "move_phase"

    def owns_tile(self, arena, tile_position):
        """
        Returns if the tile of the arena is already owmed by the player
        Used to check if a move or a summoning is legal for instance
        """
        jumon = arena.get_unit_at(tile_position)
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

    def can_summon(self, jumon):
        """
        Returns if a player can summon a jumon
        aka if the jumon is within the jumons_to_summon list
        """
        return jumon in self.jumons_to_summon

    def controls_jumon(self, jumon):
        """
        Returns wheter a player controls a jumon or not
        aka if the jumon is within the summoned_jumons list
        """
        return jumon in self.summoned_jumons

    def handle_summoning(self, jumon):
        """
        This function is invoked from the state machiene and summons
        a jumon. That means the jumon is moved from
        the jumon_to_summon list to the summone_jumons list and switches
        the phase this player is in if there are no jummons to summon left
        """
        # Change the jumon from jumons_to_summon to summoned_jumons
        self.summoned_jumons.append(jumon)
        self.jumons_to_summon.remove(jumon)
        """
        If there are no more jumons to summon left the player changes into
        the move phase
        """
        if len(self.jumons_to_summon) < 1:
            self.set_to_move_phase()

    def handle_jumon_death(self, jumon):
        """
        Handles the death of a jumon, aka removes it from the summoned_jumons
        list an invoke update_player
        """
        self.summoned_jumons.remove(jumon)
        self.update_player()

    def update_player(self):
        """
        updates if the player is dead or not and set the phase of the player
        """
        if len(self.jumons_to_summon) < 1 and len(self.summoned_jumons) < 1:
            self.kill()
        else:
            self._is_dead = False
        """
        If there are no more jumons to summon left the player changes into
        the move phase
        """
        if len(self.jumons_to_summon) < 1:
            self.set_to_move_phase()
        else:
            self.set_to_summon_phase()

    def is_dead(self):
        """
        Returns if the player is dead or not, dead players are removed
        from the player chain.
        """
        return self._is_dead

    def has_won(self):
        """
        Returns if a player has won. If a player has won the match ends
        immediatly
        """
        return self._has_won

    def kill(self):
        """
        kill the player, a player is killed if per doesnt own a single jumon
        anymore
        """
        self._is_dead = True
        self._has_won = False

    def insta_win(self):
        """
        Makes the player the winner, this might be usefull for alternative
        win conditions
        """
        self._is_dead = False
        self._has_won = True

    def increment_timeout_counter(self):
        """
        Increment the timeout counter
        """
        self.timeout_counter += 1

    def get_timeout_counter(self):
        """
        Get the timeout counter
        """
        return self.timeout_counter


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
        super().set_to_summon_phase()

    def summon_jumons(self):
        """
        This function has to be invoked before artefacts are placed on
        the arena, this way the summoning can be handeld without the akuga fsm
        THIS IS MAYBE HANDELD WITHIN AN EXTRA INIT STATE IN THE FUTURE
        """
        # Make sure is no summoning on an occupyied tile
        summon_positions = []
        width = GlobalDefinitions.BOARD_WIDTH - 1
        height = GlobalDefinitions.BOARD_HEIGHT - 1
        for jumon in self.jumons_to_summon:
            position = Position(randint(0, width), randint(0, height))
            if position not in summon_positions:
                """
                If there is no jumon at this position yet summon it there
                """
                self.handle_summoning(jumon)
                self.arena.place_unit_at(jumon, position)
                jumon.set_position(position)
                # Now add the position to positions to make this tile occupied
                summon_positions.append(position)

    def do_a_move(self, current_state, next_state_and_variables):
        """
        Do a move by selecting a random jumon and invoke its special
        ability. The special ability has to do the move by creating a state
        change. This way the fsm handels the move correctly and will end
        the turn of the neutral player.
        """
        random_index = randint(0, len(self.summoned_jumons) - 1)
        state_change = next_state_and_variables
        state_change = self.summoned_jumons[random_index].\
            special_ability(current_state, next_state_and_variables)
        return state_change
