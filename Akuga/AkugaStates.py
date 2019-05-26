import random
import pygame
import Akuga.global_definitions as global_definitions
import Akuga.Meeple
from Akuga.PathFinder import FindPath
from Akuga.Position import Position
from Akuga.Player import NeutralPlayer
from Akuga.StateMachieneState import StateMachieneState as State
from Akuga.EventDefinitions import (SUMMON_JUMON_EVENT,
                                     SELECT_JUMON_TO_MOVE_EVENT,
                                     SELECT_JUMON_TO_SPECIAL_MOVE_EVENT,
                                     PICK_JUMON_EVENT,
                                     PLAYER_HAS_WON,
                                     MATCH_IS_DRAWN)


class IdleState(State):
    """
    The representation of the idle state which is the normal
    state a user idles in until he or she decides to summon a jumon
    or make a move
    """
    def __init__(self, fsm):
        super().__init__("idle_state", fsm)

    def Run(self, event):
        """
        Listen on SUMMON_JUMON_EVENT and SELECT_JUMON_TO_MOVE_EVENT as well
        as SELECT_JUMON_TO_SPECIAL_MOVE_EVENT
        """
        if type(self.fsm.player_chain.GetCurrentPlayer()) is\
                NeutralPlayer and self.fsm.player_chain.\
                GetCurrentPlayer().InMovePhase():
            """
            If the current player is a neutral player invoke its DoAMove
            Function and use its return to archieve a state change.
            """
            state_change = self.fsm.player_chain.\
                GetCurrentPlayer().DoAMove(self, (None, {}))
            """
            Do the state change created by the special ability
            of the jumon moved
            """
            if state_change[0] is not None:
                return state_change

        if event.type == PICK_JUMON_EVENT\
                and self.fsm.player_chain.GetCurrentPlayer().\
                InPickPhase():
            """
            The event is only valid if the current player is in the pick
            phase, and the jumon within the event is inside the
            jumon_pick_pool list
            """
            # Get the jumon to pick from the event
            jumon = event.jumon_to_pick
            if jumon in self.fsm.jumon_pick_pool:
                """
                Only jump to the pick state if the jumon is
                within the pick pool
                """
                pick_state_variables = {"jumon_to_pick": jumon}
                return (self.fsm.pick_state, pick_state_variables)

        if event.type == SUMMON_JUMON_EVENT\
                and self.fsm.player_chain.GetCurrentPlayer().\
                InSummonPhase():
            """
            The event is only valid if the current player is in the move
            phase, the jumon within the event is inside the
            jumons_to_summon list.
            """
            # Get the jumon to summon and create the state variables dict
            jumon = event.jumon_to_summon
            # Only summon the jumon if the player owns the jumon
            if self.fsm.player_chain.GetCurrentPlayer().\
                    CanSummon(jumon):
                # Jump to the summon state
                summon_state_variables = {"jumon_to_summon": jumon}
                return (self.fsm.summon_state, summon_state_variables)

        if event.type == SELECT_JUMON_TO_MOVE_EVENT\
                and self.fsm.player_chain.GetCurrentPlayer().InMovePhase():
            """
            Get the jumon to move, its position and the target position
            from the event. The CheckMoveState will check if the move is
            legal or not and handles the move
            """
            jumon = event.jumon_to_move
            current_position = event.current_position
            target_position = event.target_position
            # Only move the jumon if the current player controls the jumon
            if self.fsm.player_chain.GetCurrentPlayer().ControlsJumon(jumon):
                check_move_state_variables = {
                    "jumon_to_move": jumon,
                    "current_position": current_position,
                    "target_position": target_position}
                # Jump to the check move state
                return (self.fsm.check_move_state, check_move_state_variables)

        if event.type == SELECT_JUMON_TO_SPECIAL_MOVE_EVENT\
                and self.fsm.player_chain.GetCurrentPlayer().InMovePhase():
            """
            Get the jumon to move, its position and the target position
            from the event. The CheckSpecialMoveState will check if the
            move is legal or not and handles the move.
            """
            jumon = event.jumon_to_move
            current_position = event.current_position
            target_position = event.target_position
            check_move_state_variables = {
                "jumon_to_move": jumon,
                "current_position": current_position,
                "target_position": target_position}
            # Jump to the check_special_move_state
            return (self.fsm.check_special_move_state, check_move_state_variables)
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

    def Run(self, event):
        """
        Remove the jumon to pick from the pick pool and add it to the jumons
        the current player can summon. Then check if the player has to
        switch to the summon phase.
        """
        jumon = self.state_variables["jumon_to_pick"]
        jumon.SetOwner(self.fsm.player_chain.GetCurrentPlayer())
        self.fsm.jumon_pick_pool.remove(jumon)
        self.fsm.player_chain.GetCurrentPlayer().AddJumonToSummon(jumon)
        if len(self.fsm.jumon_pick_pool) < self.fsm.player_chain.GetNotNeutralLength():
            """
            If there are less jumons in the pick pool than not neutral
            player in the playerchain the current player wont be able to
            pick another jumon, so per must go into the summon phase
            """
            self.fsm.player_chain.GetCurrentPlayer().SetToSummonPhase()
        # The turn ends, so jump to the change player state
        return (self.fsm.change_player_state, {})


class SummonState(State):
    """
    SummonState is the representation of the moment a jumon is summoned.
    In this state a random position if generated and its always jumped
    to the SummonCheckState
    """
    def __init__(self, fsm):
        super().__init__("summon_state", fsm)

    def Run(self, event):
        """
        Just create a random position and jump to the
        summon_check_state with the position and the summon as
        summon_check_state_variables
        """
        x_position = random.randint(0, global_definitions.BOARD_WIDTH - 1)
        y_position = random.randint(0, global_definitions.BOARD_HEIGHT - 1)
        jumon_to_summon = self.state_variables["jumon_to_summon"]
        # Build the summon_check_variables
        summon_check_state_variables = {
            "jumon_to_summon": self.state_variables["jumon_to_summon"],
            "summon_position": Position(x_position, y_position)}
        """"
        Invoke the special ability function of the current jumon
        and use its return for the state change of the fsm
        """
        state_change = jumon_to_summon.SpecialAbility(self,
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

    def Run(self, event):
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
        if self.fsm.arena.GetUnitAt(summon_position) is None:
            """
            If the ArenaTile is free the jumon can be placed, its ability
            script triggers and the turn ends
            """
            # Let the current player summon this jumon
            self.fsm.player_chain.GetCurrentPlayer().\
                HandleSummoning(jumon)
            # Place the jumon at the arena
            self.fsm.arena.PlaceUnitAt(jumon, summon_position)
            jumon.SetPosition(summon_position)
            """
            Invoke the jumon special ability with the same state variables
            as no new state variables occured. This way enter the battlefield
            effects can be implemented.
            """
            state_change = jumon.SpecialAbility(self,
                    (self.fsm.change_player_state, self.state_variables))
            return state_change
        elif issubclass(type(self.fsm.arena.GetUnitAt(
                summon_position)), Akuga.Meeple.Artefact) and\
                self.fsm.arena.IsBlockedAt(summon_position) is False:
            """
            If the jumon is summoned on an artefact place it on this tile
            and jump to the equip artefact to jumon state
            """
            # Let the current player summon this jumon
            self.fsm.player_chain.GetCurrentPlayer().\
                HandleSummoning(jumon)
            # Get the artefact at this point
            artefact = self.fsm.arena.GetUnitAt(summon_position)
            # Place the jumon at the arena
            self.fsm.arena.PlaceUnitAt(jumon, summon_position)
            jumon.SetPosition(summon_position)
            """
            Create the state variables with the last state as None
            as there is no last position and do the state change
            """
            return (self.fsm.equip_artefact_to_jumon_state, {
                "jumon": jumon,
                "artefact": artefact,
                "last_position": None})

        elif self.fsm.player_chain.\
                GetCurrentPlayer().OwnsTile(self.fsm.arena, summon_position)\
                or self.fsm.arena.IsBlockedAt(summon_position):
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
            The OneTileBattleState also handles if the hostile jumon is not
            a jumon at all but an equipment or a trap.
            If the jumon to summon is going to be placed on the arena or not
            the player summoned it, so HandleSummoning must be invoked
            """
            self.fsm.player_chain.GetCurrentPlayer().\
                HandleSummoning(jumon)
            one_tile_battle_state_variables = {
                "battle_position": summon_position,
                "attacking_jumon": jumon,
                "defending_jumon": self.fsm.arena.GetUnitAt(summon_position)}
            return (self.fsm.one_tile_battle_begin_state, one_tile_battle_state_variables)


class ChangePlayerState(State):
    """
    This represents the moment between the turns.
    """
    def __init__(self, fsm):
        super().__init__("change_player_state", fsm)

    def Run(self, event):
        """
        Update the current player, check for victors or if the match
        is drawn and handle the end of a match with throwing the right
        events.
        Update the inner respresentation of the player
        aka check if per is dead or not.
        """
        self.fsm.player_chain.GetCurrentPlayer().UpdatePlayer()
        # Remove dead players from the player chain
        self.fsm.player_chain.Update()
        # Check if the match is drawn
        is_drawn = self.fsm.player_chain.CheckForDrawn()
        if is_drawn is True:
            """
            After this event has been handeld the state machiene should
            not be Updated anymore
            """
            drawn_event = pygame.event.Event(MATCH_IS_DRAWN)
            pygame.event.post(drawn_event)
        # Check if a player has won
        victor = self.fsm.player_chain.CheckForVictory()
        if victor is not None:
            """
            After this event has been handeld the state machiene should
            not be Updated anymore
            """
            won_event = pygame.event.Event(PLAYER_HAS_WON, victor=victor)
            pygame.event.post(won_event)
        """
        If no one has won and its not drawn change the player and
        jump to the idle state again so its the next players turn
        """
        self.fsm.player_chain.NextPlayersTurn()
        return (self.fsm.idle_state, {})


class CheckMoveState(State):
    """
    Checks wheter a draw of a jumon is legal or not
    """
    def __init__(self, fsm):
        super().__init__("check_move_state", fsm)

    def Run(self, event):
        # Get the jumon, its current position and the target position
        jumon = self.state_variables["jumon_to_move"]
        current_position = self.state_variables["current_position"]
        target_position = self.state_variables["target_position"]
        """
        Get the shortes distance between the current position and the
        target position. Do the move only if the path is not none (aka a
        path is found) and the pathlength is less then or equal to the
        movements of the selected jumon. This way the jumons actually
        move and can be blocked by other meeples.
        """
        move_path = FindPath(current_position, target_position, self.fsm.arena)
        if move_path is None or len(move_path) == 0\
                or len(move_path) - 1 > jumon.movement:
            """
            If the target move is invalid in length just jump back to the
            idle state.
            """
            return (self.fsm.idle_state, {})
        if self.fsm.arena.GetUnitAt(target_position) is None:
            """
            If the tile at target position is free just do the move
            and end the turn by jumping to the ChangePlayerState
            """
            self.fsm.arena.PlaceUnitAt(None, current_position)
            self.fsm.arena.PlaceUnitAt(jumon, target_position)
            jumon.SetPosition(target_position)
            return (self.fsm.change_player_state, {})
        elif self.fsm.player_chain.GetCurrentPlayer().\
                OwnsTile(self.fsm.arena, target_position):
            """
            If the target position is owned by a jumon of the current player
            the move is illegal and the a new move has to be defined,
            so jump back to the idle state
            """
            return (self.fsm.idle_state, {})
        elif issubclass(type(self.fsm.arena.GetUnitAt(target_position)), Akuga.Meeple.Artefact):
            """
            If the target position is occupied by an artefact jump to the
            equip artefact to jumon state
            """
            # Get the artefact at the target position
            artefact = self.fsm.arena.GetUnitAt(target_position)
            # Move the jumon
            self.fsm.arena.PlaceUnitAt(None, current_position)
            self.fsm.arena.PlaceUnitAt(jumon, target_position)
            jumon.SetPosition(target_position)
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
                "defending_jumon": self.fsm.arena.GetUnitAt(target_position),
                "attack_position": current_position,
                "defense_position": target_position}
            return (self.fsm.two_tile_battle_begin_state, two_tile_battle_state_variable)


class CheckSpecialMoveState(State):
    """
    Check if a special move is legal or not and invoke the special move
    function of the ability script of the current jumon.
    """
    def __init__(self, fsm):
        super().__init__("check_special_move_state", fsm)

    def Run(self, event):
        # Get the jumon, its current position and the target position
        jumon = self.state_variables["jumon_to_move"]
        current_position = self.state_variables["current_position"]
        target_position = self.state_variables["target_position"]
        if jumon.IsSpecialMoveLegal(current_position, target_position):
            """
            If the special move is legal invoke the special move function
            of the current jumon
            """
            state_change = jumon.DoSpecialMove(self.fsm, current_position,
                    target_position)
            return state_change
        else:
            """
            If there is no special ability script at all the special
            move is illegal by default, so just jump to the idle_state
            """
            return (self.fsm.idle_state, {})
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

    def Run(self, event):
        """
        Invoke the ability scripts of the fighting jumons and jump
        to the OneTileBattleFlipState
        """
        attacking_jumon = self.state_variables["attacking_jumon"]
        defending_jumon = self.state_variables["defending_jumon"]
        state_change = attacking_jumon.SpecialAbility(self,
                (self.fsm.one_tile_battle_flip_state,
                self.state_variables))
        state_change = defending_jumon.SpecialAbility(self, state_change)
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

    def Run(self, event):
        """
        Get the arena tile at the battle position and add it to the state
        variables. Then jump to the OneTileBattleBoniEvaluationState
        """
        attacking_jumon = self.state_variables["attacking_jumon"]
        defending_jumon = self.state_variables["defending_jumon"]
        battle_position = self.state_variables["battle_position"]
        battle_arena_tile = self.fsm.arena.GetTileAt(battle_position)
        # Now jump to the OneTileBattleBoniEvaluationState
        one_tile_battle_boni_evaluation_state_variables = {
            "attacking_jumon": attacking_jumon,
            "defending_jumon": defending_jumon,
            "battle_position": battle_position,
            "battle_arena_tile": battle_arena_tile}
        """
        After the aren tile has flipped invoke the ability script of the
        jumons. This way an interaction of the arena tile like the one
        of the nameless jumon or red robot can be implemented.
        The attacking jumons triggers first!
        That means the state change of the attacking jumon has to be passed
        to the defending jumon!
        """
        state_change = attacking_jumon.SpecialAbility(self,
                (self.fsm.one_tile_battle_boni_evaluation_state,
                 one_tile_battle_boni_evaluation_state_variables))
        state_change = defending_jumon.SpecialAbility(self,
                (state_change[0], state_change[1]))
        return state_change


class OneTileBattleBoniEvaluationState(State):
    """
    In this State the bonus of the arena is evaluated and a bonus value
    for both jumons are added to the state variables. Then the state
    machiene jumps to the OneTileBattleFightState
    """
    def __init__(self, fsm):
        super().__init__("one_tile_battle_boni_evaluation_state", fsm)

    def Run(self, event):
        """
        Add the boni of the arena tile to the state variables and jump
        to the OneTileBattleFightState
        """
        attacking_jumon = self.state_variables["attacking_jumon"]
        defending_jumon = self.state_variables["defending_jumon"]
        battle_position = self.state_variables["battle_position"]
        battle_arena_tile = self.state_variables["battle_arena_tile"]
        attacking_jumon_bonus = battle_arena_tile.GetBonusForJumon(attacking_jumon)
        defending_jumon_bonus = battle_arena_tile.GetBonusForJumon(defending_jumon)
        # Create the state_variables
        one_tile_battle_figh_state_variables = {
            "attacking_jumon": attacking_jumon,
            "defending_jumon": defending_jumon,
            "battle_position": battle_position,
            "battle_arena_tile": battle_arena_tile,
            "attacking_jumon_bonus": attacking_jumon_bonus,
            "defending_jumon_bonus": defending_jumon_bonus}
        """
        After the bonus values are evaluated invoke the ability scripts
        """
        state_change = attacking_jumon.SpecialAbility(self,
                (self.fsm.one_tile_battle_fight_state,
                one_tile_battle_figh_state_variables))
        state_change = defending_jumon.SpecialAbility(self,
                (state_change[0], state_change[1]))
        return state_change


class OneTileBattleFightState(State):
    """
    In this state both jumons fight the victor and the looser are determined
    Then the state machiene jumps to the OneTileBattleAfterMathState
    """
    def __init__(self, fsm):
        super().__init__("one_tile_battle_fight_state", fsm)

    def Run(self, event):
        """
        Fighting is pretty simple, the jumon with less power looses.
        If both jumons have the same power both jumon looses.
        Than the state machiene jumps to OneTileBattleAftermathState
        """
        attacking_jumon = self.state_variables["attacking_jumon"]
        defending_jumon = self.state_variables["defending_jumon"]
        battle_position = self.state_variables["battle_position"]
        battle_arena_tile = self.state_variables["battle_arena_tile"]
        attacking_jumon_bonus = self.state_variables["attacking_jumon_bonus"]
        defending_jumon_bonus = self.state_variables["defending_jumon_bonus"]
        # If no one wins victor and looser are none
        victor = None
        looser = None
        # Check if the summoned jumon looses
        if attacking_jumon.base_level + attacking_jumon.level_offset +\
                attacking_jumon_bonus < defending_jumon.base_level +\
                defending_jumon.level_offset + defending_jumon_bonus:
            victor = defending_jumon
            looser = attacking_jumon
        # Check if the summoned jumon wins
        if attacking_jumon.base_level + attacking_jumon.level_offset +\
                attacking_jumon_bonus > defending_jumon.base_level +\
                defending_jumon.level_offset + defending_jumon_bonus:
            victor = attacking_jumon
            looser = defending_jumon
        """
        The summoned jumon and the defending_jumon has to be in the variables
        as well to destroy both if victor and looser are None.
        Jump to the one_tile_battle_aftermath_state
        """
        one_tile_battle_aftermath_state_variables = {
            "attacking_jumon": attacking_jumon,
            "defending_jumon": defending_jumon,
            "battle_position": battle_position,
            "battle_arena_tile": battle_arena_tile,
            "attacking_jumon_bonus": attacking_jumon_bonus,
            "defending_jumon_bonus": defending_jumon_bonus,
            "victor": victor,
            "looser": looser}
        """
        Run the ability scripts after victor and looser are determined,
        this way ability scripts can trigger if the bakugan wins or looses
        """
        state_change = attacking_jumon.SpecialAbility(self,
                (self.fsm.one_tile_battle_aftermath_state,
                one_tile_battle_aftermath_state_variables))
        state_change = defending_jumon.SpecialAbility(self, state_change)
        return state_change


class OneTileBattleAftermathState(State):
    """
    In this state the jumon which loosed the fight is removed from the
    arena and the summoned jumon list of the player.
    The jumon which won the fight will be placed on the arena tile
    """
    def __init__(self, fsm):
        super().__init__("one_tile_battle_aftermath_state", fsm)

    def Run(self, event):
        attacking_jumon = self.state_variables["attacking_jumon"]
        defending_jumon = self.state_variables["defending_jumon"]
        battle_arena_tile = self.state_variables["battle_arena_tile"]
        victor = self.state_variables["victor"]
        looser = self.state_variables["looser"]
        # battle_position = self.state_variables["battle_position"]
        # attacking_jumon_bonus = self.state_variables["attacking_jumon_bonus"]
        # defending_jumon_bonus = self.state_variables["defending_jumon_bonus"]

        """
        Run the ability scripts before the jumons are killed.
        This way the destruction of both jumons could be prohibited
        and death rattle effects can be implemented
        """
        state_change = attacking_jumon.SpecialAbility(self,
                (self.fsm.change_player_state,
                self.state_variables))
        state_change = defending_jumon.SpecialAbility(self, state_change)
        if victor is None and looser is None:
            """
            If no victor and no looser is assigned both jumons had the same
            power level and both have to be destroyed
            If the attacker has an equipment attached to it detach it
            and place it on the arena tile
            """
            if attacking_jumon.equipment is not None:
                artefact = attacking_jumon.equipment
                artefact.DetachFrom(attacking_jumon)
                battle_arena_tile.PlaceUnit(artefact)
            """
            If the defender has an equipment attached to it detach it
            and place it on the arena tile. Cause this is handeld
            after the attacker the equipment of the defender overwrites
            the equipment of the attacker. This way the equipment of
            the attacker vanishes.
            """
            if defending_jumon.equipment is not None:
                artefact = defending_jumon.equipment
                artefact.DetachFrom(defending_jumon)
                battle_arena_tile.PlaceUnit(artefact)
            # Kill the jumons
            attacking_jumon.owned_by.HandleJumonDeath(attacking_jumon)
            defending_jumon.owned_by.HandleJumonDeath(defending_jumon)
            # Remove the occupying unit from the arena tile
            battle_arena_tile.RemoveUnit()
        else:
            if looser.equipment is not None:
                """
                If the looser had an artifact attached to it attach it to the
                winner instead
                """
                artifact = looser.equipment
                looser.equipment.DetachFrom(looser)
                artifact.AttachTo(victor)
            # Now kill the looser
            looser.owned_by.HandleJumonDeath(looser)
            # Place the victor on the arena tile
            battle_arena_tile.PlaceUnit(victor)
        # Now do the state_change (mostly jump to change_player_state)
        return state_change


class TwoTileBattleBeginState(State):
    """
    The start of a battle on two tiles
    This state does nothing on its own, its just an entry point
    for special ability scripts of the fighting jumon
    """
    def __init__(self, fsm):
        super().__init__("two_tile_battle_begin_state", fsm)

    def Run(self, event):
        """
        Invoke the ability scripts of the fighting jumons and jump
        to the TwoTileBattleFlipState
        """
        attacking_jumon = self.state_variables["attacking_jumon"]
        defending_jumon = self.state_variables["defending_jumon"]
        state_change = attacking_jumon.SpecialAbility(self,
                (self.fsm.two_tile_battle_flip_state,
                self.state_variables))
        state_change = defending_jumon.SpecialAbility(self, state_change)
        return state_change


class TwoTileBattleFlipState(State):
    """
    In this state the arena tiles at the battle positions are turned around
    and attached to the state informations. Then the state machiene
    immediatly jumps to the TwoTileBattleBoniEvaluationStep
    """
    def __init__(self, fsm):
        super().__init__("two_tile_battle_flip_state", fsm)

    def Run(self, event):
        """
        Get the arena tiles at the battle positions and add them to the state
        variables. Then jump to the TwoTileBattleBoniEvaluationState
        """
        attacking_jumon = self.state_variables["attacking_jumon"]
        defending_jumon = self.state_variables["defending_jumon"]
        attack_position = self.state_variables["attack_position"]
        defense_position = self.state_variables["defense_position"]
        attack_tile = self.fsm.arena.GetTileAt(attack_position)
        defense_tile = self.fsm.arena.GetTileAt(defense_position)
        # Now jump to the TwoTileBattleBoniEvaluationState
        two_tile_battle_boni_evaluation_state_variables = {
            "attacking_jumon": attacking_jumon,
            "defending_jumon": defending_jumon,
            "attack_position": attack_position,
            "defense_position": defense_position,
            "attack_tile": attack_tile,
            "defense_tile": defense_tile}
        """
        After the aren tile has flipped invoke the ability script of the
        jumons. This way an interaction of the arena tile like the one
        of the nameless jumon or red robot can be implemented.
        The attacking jumons triggers first!
        """
        state_change = attacking_jumon.SpecialAbility(self,
                (self.fsm.two_tile_battle_boni_evaluation_state,
                two_tile_battle_boni_evaluation_state_variables))
        state_change = defending_jumon.SpecialAbility(self, state_change)
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

    def Run(self, event):
        """
        Add the boni of the arena tiles to the state variables and jump
        to the TwoTileBattleFightState
        """
        attacking_jumon = self.state_variables["attacking_jumon"]
        defending_jumon = self.state_variables["defending_jumon"]
        attack_position = self.state_variables["attack_position"]
        defense_position = self.state_variables["defense_position"]
        attack_tile = self.state_variables["attack_tile"]
        defense_tile = self.state_variables["defense_tile"]

        # Get the bonus of the attack or defense tile
        attacking_jumon_bonus = attack_tile.GetBonusForJumon(attacking_jumon)
        defending_jumon_bonus = defense_tile.GetBonusForJumon(defending_jumon)
        # Now jump to the two_tile_battle_fight_state
        two_tile_battle_figh_state_variables = {
            "attacking_jumon": attacking_jumon,
            "defending_jumon": defending_jumon,
            "attack_position": attack_position,
            "defense_position": defense_position,
            "attack_tile": attack_tile,
            "defense_tile": defense_tile,
            "attacking_jumon_bonus": attacking_jumon_bonus,
            "defending_jumon_bonus": defending_jumon_bonus}
        """
        After the bonus values are evaluated invoke the ability scripts
        """
        state_change = attacking_jumon.SpecialAbility(self,
                (self.fsm.two_tile_battle_fight_state,
                two_tile_battle_figh_state_variables))
        state_change = defending_jumon.SpecialAbility(self, state_change)
        # Do the state change
        return state_change


class TwoTileBattleFightState(State):
    """
    In this state both jumons fight the victor and the looser are determined
    Then the state machiene jumps to the TwoTileBattleAfterMathState
    """
    def __init__(self, fsm):
        super().__init__("two_tile_battle_fight_state", fsm)

    def Run(self, event):
        """
        Fighting is pretty simple, the jumon with less power looses.
        If both jumons have the same power both jumon looses.
        Than the state machiene jumps to TwoTileBattleAftermathState
        """
        attacking_jumon = self.state_variables["attacking_jumon"]
        defending_jumon = self.state_variables["defending_jumon"]
        attack_position = self.state_variables["attack_position"]
        defense_position = self.state_variables["defense_position"]
        attack_tile = self.state_variables["attack_tile"]
        defense_tile = self.state_variables["defense_tile"]
        attacking_jumon_bonus = self.state_variables["attacking_jumon_bonus"]
        defending_jumon_bonus = self.state_variables["defending_jumon_bonus"]
        # If no one wins victor and looser are none
        victor = None
        looser = None
        # Check if the summoned jumon looses
        if attacking_jumon.base_level + attacking_jumon.level_offset +\
                attacking_jumon_bonus < defending_jumon.base_level +\
                defending_jumon.level_offset + defending_jumon_bonus:
            victor = defending_jumon
            looser = attacking_jumon
        # Check if the summoned jumon wins
        if attacking_jumon.base_level + attacking_jumon.level_offset +\
                attacking_jumon_bonus > defending_jumon.base_level +\
                defending_jumon.level_offset + defending_jumon_bonus:
            victor = attacking_jumon
            looser = defending_jumon
        """
        The summoned jumon and the defending_jumon has to be in the variables
        as well to destroy both if victor and looser are None.
        """
        two_tile_battle_aftermath_state_variables = {
            "attacking_jumon": attacking_jumon,
            "defending_jumon": defending_jumon,
            "attack_position": attack_position,
            "defense_position": defense_position,
            "attack_tile": attack_tile,
            "defense_tile": defense_tile,
            "attacking_jumon_bonus": attacking_jumon_bonus,
            "defending_jumon_bonus": defending_jumon_bonus,
            "victor": victor,
            "looser": looser}
        """
        Run the ability scripts after victor and looser are determined,
        this way ability scripts can trigger if the bakugan wins or looses
        """
        state_change = attacking_jumon.SpecialAbility(self,
                (self.fsm.two_tile_battle_aftermath_state,
                two_tile_battle_aftermath_state_variables))
        state_change = defending_jumon.SpecialAbility(self, state_change)
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

    def Run(self, event):
        attacking_jumon = self.state_variables["attacking_jumon"]
        defending_jumon = self.state_variables["defending_jumon"]
        attack_tile = self.state_variables["attack_tile"]
        defense_tile = self.state_variables["defense_tile"]
        victor = self.state_variables["victor"]
        looser = self.state_variables["looser"]
        """
        Run the ability scripts before the jumons are killed.
        This way the destruction of both jumons could be prohibited
        and death rattle effects can be implemented
        """
        state_change = attacking_jumon.SpecialAbility(self,
                (self.fsm.change_player_state,
                self.state_variables))
        state_change = defending_jumon.SpecialAbility(self, state_change)
        if victor is None and looser is None:
            """
            If no victor and no looser is assigned both jumons had the same
            power level and both have to be destroyed
            """
            # Kill both jumons
            attacking_jumon.owned_by.HandleJumonDeath(attacking_jumon)
            defending_jumon.owned_by.HandleJumonDeath(defending_jumon)
            # Remove both units from the arena tile
            attack_tile.RemoveUnit()
            defense_tile.RemoveUnit()
            if attacking_jumon.equipment is not None:
                """
                If the attacking_jumon had an artefact equiped drop it
                """
                artefact = attacking_jumon.equipment
                artefact.DetachFrom(attacking_jumon)
                attack_tile.PlaceUnit(artefact)
            if defending_jumon.equipment is not None:
                """
                If the defending_jumon had an artefact equiped drop it
                """
                artefact = defending_jumon.equipment
                artefact.DetachFrom(defending_jumon)
                defense_tile.PlaceUnit(artefact)

        elif victor is attacking_jumon:
            """
            If the jumon to move has won move it to the defense tile
            """
            # Just kill the looser
            defending_jumon.owned_by.HandleJumonDeath(defending_jumon)
            # Move the victor from the attack tile to the defense tile
            attack_tile.RemoveUnit()
            defense_tile.PlaceUnit(victor)
            if looser.equipment is not None:
                """
                If the defender had an equipment it has to be detached
                from it and attached to the attacker
                """
                looser_artefact = looser.equipment
                looser_artefact.DetachFrom(looser)
                if victor.equipment is not None:
                    """
                    If the victor jumon has an equipment on its own it dropps
                    its artefact on the attack tile and attaches the
                    artefact of the defender jumon
                    """
                    victor_artefact = victor.equipment
                    victor_artefact.DetachFrom(victor)
                    attack_tile.PlaceUnit(victor_artefact)
                # Attach the artefact of the defender to the attacker
                looser_artefact.AttachTo(victor)
        elif victor is defending_jumon:
            """
            If the defending_jumon has won remove the attacking jumon
            """
            # Just kill the looser
            attacking_jumon.owned_by.HandleJumonDeath(attacking_jumon)
            attack_tile.RemoveUnit()
            if attacking_jumon.equipment is not None:
                """
                If the attacking jumon had an equipment it drops it on the
                attack tile
                """
                # Detach the artefact from the jumon
                attack_artefact = attacking_jumon.equipment
                attack_artefact.DetachFrom(attacking_jumon)
                # Place it on the attack tile
                attack_tile.PlaceUnit(attack_artefact)
        # Now the turn ends so do the change
        return state_change


class EquipArtefactToJumonState(State):
    """
    Equips an artefact to a jumon
    """
    def __init__(self, fsm):
        super().__init__("equip_artefact_to_jumon_state", fsm)

    def Run(self, event):
        """
        Attaches an equipment to a jumon
        """
        jumon = self.state_variables["jumon"]
        artefact = self.state_variables["artefact"]
        last_position = self.state_variables["last_position"]

        if jumon.equipment is None:
            """
            If the jumon has no equipment yet just attach it
            """
            artefact.AttachTo(jumon)
        else:
            """
            If the jumon has an equipment attached it has to be detached
            and placed at the old position. In the very special case
            a jumon is summoned with an equipment attached to it
            aka last_position is None discard it
            """
            # Get the artefact to detach and detach it from the jumon
            detached_artefact = jumon.equipment
            detached_artefact.DetachFrom(jumon)
            # Attach the current artefact to the jumon
            artefact.AttachTo(jumon)
            """
            Just place the detached artefact on the arena again if the
            last position is not None like it would be if the jumon
            was just summoned. This presupposes there is a jumon
            which is summoned with an artefact attached to it
            """
            if last_position is not None:
                self.fsm.arena.PlaceUnitAt(detached_artefact, last_position)
        # Invoke the special ability of the jumon and do the state change
        state_change = (self.fsm.change_player_state, {})
        state_change = jumon.SpecialAbility(self, state_change)
        return state_change
