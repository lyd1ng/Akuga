import random
import pygame
import Akuga.global_definitions as global_definitions
from Akuga.StateMachieneState import StateMachieneState as State
from Akuga.event_definitions import (SUMMON_JUMON_EVENT,
                                     SELECT_JUMON_TO_MOVE_EVENT,
                                     SELECT_JUMON_TO_SPECIAL_MOVE_EVENT,
                                     PLAYER_HAS_WON,
                                     MATCH_IS_DRAWN)


class IdleState(State):
    """
    The representation of the idle state which is the normal
    state a user idles in until he or she decides to summon a jumon
    or make a move
    """
    def __init__(self):
        super().__init__("IDLE_STATE")

    def run(self, event):
        """
        Listen on SUMMON_JUMON_EVENT and SELECT_JUMON_TO_MOVE_EVENT
        """
        if event.type == SUMMON_JUMON_EVENT\
                and global_definitions.PLAYER_CHAIN.GetCurrentPlayer().\
                InSummonPhase():
            """
            The event is only valid if the current player is in the move
            phase, the jumon within the event is inside the
            jumons_to_summon list.
            """
            # Get the jumon to summon and create the state variables dict
            jumon = event.jumon_to_summon
            summon_state_variables = {"jumon_to_summon": jumon}
            # Only summon the jumon if the player owns the jumon
            if global_definitions.PLAYER_CHAIN.GetCurrentPlayer().\
                    CanSummon(jumon):
                # Jump to the summon_state with the jumon as state variables
                return (summon_state, summon_state_variables)

        if event.type == SELECT_JUMON_TO_MOVE_EVENT\
                and global_definitions.PLAYER_CHAIN.GetCurrentPlayer().InMovePhase():
            """
            Get the jumon to move, its position and the target position
            from the event. The CheckDrawState will check if the move is
            legal or not and handles the move
            """
            jumon = event.jumon_to_move
            current_position = event.current_position
            target_position = event.target_position
            # Only move the jumon if the current player controls the jumon
            if global_definitions.PLAYER_CHAIN.GetCurrentPlayer().ControlsJumon(jumon):
                check_move_state_variables = {
                    "jumon_to_move": jumon,
                    "current_position": current_position,
                    "target_position": target_position}
                return (check_move_state, check_move_state_variables)

        if event.type == SELECT_JUMON_TO_SPECIAL_MOVE_EVENT\
                and global_definitions.PLAYER_CHAIN.GetCurrentPlayer().InMovePhase():
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
            return (check_special_move_state, check_move_state_variables)

            pass
        # If no event was caught return None, so the state machiene
        # remains in the idle state
        return None


class SummonState(State):
    """
    SummonState is the representation of the moment a jumon is summoned.
    In this state a random position if generated and its always jumped
    to the SummonCheckState
    """
    def __init__(self):
        super().__init__("SUMMON_STATE")

    def run(self, event):
        """
        Just create a random position and jump to the
        summon_check_state with the position and the summon as
        summon_check_state_variables
        """
        x_position = random.randint(0, global_definitions.BOARD_WIDTH - 1)
        y_position = random.randint(0, global_definitions.BOARD_HEIGHT - 1)
        summon_check_state_variables = {
            "jumon_to_summon": self.state_variables["jumon_to_summon"],
            "summon_position": (x_position, y_position)}
        return (summon_check_state, summon_check_state_variables)


class SummonCheckState(State):
    """
    In this state its checked whether the jumon has to be replaced, the
    jummon was summond on a free position and the turn is over or
    a battle is triggererd
    """
    def __init__(self):
        super().__init__("SUMMON_CHECK_STATE")

    def run(self, event):
        """
        Check if the summon position is free, which makes the summonation
        complete and ends the turn, the summon position is blocked which
        makes the state machiene jump back to the SummonState or the
        summon position is blocked by a hostile jumon which leads to
        a jump to the OneTileBattleState.
        """
        # Get the jumon to summon and where to summon it
        jumon = self.state_variables["jumon_to_summon"]
        summon_position = self.state_variables["summon_position"]
        if global_definitions.ARENA.GetUnitAt(summon_position) is None:
            """
            If the ArenaTile is free the invocation is complete and the
            turn ends
            """
            # Let the current player handle the summoning
            global_definitions.PLAYER_CHAIN.GetCurrentPlayer().\
                HandleSummoning(jumon, summon_position)
            # Jump to the change player state to end the turn
            change_player_state_variables = {}
            return (change_player_state, change_player_state_variables)
        elif global_definitions.PLAYER_CHAIN.\
                GetCurrentPlayer().OwnsTile(summon_position)\
                or global_definitions.ARENA.IsBlockedAt(summon_position):
            """
            If the jumon at this tile is owned  by the current player
            the jumon has to be replaced, so jump back to the summon state
            """
            summon_state_variables = {
                "jumon_to_summon": self.state_variables["jumon_to_summon"]}
            return (summon_state, summon_state_variables)
        else:
            """
            If the tile is not empty and the jumon is not owned by
            the current player it has to be a hostile jumon so jump
            to the OneTileBattleState with the position as well as
            both the current and the hostile jumon attached as
            state variables.
            The OneTileBattleState also handles if the hostile jumon is not
            a jumon at all but an equipment or a trap
            """
            one_tile_battle_state_variables = {
                "battle_position": summon_position,
                "summoned_jumon": jumon,
                "occupying_jumon": global_definitions.ARENA.GetUnitAt(summon_position)}
            return (one_tile_battle_begin_state, one_tile_battle_state_variables)


class ChangePlayerState(State):
    """
    This represents the moment between the turns.
    """
    def __init__(self):
        super().__init__("CHANGE_PLAYER_STATE")

    def run(self, event):
        # Remove dead players from the player chain
        global_definitions.PLAYER_CHAIN.Update()
        # Check if the match is drawn
        is_drawn = global_definitions.PLAYER_CHAIN.CheckForDrawn()
        if is_drawn is True:
            """
            After this event has been handeld the state machiene should
            not be updated anymore
            """
            drawn_event = pygame.event.Event(MATCH_IS_DRAWN)
            pygame.event.post(drawn_event)
        # Check if a player has won
        victor = global_definitions.PLAYER_CHAIN.CheckForVictory()
        if victor is not None:
            """
            After this event has been handeld the state machiene should
            not be updated anymore
            """
            won_event = pygame.event.Event(PLAYER_HAS_WON, victor=victor)
            pygame.event.post(won_event)
        """
        If no one has won and its not drawn change the player and
        jump to the idle state again so its the next players turn
        """
        global_definitions.PLAYER_CHAIN.NextPlayersTurn()
        return (idle_state, {})


class CheckMoveState(State):
    """
    Checks wheter a draw of a jumon is legal or not
    """
    def __init__(self):
        super().__init__("CHECK_MOVE_STATE")

    def run(self, event):
        # Get the jumon, its current position and the target position
        jumon = self.state_variables["jumon_to_move"]
        current_position = self.state_variables["current_position"]
        target_position = self.state_variables["target_position"]
        # Get the distance to check if a move is valid or not
        manhatte_distance = abs(current_position[0] - target_position[0]) + \
            abs(current_position[1] - target_position[1])
        if manhatte_distance > jumon.movement and manhatte_distance != 0 or\
                target_position[0] < 0 or target_position[1] < 0:
            """
            If the target move is invalid in length just jump back to the
            idle state.
            """
            return (idle_state, {})
        if global_definitions.ARENA.GetUnitAt(target_position) is None:
            """
            If the tile at target position is free just do the move
            and end the turn by jumping to the ChangePlayerState
            """
            global_definitions.ARENA.PlaceUnitAt(None, current_position)
            global_definitions.ARENA.PlaceUnitAt(jumon, target_position)
            return (change_player_state, {})
        elif global_definitions.PLAYER_CHAIN.GetCurrentPlayer().\
                OwnsTile(target_position):
            """
            If the target position is owned by a jumon of the current player
            the move is illegal and the a new move has to be defined,
            so jump back to the idle state
            """
            return (idle_state, {})
        else:
            """
            If the target position is not empty and the jumon on target
            position is not owned by the current player it has to be
            a hostile jumon, so a TwoTileBattle is triggered
            """
            two_tile_battle_state_variable = {
                "jumon_to_move": jumon,
                "occupying_jumon": global_definitions.ARENA.GetUnitAt(target_position),
                "attack_position": current_position,
                "defense_position": target_position}
            return (two_tile_battle_begin_state, two_tile_battle_state_variable)


class CheckSpecialMoveState(State):
    """
    Check if a special move is legal or not and invoke the special move
    function of the ability script of the current jumon.
    """
    def __init__(self):
        super().__init__("CHECK_SPECIAL_MOVE_STATE")

    def run(self, event):
        # Get the jumon, its current position and the target position
        jumon = self.state_variables["jumon_to_move"]
        current_position = self.state_variables["current_position"]
        target_position = self.state_variables["target_position"]
        if jumon.ability_script is not None:
            """
            If the ability script is not None define a local
            is_special_move_legal function which has to be overwritten
            if the jumon should be allowed to make a special move.
            This way not every jumon with an other special ability
            has to define the is_special_move_legal function.
            """
            def is_special_move_legal(current_position, target_position):
                return False
            # Now evaluate the ability script
            exec(jumon.ability_script)
            # Now the is_special_move_legal might be overwritten
            if is_special_move_legal(current_position, target_position):
                """
                If the special move is legal invoke the special move function
                which HAS TO BE DEFINED within the ability_script of the
                jumon
                """
                do_special_move(current_position, target_position)
                """
                After the special move is done end the turn by jumping to the
                ChangePlayerState
                """
                return (change_player_state, {})
            else:
                """
                If there is no special ability script at all the special
                move is illegal by default, so just jump to the idle_state
                """
                return (idle_state, {})


class OneTileBattleBeginState(State):
    """
    The start of a battle on one tile
    This state does nothing on its own, its just an entry point
    for special ability scripts of the fighting jumon
    """
    def __init__(self):
        super().__init__("ONE_TILE_BATTLE_STATE")

    def run(self, event):
        """
        Invoke the ability scripts of the fighting jumons and jump
        to the OneTileBattleFlipState
        """
        summoned_jumon = event.summoned_jumon
        occupying_jumon = event.occupying_jumon
        # The attacking jumon triggers its ability script first
        if summoned_jumon.ability_script is not None:
            exec(summoned_jumon.ability_script)
        # Then the occupying jumon triggers its ability script
        if occupying_jumon.ability_script is not None:
            exec(occupying_jumon.ability_script)
        # Jump to the OneTileBattleFlipState with the same variables
        return (one_tile_battle_flip_state, self.state_variables)


class OneTileBattleFlipState(State):
    """
    In this state the arena tile at battle position is turned around
    and attached to the state informations. Then the state machiene
    immediatly jumps to the OneTileBattleBoniEvaluationStep
    """
    def __init__():
        super().__init__("ONE_TILE_BATTLE_FLIP_STATE")

    def run(self, event):
        """
        Get the arena tile at the battle position and add it to the state
        variables. Then jump to the OneTileBattleBoniEvaluationState
        """
        summoned_jumon = event.summoned_jumon
        occupying_jumon = event.occupying_jumon
        battle_position = event.battle_position
        battle_arena_tile = global_definitions.ARENA.GetTileAt(battle_position)
        one_tile_battle_boni_evaluation_state_variables = {
            "summoned_jumon": summoned_jumon,
            "occupying_jumon": occupying_jumon,
            "battle_position": battle_position,
            "battle_arena_tile": battle_arena_tile}
        # Now jump to the OneTileBattleBoniEvaluationState
        return (one_tile_battle_boni_evaluation_state,
                one_tile_battle_boni_evaluation_state_variables)


class OneTileBattleBoniEvaluationState(State):
    """
    In this State the bonus of the arena is evaluated and a bonus value
    for both jumons are added to the state variables. Then the state
    machiene jumps to the OneTileBattleFightState
    """
    def __init__(self):
        super().__init__("ONE_TILE_BATTLE_BONI_EVALUATION_STATE")

    def run(self, event):
        """
        Add the boni of the arena tile to the state variables and jump
        to the OneTileBattleFightState
        """
        summoned_jumon = event.summoned_jumon
        occupying_jumon = event.occupying_jumon
        battle_position = event.battle_position
        battle_arena_tile = event.battle_arena_tile
        summoned_jumon_bonus = battle_arena_tile.GetBonusForJumon(summoned_jumon)
        occupying_jumon_bonus = battle_arena_tile.GetBonusForJumon(occupying_jumon)
        one_tile_battle_figh_state_variables = {
            "summoned_jumon": summoned_jumon,
            "occupying_jumon": occupying_jumon,
            "battle_position": battle_position,
            "summoned_jumon_bonus": summoned_jumon_bonus,
            "occupying_jumon_bonus": occupying_jumon_bonus}
        return (one_tile_battle_fight_state,
                one_tile_battle_figh_state_variables)


idle_state = IdleState()
summon_state = SummonState()
check_move_state = CheckMoveState()
check_special_move_state = CheckSpecialMoveState()
summon_check_state = SummonCheckState()
change_player_state = ChangePlayerState()
one_tile_battle_begin_state = OneTileBattleBeginState()
one_tile_battle_flip_state = OneTileBattleFlipState()
one_tile_battle_boni_evaluation_state = None
one_tile_battle_fight_state = None
two_tile_battle_begin_state = None
