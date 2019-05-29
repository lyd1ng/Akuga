import Akuga.MatchServer.AkugaStates as AkugaStates
from Akuga.MatchServer.StateMachiene import StateMachiene


def CreateLastManStandingFSM():
    """
    Creates and returns state machiene for a last man standing game, which is
    the only game mode for now
    """
    fsm = StateMachiene(AkugaStates.IdleState(None))
    fsm.AddState(AkugaStates.PickState(None))
    fsm.AddState(AkugaStates.SummonState(None))
    fsm.AddState(AkugaStates.CheckMoveState(None))
    fsm.AddState(AkugaStates.CheckSpecialMoveState(None))
    fsm.AddState(AkugaStates.SummonCheckState(None))
    fsm.AddState(AkugaStates.ChangePlayerState(None))
    fsm.AddState(AkugaStates.EquipArtefactToJumonState(None))
    fsm.AddState(AkugaStates.OneTileBattleBeginState(None))
    fsm.AddState(AkugaStates.OneTileBattleFlipState(None))
    fsm.AddState(AkugaStates.OneTileBattleBoniEvaluationState(None))
    fsm.AddState(AkugaStates.OneTileBattleFightState(None))
    fsm.AddState(AkugaStates.OneTileBattleAftermathState(None))
    fsm.AddState(AkugaStates.TwoTileBattleBeginState(None))
    fsm.AddState(AkugaStates.TwoTileBattleFlipState(None))
    fsm.AddState(AkugaStates.TwoTileBattleBoniEvaluationState(None))
    fsm.AddState(AkugaStates.TwoTileBattleFightState(None))
    fsm.AddState(AkugaStates.TwoTileBattleAftermathState(None))
    return fsm
