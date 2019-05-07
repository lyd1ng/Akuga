import random
from Akuga.global_definitions import (BOARD_WIDTH, BOARD_HEIGHT)
from Akuga.StateMachieneState import StateMachieneState as State
from Akuga.event_definitions import (SUMMON_JUMON_EVENT,
                                     SELECT_JUMON_TO_MOVE_EVENT,
                                     SELECT_JUMON_TO_SPECIAL_MOVE_EVENT)


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
        if event.type == SUMMON_JUMON_EVENT:
            # Get the jumon to summon and create the state variables dict
            jumon = event.jumon_to_summon
            summon_state_variables = {"jumon_to_summon": jumon}
            # Jump to the summon_state with the jumon as state variables
            return (summon_state, summon_state_variables)

        if event.type == SELECT_JUMON_TO_MOVE_EVENT:
            """
            Get the jumon to move, its position and the target position
            from the event. The CheckDrawState will check if the move is
            legal or not and handles the move
            """
            jumon = event.jumon_to_move
            current_position = event.current_position
            target_position = event.target_position
            check_move_state_variables = {
                "jumon_to_move": jumon,
                "current_position": current_position,
                "target_position": target_position}
            return (check_move_state, check_move_state_variables)

        if event.type == SELECT_JUMON_TO_SPECIAL_MOVE_EVENT:
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
        x_position = random.randint(0, BOARD_WIDTH)
        y_position = random.randint(0, BOARD_HEIGHT)
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
        """
        If the ArenaTile is free the invocation is complete and the
        turn ends
        """
        if ARENA.GetUnitAt(summon_position) is None:
            ARENA.PlaceUnitAt(jumon, summon_position)
            """
            Now the turn is over and the player has to change
            so jump to the ChangePlayerState
            """
            change_player_state_variables = {}
            return (change_player_state, change_player_state_variables)
        elif ARENA.GetUnitAt(summon_position).owned_by == CURRENT_PLAYER\
                or ARENA.IsBlockedAt(summon_position):
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
                "occupying_jumon": ARENA.GetUnitAt(summon_position)}
            return (one_tile_battle_state, one_tile_battle_state_variables)


class ChangePlayerState(State):
    """
    This represents the moment between the turns.
    The CURRENT_PLAYER variable (an integer) is incremented by
    one and wrapped to the interval [0, MAX_PLAYERS[
    """
    def __init__(self):
        super().__init__("CHANGE_PLAYER_STATE")

    def run(self, event):
        """
        Increment the CURRENT_PLAYER variable and wrapp it within the
        interval [0, MAX_PLAYERS[
        Than instantly jump to the idle state
        """
        CURRENT_PLAYER = CURRENT_PLAYER + 1
        CURRENT_PLAYER = CURRENT_PLAYER % MAX_PLAYERS
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
        if manhatte_distance > jumon.movement and manhatte_distance != 0:
            """
            If the target move is invalid in length just jump back to the
            idle state.
            """
            return (idle_state, {})
        if ARENA.GetUnitAt(target_position) is None:
            """
            If the tile at target position is free just do the move
            and end the turn by jumping to the ChangePlayerState
            """
            ARENA.PlaceUnitAt(None, current_position)
            ARENA.PlaceUnitAt(jumon, target_position)
            return (change_player_state, {})
        elif ARENA.GetUnitAt(target_position).owned_by == CURRENT_PLAYER:
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
                "occupying_jumon": ARENA.GetUnitAt(target_position),
                "attack_position": current_position,
                "defense_position": target_position}
            return (two_tile_battle_state, two_tile_battle_state_variable)


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


idle_state = IdleState()
summon_state = SummonState()
check_move_state = CheckMoveState()
check_special_move_state = CheckSpecialMoveState()
summon_check_state = SummonCheckState()
change_player_state = ChangePlayerState()
one_tile_battle_state = None
two_tile_battle_state = None
