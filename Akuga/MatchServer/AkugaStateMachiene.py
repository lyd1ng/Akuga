import Akuga.MatchServer.AkugaStates as AkugaStates
from Akuga.MatchServer.StateMachiene import StateMachiene


def create_last_man_standing_fsm():
    """
    Creates and returns state machiene for a last man standing game, which is
    the only game mode for now
    """
    fsm = StateMachiene(AkugaStates.TurnBeginState(None))
    fsm.add_state(AkugaStates.TurnEndState(None))
    fsm.add_state(AkugaStates.WaitForUserState(None))
    fsm.add_state(AkugaStates.PickState(None))
    fsm.add_state(AkugaStates.SummonState(None))
    fsm.add_state(AkugaStates.CheckMoveState(None))
    fsm.add_state(AkugaStates.CheckSpecialMoveState(None))
    fsm.add_state(AkugaStates.SummonCheckState(None))
    fsm.add_state(AkugaStates.ChangePlayerState(None))
    fsm.add_state(AkugaStates.EquipArtefactToJumonState(None))
    fsm.add_state(AkugaStates.OneTileBattleBeginState(None))
    fsm.add_state(AkugaStates.OneTileBattleFlipState(None))
    fsm.add_state(AkugaStates.OneTileBattleBoniEvaluationState(None))
    fsm.add_state(AkugaStates.OneTileBattleFightState(None))
    fsm.add_state(AkugaStates.OneTileBattleAftermathState(None))
    fsm.add_state(AkugaStates.TwoTileBattleBeginState(None))
    fsm.add_state(AkugaStates.TwoTileBattleFlipState(None))
    fsm.add_state(AkugaStates.TwoTileBattleBoniEvaluationState(None))
    fsm.add_state(AkugaStates.TwoTileBattleFightState(None))
    fsm.add_state(AkugaStates.TwoTileBattleAftermathState(None))
    fsm.add_state(AkugaStates.TimeoutState(None))
    return fsm
