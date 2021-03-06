import random
import time
import Akuga.AkugaGameModi.Meeple
from Akuga.AkugaGameModi.LastManStanding import GlobalDefinitions
from Akuga.AkugaGameModi.PathFinder import find_path
from Akuga.AkugaGameModi.Position import Position
from Akuga.AkugaGameModi.Player import NeutralPlayer
from Akuga.AkugaGameModi.StateMachieneState import StateMachieneState as State
from Akuga.AkugaGameModi.NetworkProtocoll import (propagate_message)
from Akuga.EventDefinitions import (Event,
                                    SUMMON_JUMON_EVENT,
                                    SELECT_JUMON_TO_MOVE_EVENT,
                                    SELECT_JUMON_TO_SPECIAL_MOVE_EVENT,
                                    PICK_JUMON_EVENT,
                                    PLAYER_HAS_WON,
                                    MATCH_IS_DRAWN,
                                    TURN_ENDS,
                                    TIMEOUT_EVENT,
                                    MESSAGE)


def jumon_fight(attacking_jumon, attacking_bonus,
                defending_jumon, defending_bonus):
    """
    Return the winner and the looser as a tupel of the form
    ($winner, $looser). If the fight was drawn return None for
    both.
    """
    if attacking_jumon.attack + attacking_bonus >\
            defending_jumon.defense + defending_bonus:
        return (attacking_jumon, defending_jumon)
    elif attacking_jumon.attack + attacking_bonus <\
            defending_jumon.defense + defending_bonus:
        return (defending_jumon, attacking_jumon)
    else:
        return (None, None)


def propagating_handle_jumon_death(jumon, players):
    '''
    Handles the death of a jumon and propagates this
    as an inter turn event
    '''
    # Handle the death of the jumon
    jumon.owned_by.handle_jumon_death(jumon)
    # Propagate a burying_jumon inter turn event
    burying_itevent = Event(MESSAGE, players=players,
        tokens=['BURYING_JUMON_ITEVENT', jumon.id])
    propagate_message(burying_itevent)


class TurnBeginState(State):
    """
    This represents the moment a turn begins, in this state
    the nonpersistent interferences are refreshed
    """
    def __init__(self, fsm):
        super().__init__("turn_begin_state", fsm)

    def run(self, event):
        """
        Refresh the interferences and jump to the wait_for_user_state
        To allow passive special abilities the nonpersistent interference
        of all jumons and all arena tiles has to be cleared. Then
        the special ability script of all jumons (even the neutral ones)
        can be invoked without allowing a state change.
        """
        # Reset the nonpersistent interference of all arena tiles
        for row in self.fsm.arena.tiles:
            for arena_tile in row:
                arena_tile.reset_nonpersistent_interf()
        # Reset the nonpersistent  interference of all jumons
        for player in self.fsm.player_chain.get_players():
            for jumon in player.summoned_jumons:
                jumon.reset_nonpersistent_interf()

        # Go through all players, even the neutral player
        for player in self.fsm.player_chain.get_players():
            # Go through all jumons that player summoned
            for jumon in player.summoned_jumons:
                # There is no state change planed nor are there state variables
                jumon.special_ability(self, None)
        # Start the timeout timer
        self.fsm.timeout_timer = 0
        self.fsm.old_time = time.time()
        self.fsm.current_time = self.fsm.old_time
        # If the turn starts regularly no jumon is enforced to be the
        # active jumon and no event is enforced to be recieved from the player
        return (self.fsm.wait_for_user_state, {
            "enforced_jumon": None,
            "enforced_event": None})


class TurnEndState(State):
    """
    This represent the end of a turn, which is used to handle post
    turn state changes. Those can be used to e.g implement mass displacements
    """
    def __init__(self, fsm):
        super().__init__("turn_end_state", fsm)

    def run(self, event):
        """
        As long as their are post turn state changes on the stack execute
        them and dont jump to the change player state
        """
        if len(self.fsm.post_turn_state_changes) > 0:
            return self.fsm.post_turn_state_changes.pop(0)
        return (self.fsm.change_player_state, {})


class WaitForUserState(State):
    """
    The representation of the wait_for_user_state which is the normal
    state a user idles in until per decides do something.
    """
    def __init__(self, fsm):
        super().__init__("wait_for_user_state", fsm)

    def run(self, event):
        """
        Listen on SUMMON_JUMON_EVENT and SELECT_JUMON_TO_MOVE_EVENT as well
        as SELECT_JUMON_TO_SPECIAL_MOVE_EVENT
        """
        # Get the current time
        self.fsm.current_time = time.time()
        self.fsm.timeout_timer += self.fsm.current_time - self.fsm.old_time
        self.fsm.old_time = self.fsm.current_time
        if self.fsm.timeout_timer > GlobalDefinitions.SECONDS_PER_TURN:
            return (self.fsm.timeout_state, {})
        if type(self.fsm.player_chain.get_current_player()) is\
                NeutralPlayer and self.fsm.player_chain.\
                get_current_player().in_move_phase():
            """
            If the current player is a neutral player invoke its do_a_move
            Function and use its return to archieve a state change.
            """
            state_change = self.fsm.player_chain.\
                get_current_player().do_a_move(self, (None, {}))
            """
            Do the state change created by the special ability
            of the jumon moved
            """
            if state_change[0] is not None:
                return state_change

        # If the player times out jump to the timeout state
        if event.type == TIMEOUT_EVENT:
            return (self.fsm.timeout_state, {})

        # If the event type is not a user event dont do anything
        # (0 to 100 is the range of user events)
        if event.type < 0 or event.type > 100:
            return None

        # Now its assured that the event is a user event
        # So it can be tested if the selected jumon is the enforced
        # jumon, if there is one
        if self.state_variables["enforced_jumon"] and\
                (event.jumon is not self.state_variables["enforced_jumon"]):
            return None

        # If the enforced event is not none check if the received event
        # type matches the enforced event. Return none, so do nothing,
        # if the event type doesnt match the enforced event
        if self.state_variables["enforced_event"] and\
                (event.type != self.state_variables["enforced_event"]):
            return None

        print("EVENT TYPE: " + str(event.type))
        if event.type == PICK_JUMON_EVENT\
                and self.fsm.player_chain.get_current_player().\
                in_pick_phase():
            """
            The event is only valid if the current player is in the pick
            phase, and the jumon within the event is inside the
            jumon_pick_pool list
            """
            # Get the jumon to pick from the event
            jumon = event.jumon
            if jumon in self.fsm.jumon_pick_pool:
                """
                Only jump to the pick state if the jumon is
                within the pick pool
                """
                pick_state_variables = {"jumon_to_pick": jumon}
                return (self.fsm.pick_state, pick_state_variables)

        if event.type == SUMMON_JUMON_EVENT\
                and self.fsm.player_chain.get_current_player().\
                in_summon_phase():
            """
            The event is only valid if the current player is in the move
            phase, the jumon within the event is inside the
            jumons_to_summon list.
            """
            # Get the jumon to summon and create the state variables dict
            jumon = event.jumon
            # Only summon the jumon if the player owns the jumon
            if self.fsm.player_chain.get_current_player().\
                    can_summon(jumon):
                # Jump to the summon state
                summon_state_variables = {"jumon_to_summon": jumon}
                return (self.fsm.summon_state, summon_state_variables)

        if event.type == SELECT_JUMON_TO_MOVE_EVENT\
                and self.fsm.player_chain.get_current_player().in_move_phase():
            """
            Get the jumon to move, its position and the target position
            from the event. The CheckMoveState will check if the move is
            legal or not and handles the move
            """
            jumon = event.jumon
            current_position = event.current_position
            target_position = event.target_position
            # Only move the jumon if the current player controls the jumon
            if self.fsm.player_chain.get_current_player().\
                    controls_jumon(jumon):
                check_move_state_variables = {
                    "jumon_to_move": jumon,
                    "current_position": current_position,
                    "target_position": target_position}
                # Jump to the check move state
                return (self.fsm.check_move_state, check_move_state_variables)

        if event.type == SELECT_JUMON_TO_SPECIAL_MOVE_EVENT\
                and self.fsm.player_chain.get_current_player().in_move_phase():
            """
            Get the jumon to move, its position and the target position
            from the event. The CheckSpecialMoveState will check if the
            move is legal or not and handles the move.
            """
            jumon = event.jumon
            current_position = event.current_position
            target_position = event.target_position
            check_move_state_variables = {
                "jumon_to_move": jumon,
                "current_position": current_position,
                "target_position": target_position}
            # Jump to the check_special_move_state
            return (self.fsm.check_special_move_state,
                check_move_state_variables)
        # If no event was caught return None, so the state machiene
        # remains in the idle state
        return None


class PickState(State):
    """
    PickState is the representation of the moment a jumon is picked
    from the jumon pick pool. A picked jumon is removed from the pick pool
    and added to the jumon_to_summon list of the current player.
    This way the player can summon the jumon later on.
    """
    def __init__(self, fsm):
        super().__init__("pick_state", fsm)

    def run(self, event):
        """
        Remove the jumon to pick from the pick pool and add it to the jumons
        the current player can summon. Then check if the player has to
        switch to the summon phase.
        """
        jumon = self.state_variables["jumon_to_pick"]
        jumon.set_owner(self.fsm.player_chain.get_current_player())
        self.fsm.jumon_pick_pool.remove(jumon)
        self.fsm.player_chain.get_current_player().add_jumon_to_summon(jumon)
        # Propagate a pick inter turn event
        pick_ite = Event(MESSAGE, players=self.fsm.player_chain.get_players(),
            tokens=['PICK_ITEVENT',
            self.fsm.player_chain.get_current_player().name, jumon.id])
        propagate_message(pick_ite)
        if len(self.fsm.jumon_pick_pool) <\
                self.fsm.player_chain.get_not_neutral_length():
            """
            If there are less jumons in the pick pool than not neutral
            player in the playerchain the current player wont be able to
            pick another jumon, so per must go into the summon phase
            """
            print(len(self.fsm.jumon_pick_pool))
            print(self.fsm.player_chain.get_not_neutral_length())
            self.fsm.player_chain.get_current_player().set_to_summon_phase()
        # The turn ends, so jump to the change player state
        return (self.fsm.turn_end_state, {})


class SummonState(State):
    """
    SummonState is the representation of the moment a jumon is summoned.
    In this state a random position if generated and its always jumped
    to the SummonCheckState
    """
    def __init__(self, fsm):
        super().__init__("summon_state", fsm)

    def run(self, event):
        """
        Just create a random position and jump to the
        summon_check_state with the position and the summon as
        summon_check_state_variables
        """
        x_position = random.randint(0, GlobalDefinitions.BOARD_WIDTH - 1)
        y_position = random.randint(0, GlobalDefinitions.BOARD_HEIGHT - 1)
        jumon_to_summon = self.state_variables["jumon_to_summon"]
        # Build the summon_check_variables
        summon_check_state_variables = {
            "jumon_to_summon": self.state_variables["jumon_to_summon"],
            "summon_position": Position(x_position, y_position)}
        """"
        Invoke the special ability function of the current jumon
        and use its return for the state change of the fsm
        """
        state_change = jumon_to_summon.special_ability(self,
                (self.fsm.summon_check_state, summon_check_state_variables))
        return state_change


class SummonCheckState(State):
    """
    In this state its checked whether the jumon has to be replaced, the
    jummon was summond on a free position and the turn is over or
    a battle is triggererd
    """
    def __init__(self, fsm):
        super().__init__("summon_check_state", fsm)

    def run(self, event):
        """
        Check if the summon position is free, which makes the summonation
        complete and ends the turn, the summon position is blocked which
        makes the state machiene jump back to the SummonState or the
        summon position is blocked by a hostile jumon which leads to
        a jump to the OneTileBattleState.
        The ability script of the active jumon is only invoked on a succesfull
        summoning. In other case there is a following state in which
        the ability script will be triggered.
        """
        # Get the jumon to summon and where to summon it
        jumon = self.state_variables["jumon_to_summon"]
        summon_position = self.state_variables["summon_position"]
        if self.fsm.arena.get_unit_at(summon_position) is None:
            """
            If the ArenaTile is free the jumon can be placed, its ability
            script triggers and the turn ends
            """
            # Let the current player summon this jumon
            jumon.owned_by.\
                handle_summoning(jumon)
            # Propagate a summon inter turn event
            summon_itevent = Event(MESSAGE,
                players=self.fsm.player_chain.get_players(),
                tokens=['SUMMON_ITEVENT', self.fsm.player_chain.get_current_player().name,
                jumon.id, jumon.position])
            propagate_message(summon_itevent)

            if self.fsm.arena.get_tile_at(summon_position).is_wasted():
                """
                If the summoned position is a wasted land kill the jumon
                instead of place it on the tile
                """
                propagating_handle_jumon_death(jumon,
                    self.fsm.player_chain.get_players())
            else:
                """ Place the jumon at the arena """
                self.fsm.arena.place_unit_at(jumon, summon_position)
            """
            Invoke the jumon special ability with the same state variables
            as no new state variables occured. This way enter the battlefield
            effects can be implemented.
            """
            state_change = jumon.special_ability(self,
                    (self.fsm.turn_end_state, self.state_variables))
            return state_change
        elif issubclass(type(self.fsm.arena.get_unit_at(summon_position)),
                Akuga.AkugaGameModi.Meeple.Artefact):
            """
            If the jumon is summoned on an artefact place it on this tile
            and jump to the equip artefact to jumon state
            """
            # Let the current player summon this jumon
            jumon.owned_by.\
                handle_summoning(jumon)
            # Propagate a summon inter turn event
            summon_itevent = Event(MESSAGE,
                players=self.fsm.player_chain.get_players(),
                tokens=['SUMMON_ITEVENT', self.fsm.player_chain.get_current_player().name,
                jumon.id, jumon.position])
            propagate_message(summon_itevent)
            # Get the artefact at this point
            artefact = self.fsm.arena.get_unit_at(summon_position)
            # Place the jumon at the arena
            self.fsm.arena.place_unit_at(jumon, summon_position)
            """
            Create the state variables with the last state as None
            as there is no last position and do the state change
            """
            return (self.fsm.equip_artefact_to_jumon_state, {
                "jumon": jumon,
                "artefact": artefact,
                "last_position": None})

        elif jumon.owned_by.owns_tile(
                self.fsm.arena, summon_position):
            """
            If the jumon at this tile is owned  by the current player
            the jumon has to be replaced, so jump back to the summon state
            """
            summon_state_variables = {
                "jumon_to_summon": self.state_variables["jumon_to_summon"]}
            return (self.fsm.summon_state, summon_state_variables)
        else:
            """
            If the tile is not empty and the jumon is not owned by
            the current player it has to be a hostile jumon so jump
            to the OneTileBattleState with the position as well as
            both the current and the hostile jumon attached as
            state variables.
            If the jumon to summon is going to be placed on the arena or not
            the player summoned it, so handle_summoning must be invoked
            """
            jumon.owned_by.\
                handle_summoning(jumon)
            one_tile_battle_state_variables = {
                "battle_position": summon_position,
                "attacking_jumon": jumon,
                "defending_jumon": self.fsm.arena.get_unit_at(summon_position)}
            return (self.fsm.one_tile_battle_begin_state,
                    one_tile_battle_state_variables)


class ChangePlayerState(State):
    """
    This represents the moment between the turns.
    """
    def __init__(self, fsm):
        super().__init__("change_player_state", fsm)
        self.remi_counter = 0

    def check_for_victory(self):
        """
        In the last man standing mode there are two cases in which
        a player has won:
        1. Per is the only not neutral player left
        2. Per has won using an alternative win condition
        """
        players = self.fsm.player_chain.get_players()
        not_neutral_players = list(
            filter(lambda x: type(x) is not NeutralPlayer, players))
        # Only one not neutral player is left per has won
        if len(not_neutral_players) == 1:
            return not_neutral_players[0]
        # The first player with the has_won flag set is the victor
        victors = list(filter(lambda x: x.has_won(), players))
        if len(victors) > 1:
            return victors[0]
        return None

    def check_for_drawn(self):
        """
        In the last man standing game mode the game is drawn if there
        is no non neutral players left, or there are only two jumons left
        and the match takes to long
        """
        pc = self.fsm.player_chain
        # If only two jumons are left in the game count the turns of the
        # match. The match is drawn (remi) if the number of turns with only
        # two jumons exceed the MAX_REMI_COUNTER variable.
        jumons_left_in_game = 0
        for player in pc.get_players():
            jumons_left_in_game += len(player.jumons_to_summon)
            jumons_left_in_game += len(player.summoned_jumons)
        if jumons_left_in_game == 2:
            self.remi_counter += 1
            print("REMI COUNTER INCREMENT TO:")
            print(self.remi_counter)
            if self.remi_counter > GlobalDefinitions.MAX_REMI_COUNTER:
                return True
        # A match is drawn if there is no player
        # or only the neutral player left
        return pc.len == 0 or (pc.len == 1 and type(pc.startNode.
            get_player()) is NeutralPlayer)

    def run(self, event):
        """
        update the current player, check for victors or if the match
        is drawn and handle the end of a match with throwing the right
        events.
        update the inner respresentation of the player
        aka check if per is dead or not.
        """
        # Dont change the phase of the player if per is in the pick phase
        # Only the pick state can set a player from the pick phase in
        # an other phase, but once the pick phase is left it cant be entered
        # again
        if self.fsm.player_chain.get_current_player().in_pick_phase() is False:
            self.fsm.player_chain.get_current_player().update_player()
        # Remove dead players from the player chain
        self.fsm.player_chain.update()
        # Check if the match is drawn
        if self.check_for_drawn():
            """
            After this event has been handeld the state machiene should
            not be updated anymore
            """
            drawn_event = Event(MATCH_IS_DRAWN)
            self.fsm.queue.put(drawn_event)
        # Check if a player has won
        victor = self.check_for_victory()
        if victor is not None:
            """
            After this event has been handeld the state machiene should
            not be updated anymore
            """
            won_event = Event(PLAYER_HAS_WON, victor=victor)
            self.fsm.queue.put(won_event)
        """
        If no one has won and its not drawn change the player and
        jump to the idle state again so its the next players turn
        """
        self.fsm.player_chain.next_players_turn()
        """
        Throw an turn ends event to refresh the gamestate for the clients
        and propagate the changes on the gamestate.
        """
        event = Event(TURN_ENDS)
        self.fsm.queue.put(event)
        return (self.fsm.turn_begin_state, {})


class CheckMoveState(State):
    """
    Checks wheter a draw of a jumon is legal or not
    """
    def __init__(self, fsm):
        super().__init__("check_move_state", fsm)

    def run(self, event):
        """
        Get the shortest path from the current position to the target
        position. Do the move if its legal, or jump back to the idle
        state if its not. Jump to the two tile battle state or the
        equip artefact state if the target position is occupied by an
        hostile jumon or an artefact
        """
        # Get the jumon, its current position and the target position
        jumon = self.state_variables["jumon_to_move"]
        current_position = self.state_variables["current_position"]
        target_position = self.state_variables["target_position"]
        print("State Variables")
        print(jumon.name)
        print(str(current_position))
        print(str(target_position))
        """
        Get the shortes distance between the current position and the
        target position. Do the move only if the path is not none (aka a
        path is found) and the pathlength is less then or equal to the
        movements of the selected jumon. This way the jumons actually
        move and can be blocked by other meeples.
        """
        move_path = find_path(current_position, target_position,
            self.fsm.arena)
        if move_path is None or len(move_path) == 0\
                or len(move_path) - 1 > jumon.get_total_movement():
            """
            If the target move is invalid in length just jump back to the
            idle state.
            """
            return (self.fsm.wait_for_user_state, {
                "enforced_jumon": None,
                "enforced_event": None})
        if self.fsm.arena.get_unit_at(target_position) is None:
            """
            If the tile at target position is free just do the move
            and end the turn by jumping to the ChangePlayerState
            """
            if self.fsm.arena.get_tile_at(target_position).is_wasted():
                """
                If the target position is a wasted arena tile kill the
                jumon
                """
                self.fsm.arena.place_unit_at(None, current_position)
                propagating_handle_jumon_death(jumon, self.fsm.player_chain.get_players())
            else:
                """ Place the jumon on the arena tile """
                print('Moving jumon: ' + jumon.name)
                print('From: ' + str(current_position))
                print('To: ' + str(target_position))

                self.fsm.arena.place_unit_at(None, current_position)
                self.fsm.arena.place_unit_at(jumon, target_position)
                # Propagate an movement inter turn event
                movement_itevent = Event(MESSAGE,
                    players=self.fsm.player_chain.get_players(),
                    tokens=['MOVEMENT_ITEVENT',
                        self.fsm.player_chain.get_current_player().name,
                        jumon.id, current_position, target_position])
                propagate_message(movement_itevent)
            return (self.fsm.turn_end_state, {})
        elif jumon.owned_by.\
                owns_tile(self.fsm.arena, target_position):
            """
            If the target position is owned by a jumon of the current player
            the move is illegal and the a new move has to be defined,
            so jump back to the idle state
            """
            return (self.fsm.wait_for_user_state, {
                "enforced_jumon": None,
                "enforced_event": None})
        elif issubclass(type(self.fsm.arena.get_unit_at(target_position)),
                Akuga.AkugaGameModi.Meeple.Artefact):
            """
            If the target position is occupied by an artefact jump to the
            equip artefact to jumon state
            """
            # Get the artefact at the target position
            artefact = self.fsm.arena.get_unit_at(target_position)
            # Move the jumon
            self.fsm.arena.place_unit_at(None, current_position)
            self.fsm.arena.place_unit_at(jumon, target_position)
            # Jump to the equip artefact to jumon state
            return (self.fsm.equip_artefact_to_jumon_state, {
                "jumon": jumon,
                "artefact": artefact,
                "last_position": current_position})  # Its right think about it
        else:
            """
            If the target position is not empty and the jumon on target
            position is not owned by the current player it has to be
            a hostile jumon, so a TwoTileBattle is triggered
            """
            two_tile_battle_state_variable = {
                "attacking_jumon": jumon,
                "defending_jumon": self.fsm.arena.get_unit_at(target_position),
                "attack_position": current_position,
                "defense_position": target_position}
            return (self.fsm.two_tile_battle_begin_state,
                    two_tile_battle_state_variable)


class CheckDisplacementState(State):
    """
    Checks wheter a draw of a jumon is legal or not
    """
    def __init__(self, fsm):
        super().__init__("check_displacement_state", fsm)

    def run(self, event):
        """
        Displace the selected jumon to the target position regardless of
        its movement. Do nothing, aka jump to the ChangePlayerState if the
        target position is occupied by a jumon of the same team.
        Jump to the two tile battle state or the
        equip artefact state if the target position is occupied by an
        hostile jumon or an artefact
        """
        # Get the jumon, its current position and the target position
        jumon = self.state_variables["jumon_to_displace"]
        current_position = self.state_variables["current_position"]
        target_position = self.state_variables["target_position"]

        # Displacing a jumon outside the arena is allowed, it kills the
        # jumon instantly
        if target_position.x < 0 or\
                target_position.x > self.fsm.arena.board_width - 1:
            # Propagate a displacement inter turn event
            displacement_itevent = Event(MESSAGE,
                players=self.fsm.player_chain.get_players(),
                tokens=['DISPLACEMENT_ITEVENT', jumon.id,
                    current_position, target_position])
            propagate_message(displacement_itevent)
            self.fsm.arena.place_unit_at(None, current_position)
            propagating_handle_jumon_death(jumon, self.fsm.player_chain.get_players())

            return (self.fsm.turn_end_state, {})

        if target_position.y < 0 or\
                target_position.y > self.fsm.arena.board_height - 1:
            # Propagate a displacement inter turn event
            displacement_itevent = Event(MESSAGE,
                players=self.fsm.player_chain.get_players(),
                tokens=['DISPLACEMENT_ITEVENT', jumon.id,
                    current_position, target_position])
            propagate_message(displacement_itevent)
            self.fsm.arena.place_unit_at(None, current_position)
            propagating_handle_jumon_death(jumon, self.fsm.player_chain.get_players())

            return (self.fsm.turn_end_state, {})

        if self.fsm.arena.get_unit_at(target_position) is None:
            """
            If the tile at target position is free just do the displacement
            and end the turn by jumping to the ChangePlayerState
            """
            # Propagate a displacement inter turn event
            displacement_itevent = Event(MESSAGE,
                players=self.fsm.player_chain.get_players(),
                tokens=['DISPLACEMENT_ITEVENT', jumon.id,
                    current_position, target_position])
            propagate_message(displacement_itevent)

            if self.fsm.arena.get_tile_at(target_position).is_wasted():
                """
                If the target position is a wasted arena tile kill the
                jumon
                """
                self.fsm.arena.place_unit_at(None, current_position)
                propagating_handle_jumon_death(jumon, self.fsm.player_chain.get_players())

            else:
                """ Place the jumon on the arena tile """
                self.fsm.arena.place_unit_at(None, current_position)
                self.fsm.arena.place_unit_at(jumon, target_position)
            return (self.fsm.turn_end_state, {})
        elif jumon.owned_by.\
                owns_tile(self.fsm.arena, target_position):
            """
            If the target position is owned by a jumon of the same team
            the displacement is illegal and cant be done,
            so jump to the TurnEndState
            """
            return (self.fsm.turn_end_state, {})
        elif issubclass(type(self.fsm.arena.get_unit_at(target_position)),
                Akuga.AkugaGameModi.Meeple.Artefact):
            """
            If the target position is occupied by an artefact jump to the
            equip artefact to jumon state
            """
            # Get the artefact at the target position
            artefact = self.fsm.arena.get_unit_at(target_position)
            # Move the jumon
            self.fsm.arena.place_unit_at(None, current_position)
            self.fsm.arena.place_unit_at(jumon, target_position)
            # Propagate a displacement inter turn event
            displacement_itevent = Event(MESSAGE,
                players=self.fsm.player_chain.get_players(),
                tokens=['DISPLACEMENT_ITEVENT', jumon.id,
                    current_position, target_position])
            propagate_message(displacement_itevent)
            # Jump to the equip artefact to jumon state
            return (self.fsm.equip_artefact_to_jumon_state, {
                "jumon": jumon,
                "artefact": artefact,
                "last_position": current_position})  # Its right think about it
        else:
            """
            If the target position is not empty and the jumon on target
            position is not owned by the current player it has to be
            a hostile jumon, so a OneTileBattle is triggered
            """
            one_tile_battle_state_variable = {
                "battle_position": target_position,
                "attacking_jumon": jumon,
                "defending_jumon": self.fsm.arena.get_unit_at(target_position)}
            return (self.fsm.two_tile_battle_begin_state,
                    one_tile_battle_state_variable)


class CheckSpecialMoveState(State):
    """
    Check if a special move is legal or not and invoke the special move
    function of the ability script of the current jumon.
    """
    def __init__(self, fsm):
        super().__init__("check_special_move_state", fsm)

    def run(self, event):
        """
        Use the 'is_special_move_legal' function of the current jumon
        to check if the move is legal or not. Invoke the special_move
        function of the current jumon if the move is legal.
        Go back to the idle state if its not
        """
        # Get the jumon, its current position and the target position
        jumon = self.state_variables["jumon_to_move"]
        current_position = self.state_variables["current_position"]
        target_position = self.state_variables["target_position"]
        if jumon.is_special_move_legal(self.fsm.arena,
                current_position, target_position):
            """
            If the special move is legal invoke the special move function
            of the current jumon
            """
            # Propagate a special move inter turn event
            specialmove_itevent = Event(MESSAGE,
                players=self.fsm.player_chain.get_players(),
                tokens=['SPECIAL_MOVE_ITEVENT', jumon.id,
                    current_position, target_position])
            propagate_message(specialmove_itevent)
            state_change = jumon.do_special_move(self.fsm, current_position,
                    target_position)
            return state_change
        else:
            """
            If there is no special ability script at all the special
            move is illegal by default, so just jump to the wait_for_user_state
            """
            return (self.fsm.wait_for_user_state, {
                "enforced_jumon": None,
                "enforced_event": None})
        # Is never hit but nonetheless
        return None


class OneTileBattleBeginState(State):
    """
    The start of a battle on one tile
    This state does nothing on its own, its just an entry point
    for special ability scripts of the fighting jumon
    """
    def __init__(self, fsm):
        super().__init__("one_tile_battle_begin_state", fsm)

    def run(self, event):
        """
        Invoke the ability scripts of the fighting jumons and jump
        to the OneTileBattleFlipState
        """
        attacking_jumon = self.state_variables["attacking_jumon"]
        defending_jumon = self.state_variables["defending_jumon"]
        state_change = attacking_jumon.special_ability(self,
                (self.fsm.one_tile_battle_flip_state,
                self.state_variables))
        state_change = defending_jumon.special_ability(self, state_change)
        # Do the state change
        return state_change


class OneTileBattleFlipState(State):
    """
    In this state the arena tile at battle position is turned around
    and attached to the state informations. Then the state machiene
    immediatly jumps to the OneTileBattleBoniEvaluationStep
    """
    def __init__(self, fsm):
        super().__init__("one_tile_battle_flip_state", fsm)

    def run(self, event):
        """
        Get the arena tile at the battle position and add it to the state
        variables. Then jump to the OneTileBattleBoniEvaluationState
        """
        attacking_jumon = self.state_variables["attacking_jumon"]
        defending_jumon = self.state_variables["defending_jumon"]
        battle_position = self.state_variables["battle_position"]
        # Get the battle arena tile
        battle_tile = self.fsm.arena.get_tile_at(battle_position)
        # Now jump to the OneTileBattleBoniEvaluationState
        one_tile_battle_boni_evaluation_state_variables = {
            "attacking_jumon": attacking_jumon,
            "defending_jumon": defending_jumon,
            "battle_position": battle_position}
        """
        After the arena tile has flipped invoke its ability script
        """
        state_change = battle_tile.one_tile_special_ability(self,
            attacking_jumon, defending_jumon,
            (self.fsm.one_tile_battle_boni_evaluation_state,
            one_tile_battle_boni_evaluation_state_variables))
        return state_change


class OneTileBattleBoniEvaluationState(State):
    """
    In this State the bonus of the arena is evaluated and a bonus value
    for both jumons are added to the state variables. Then the state
    machiene jumps to the OneTileBattleFightState
    """
    def __init__(self, fsm):
        super().__init__("one_tile_battle_boni_evaluation_state", fsm)

    def run(self, event):
        """
        Add the boni of the arena tile to the state variables and jump
        to the OneTileBattleFightState
        """
        attacking_jumon = self.state_variables["attacking_jumon"]
        defending_jumon = self.state_variables["defending_jumon"]
        battle_position = self.state_variables["battle_position"]
        battle_arena_tile = self.fsm.arena.get_tile_at(battle_position)
        attacking_jumon_bonus = battle_arena_tile.\
            get_total_attack_bonus(attacking_jumon)
        defending_jumon_bonus = battle_arena_tile.\
            get_total_defense_bonus(defending_jumon)
        # Create the state_variables
        one_tile_battle_figh_state_variables = {
            "attacking_jumon": attacking_jumon,
            "defending_jumon": defending_jumon,
            "battle_position": battle_position,
            "attacking_jumon_bonus": attacking_jumon_bonus,
            "defending_jumon_bonus": defending_jumon_bonus}
        """
        After the bonus values are evaluated invoke the ability scripts
        """
        # Propagate a bonus inter turn event
        attackbonus_itevent = Event(MESSAGE,
            players=self.fsm.player_chain.get_players(),
            tokens=['ATTACKBONUS_ITEVENT',
                attacking_jumon.id,
                attacking_jumon.position,
                attacking_jumon_bonus])
        defensebonus_itevent = Event(MESSAGE,
            players=self.fsm.player_chain.get_players(),
            tokens=['DEFENSEBONUS_ITEVENT',
                defending_jumon.id,
                defending_jumon.position,
                defending_jumon_bonus])
        propagate_message(attackbonus_itevent)
        propagate_message(defensebonus_itevent)
        state_change = attacking_jumon.special_ability(self,
                (self.fsm.one_tile_battle_fight_state,
                one_tile_battle_figh_state_variables))
        state_change = defending_jumon.special_ability(self,
                (state_change[0], state_change[1]))
        return state_change


class OneTileBattleFightState(State):
    """
    In this state both jumons fight the victor and the looser are determined
    Then the state machiene jumps to the OneTileBattleAfterMathState
    """
    def __init__(self, fsm):
        super().__init__("one_tile_battle_fight_state", fsm)

    def run(self, event):
        """
        Fighting is pretty simple, the jumon with less power looses.
        If both jumons have the same power both jumon looses.
        Than the state machiene jumps to OneTileBattleAftermathState
        """
        attacking_jumon = self.state_variables["attacking_jumon"]
        defending_jumon = self.state_variables["defending_jumon"]
        battle_position = self.state_variables["battle_position"]
        attacking_jumon_bonus = self.state_variables["attacking_jumon_bonus"]
        defending_jumon_bonus = self.state_variables["defending_jumon_bonus"]
        # Propagate a one tile battle fight inter turn event
        onetilefight_itevent = Event(MESSAGE,
            players=self.fsm.player_chain.get_players(),
            tokens=['ONETILEFIGHT',
                attacking_jumon.id,
                defending_jumon.id,
                attacking_jumon.position,
                defending_jumon.position])
        propagate_message(onetilefight_itevent)
        # If no one wins victor and looser are none
        victor, looser = jumon_fight(attacking_jumon, attacking_jumon_bonus,
                                     defending_jumon, defending_jumon_bonus)
        """
        The summoned jumon and the defending_jumon has to be in the variables
        as well to destroy both if victor and looser are None.
        Jump to the one_tile_battle_aftermath_state
        """
        one_tile_battle_aftermath_state_variables = {
            "attacking_jumon": attacking_jumon,
            "defending_jumon": defending_jumon,
            "battle_position": battle_position,
            "attacking_jumon_bonus": attacking_jumon_bonus,
            "defending_jumon_bonus": defending_jumon_bonus,
            "victor": victor,
            "looser": looser}
        """
        run the ability scripts after victor and looser are determined,
        this way ability scripts can trigger if the bakugan wins or looses
        """
        state_change = attacking_jumon.special_ability(self,
                (self.fsm.one_tile_battle_aftermath_state,
                one_tile_battle_aftermath_state_variables))
        state_change = defending_jumon.special_ability(self, state_change)
        return state_change


class OneTileBattleAftermathState(State):
    """
    In this state the jumon which loosed the fight is removed from the
    arena and the summoned jumon list of the player.
    The jumon which won the fight will be placed on the arena tile
    """
    def __init__(self, fsm):
        super().__init__("one_tile_battle_aftermath_state", fsm)

    def run(self, event):
        """
        Kill the looser jumon, place the victor jumon,
        and swap the artefact from the victor to the looser.
        """
        attacking_jumon = self.state_variables["attacking_jumon"]
        defending_jumon = self.state_variables["defending_jumon"]
        victor = self.state_variables["victor"]
        looser = self.state_variables["looser"]
        battle_position = self.state_variables["battle_position"]
        # attacking_jumon_bonus = self.state_variables["attacking_jumon_bonus"]
        # defending_jumon_bonus = self.state_variables["defending_jumon_bonus"]

        if victor is None and looser is None:
            """
            If no victor and no looser is assigned both jumons had the same
            power level and both have to be destroyed
            If the attacker has an equipment attached to it detach it
            and place it on the arena tile
            """
            if attacking_jumon.equipment is not None:
                artefact = attacking_jumon.equipment
                artefact.detach_from(attacking_jumon)
                self.fsm.arena.place_unit_at(artefact, battle_position)
            """
            If the defender has an equipment attached to it detach it
            and place it on the arena tile. Cause this is handeld
            after the attacker the equipment of the defender overwrites
            the equipment of the attacker. This way the equipment of
            the attacker vanishes.
            """
            if defending_jumon.equipment is not None:
                artefact = defending_jumon.equipment
                artefact.detach_from(defending_jumon)
                self.fsm.arena.place_unit_at(artefact, battle_position)

            # kill the jumons
            propagating_handle_jumon_death(attacking_jumon, self.fsm.player_chain.get_players())
            propagating_handle_jumon_death(defending_jumon, self.fsm.player_chain.get_players())

            # Remove the occupying unit from the arena tile
            self.fsm.arena.place_unit_at(None, battle_position)

        else:
            if looser.equipment is not None:
                """
                If the looser had an artifact attached to it attach it to the
                winner instead
                """
                artifact = looser.equipment
                looser.equipment.detach_from(looser)
                artifact.attach_to(victor)
            # Now kill the looser
            propagating_handle_jumon_death(looser, self.fsm.player_chain.get_players())

            # Place the victor on the arena tile
            self.fsm.arena.place_unit_at(victor, battle_position)

        # Now do the state_change (mostly jump to turn_end_state)
        state_change = attacking_jumon.special_ability(self,
                (self.fsm.turn_end_state,
                self.state_variables))
        state_change = defending_jumon.special_ability(self, state_change)
        return state_change


class TwoTileBattleBeginState(State):
    """
    The start of a battle on two tiles
    This state does nothing on its own, its just an entry point
    for special ability scripts of the fighting jumon
    """
    def __init__(self, fsm):
        super().__init__("two_tile_battle_begin_state", fsm)

    def run(self, event):
        """
        Invoke the ability scripts of the fighting jumons and jump
        to the TwoTileBattleFlipState
        """
        attacking_jumon = self.state_variables["attacking_jumon"]
        defending_jumon = self.state_variables["defending_jumon"]
        state_change = attacking_jumon.special_ability(self,
                (self.fsm.two_tile_battle_flip_state,
                self.state_variables))
        state_change = defending_jumon.special_ability(self, state_change)
        return state_change


class TwoTileBattleFlipState(State):
    """
    In this state the arena tiles at the battle positions are turned around
    and attached to the state informations. Then the state machiene
    immediatly jumps to the TwoTileBattleBoniEvaluationStep
    """
    def __init__(self, fsm):
        super().__init__("two_tile_battle_flip_state", fsm)

    def run(self, event):
        """
        Get the arena tiles at the battle positions and add them to the state
        variables. Then jump to the TwoTileBattleBoniEvaluationState
        """
        attacking_jumon = self.state_variables["attacking_jumon"]
        defending_jumon = self.state_variables["defending_jumon"]
        attack_position = self.state_variables["attack_position"]
        defense_position = self.state_variables["defense_position"]
        # Get the battle tiles
        attack_tile = self.fsm.arena.get_tile_at(attack_position)
        defense_tile = self.fsm.arena.get_tile_at(defense_position)
        # Now jump to the TwoTileBattleBoniEvaluationState
        two_tile_battle_boni_evaluation_state_variables = {
            "attacking_jumon": attacking_jumon,
            "defending_jumon": defending_jumon,
            "attack_position": attack_position,
            "defense_position": defense_position}
        """
        After the arena tiles has flipped invoke their ability scripts
        The attack tile triggers first! The state_change returned by
        the attack_tile has to be the input of the defense tile so
        both tiles can alter the state change and the state variables.
        """
        state_change = attack_tile.two_tile_special_ability(self,
            attacking_jumon, (self.fsm.two_tile_battle_boni_evaluation_state,
            two_tile_battle_boni_evaluation_state_variables))
        state_change = defense_tile.two_tile_special_ability(self,
            defending_jumon, state_change)
        # Do the state change
        return state_change


class TwoTileBattleBoniEvaluationState(State):
    """
    In this State the bonus of the arena is evaluated and a bonus value
    for both jumons are added to the state variables. Then the state
    machiene jumps to the TwoTileBattleFightState
    """
    def __init__(self, fsm):
        super().__init__("two_tile_battle_boni_evaluation_state", fsm)

    def run(self, event):
        """
        Add the boni of the arena tiles to the state variables and jump
        to the TwoTileBattleFightState
        """
        attacking_jumon = self.state_variables["attacking_jumon"]
        defending_jumon = self.state_variables["defending_jumon"]
        attack_position = self.state_variables["attack_position"]
        defense_position = self.state_variables["defense_position"]
        attack_tile = self.fsm.arena.get_tile_at(attack_position)
        defense_tile = self.fsm.arena.get_tile_at(defense_position)

        # Get the bonus of the attack or defense tile
        attacking_jumon_bonus = attack_tile.\
            get_total_attack_bonus(attacking_jumon)
        defending_jumon_bonus = defense_tile.\
            get_total_defense_bonus(defending_jumon)
        # Propagate a bonus inter turn event
        attackbonus_itevent = Event(MESSAGE,
            players=self.fsm.player_chain.get_players(),
            tokens=['ATTACKBONUS_ITEVENT',
                attacking_jumon.id,
                attacking_jumon.position,
                attacking_jumon_bonus])
        defensebonus_itevent = Event(MESSAGE,
            players=self.fsm.player_chain.get_players(),
            tokens=['DEFENSEBONUS_ITEVENT',
                defending_jumon.id,
                defending_jumon.position,
                defending_jumon_bonus])
        propagate_message(attackbonus_itevent)
        propagate_message(defensebonus_itevent)
        # Now jump to the two_tile_battle_fight_state
        two_tile_battle_figh_state_variables = {
            "attacking_jumon": attacking_jumon,
            "defending_jumon": defending_jumon,
            "attack_position": attack_position,
            "defense_position": defense_position,
            "attacking_jumon_bonus": attacking_jumon_bonus,
            "defending_jumon_bonus": defending_jumon_bonus}
        """
        After the bonus values are evaluated invoke the ability scripts
        """
        state_change = attacking_jumon.special_ability(self,
                (self.fsm.two_tile_battle_fight_state,
                two_tile_battle_figh_state_variables))
        state_change = defending_jumon.special_ability(self, state_change)
        # Do the state change
        return state_change


class TwoTileBattleFightState(State):
    """
    In this state both jumons fight the victor and the looser are determined
    Then the state machiene jumps to the TwoTileBattleAfterMathState
    """
    def __init__(self, fsm):
        super().__init__("two_tile_battle_fight_state", fsm)

    def run(self, event):
        """
        Fighting is pretty simple, the jumon with less power looses.
        If both jumons have the same power both jumon looses.
        Than the state machiene jumps to TwoTileBattleAftermathState
        """
        attacking_jumon = self.state_variables["attacking_jumon"]
        defending_jumon = self.state_variables["defending_jumon"]
        attack_position = self.state_variables["attack_position"]
        defense_position = self.state_variables["defense_position"]
        attacking_jumon_bonus = self.state_variables["attacking_jumon_bonus"]
        defending_jumon_bonus = self.state_variables["defending_jumon_bonus"]
        # Propagate a one tile battle fight inter turn event
        onetilefight_itevent = Event(MESSAGE,
            players=self.fsm.player_chain.get_players(),
            tokens=['ONETILEFIGHT',
                attacking_jumon.id,
                defending_jumon.id,
                attacking_jumon.position,
                defending_jumon.position])
        propagate_message(onetilefight_itevent)
        # If no one wins victor and looser are none
        victor, looser = jumon_fight(attacking_jumon, attacking_jumon_bonus,
                                     defending_jumon, defending_jumon_bonus)
        """
        The summoned jumon and the defending_jumon has to be in the variables
        as well to destroy both if victor and looser are None.
        """
        two_tile_battle_aftermath_state_variables = {
            "attacking_jumon": attacking_jumon,
            "defending_jumon": defending_jumon,
            "attack_position": attack_position,
            "defense_position": defense_position,
            "attacking_jumon_bonus": attacking_jumon_bonus,
            "defending_jumon_bonus": defending_jumon_bonus,
            "victor": victor,
            "looser": looser}
        """
        run the ability scripts after victor and looser are determined,
        this way ability scripts can trigger if the bakugan wins or looses
        """
        state_change = attacking_jumon.special_ability(self,
                (self.fsm.two_tile_battle_aftermath_state,
                two_tile_battle_aftermath_state_variables))
        state_change = defending_jumon.special_ability(self, state_change)
        # Do the state change
        return state_change


class TwoTileBattleAftermathState(State):
    """
    In this state the jumon which loosed the fight is removed from the
    arena and the summoned jumon list of the player.
    The jumon which won the fight will be placed on the arena tile
    """
    def __init__(self, fsm):
        super().__init__("two_tile_battle_aftermath_state", fsm)

    def run(self, event):
        """
        Kill the looser, place the victor and swap the artefact from
        the victor to the looser.
        """
        attacking_jumon = self.state_variables["attacking_jumon"]
        defending_jumon = self.state_variables["defending_jumon"]
        attack_position = self.state_variables["attack_position"]
        defense_position = self.state_variables["defense_position"]
        victor = self.state_variables["victor"]
        looser = self.state_variables["looser"]
        if victor is None and looser is None:
            """
            If no victor and no looser is assigned both jumons had the same
            power level and both have to be destroyed
            """
            # kill both jumons
            propagating_handle_jumon_death(attacking_jumon, self.fsm.player_chain.get_players())
            propagating_handle_jumon_death(defending_jumon, self.fsm.player_chain.get_players())

            # Remove both units from the arena tile
            self.fsm.arena.place_unit_at(None, attack_position)
            self.fsm.arena.place_unit_at(None, defense_position)
            if attacking_jumon.equipment is not None:
                """
                If the attacking_jumon had an artefact equiped drop it
                """
                artefact = attacking_jumon.equipment
                artefact.detach_from(attacking_jumon)
                self.fsm.arena.place_unit_at(artefact, attack_position)
            if defending_jumon.equipment is not None:
                """
                If the defending_jumon had an artefact equiped drop it
                """
                artefact = defending_jumon.equipment
                artefact.detach_from(defending_jumon)
                self.fsm.arena.place_unit_at(artefact, defense_position)

        elif victor is attacking_jumon:
            """
            If the jumon to move has won move it to the defense tile
            """
            # Just kill the looser
            propagating_handle_jumon_death(defending_jumon, self.fsm.player_chain.get_players())

            # Move the victor from the attack tile to the defense tile
            self.fsm.arena.place_unit_at(None, attack_position)
            self.fsm.arena.place_unit_at(victor, defense_position)
            if looser.equipment is not None:
                """
                If the defender had an equipment it has to be detached
                from it and attached to the attacker
                """
                looser_artefact = looser.equipment
                looser_artefact.detach_from(looser)
                if victor.equipment is not None:
                    """
                    If the victor jumon has an equipment on its own it dropps
                    its artefact on the attack tile and attaches the
                    artefact of the defender jumon
                    """
                    victor_artefact = victor.equipment
                    victor_artefact.detach_from(victor)
                    self.fsm.arena.place_unit_at(victor_artefact,
                        attack_position)
                # Attach the artefact of the defender to the attacker
                looser_artefact.attach_to(victor)
        elif victor is defending_jumon:
            """
            If the defending_jumon has won remove the attacking jumon
            """
            # Just kill the looser
            propagating_handle_jumon_death(attacking_jumon, self.fsm.player_chain.get_players())

            self.fsm.arena.place_unit_at(None, attack_position)
            if attacking_jumon.equipment is not None:
                """
                If the attacking jumon had an equipment it drops it on the
                attack tile
                """
                # Detach the artefact from the jumon
                attack_artefact = attacking_jumon.equipment
                attack_artefact.detach_from(attacking_jumon)
                # Place it on the attack tile
                self.fsm.arena.place_unit_at(attack_artefact, attack_position)
        # Now the turn ends so do the change
        state_change = attacking_jumon.special_ability(self,
                (self.fsm.turn_end_state,
                self.state_variables))
        state_change = defending_jumon.special_ability(self, state_change)
        return state_change


class EquipArtefactToJumonState(State):
    """
    Equips an artefact to a jumon
    """
    def __init__(self, fsm):
        super().__init__("equip_artefact_to_jumon_state", fsm)

    def run(self, event):
        """
        Attaches an equipment to a jumon
        """
        jumon = self.state_variables["jumon"]
        artefact = self.state_variables["artefact"]
        last_position = self.state_variables["last_position"]

        # Propagate a equip artefact event
        equip_itevent = Event(MESSAGE,
            players=self.fsm.player_chain.get_players(),
            tokens=['EQUIP_ITEVENT', jumon.id, artefact.id])
        propagate_message(equip_itevent)
        if jumon.equipment is None:
            """
            If the jumon has no equipment yet just attach it
            """
            artefact.attach_to(jumon)
        else:
            """
            If the jumon has an equipment attached it has to be detached
            and placed at the old position. In the very special case
            a jumon is summoned with an equipment attached to it
            aka last_position is None discard it
            """
            # Get the artefact to detach and detach it from the jumon
            detached_artefact = jumon.equipment
            detached_artefact.detach_from(jumon)
            # Attach the current artefact to the jumon
            artefact.attach_to(jumon)
            """
            Just place the detached artefact on the arena again if the
            last position is not None like it would be if the jumon
            was just summoned. This presupposes there is a jumon
            which is summoned with an artefact attached to it
            """
            if last_position is not None:
                self.fsm.arena.place_unit_at(detached_artefact, last_position)
        # Invoke the special ability of the jumon and do the state change
        state_change = (self.fsm.turn_end_state, {})
        state_change = jumon.special_ability(self, state_change)
        return state_change


class TimeoutState(State):
    """
    A player can timeout on making pers decisions.
    A player dies if per times out the third time
    """

    def __init__(self, fsm):
        super().__init__("timeout_state", fsm)

    def run(self, event):
        """
        Increment the timeout counter of the player.
        Kill the player if per has timed out to often
        """
        # Propagate a timeout inter turn event
        timeout_itevent = Event(MESSAGE,
            players=self.fsm.player_chain.get_players(),
            tokens=['TIMEOUT_ITEVENT',
                self.fsm.player_chain.get_current_player().name,
                self.fsm.player_chain.get_current_player().timeout_counter])
        propagate_message(timeout_itevent)
        self.fsm.player_chain.get_current_player().increment_timeout_counter()
        if self.fsm.player_chain.get_current_player().\
                get_timeout_counter() > GlobalDefinitions.MAX_TIMEOUTS:
            self.fsm.player_chain.get_current_player().kill()
        return (self.fsm.turn_end_state, {})
