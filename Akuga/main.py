import pygame
from Akuga.Position import Position
from Akuga.Meeple import (Jumon, Test2Artefact, TestNeutralJumon)
from Akuga.Player import (Player, NeutralPlayer)
from Akuga.PlayerChain import PlayerChain
from Akuga.event_definitions import (SUMMON_JUMON_EVENT,
                                     SELECT_JUMON_TO_MOVE_EVENT,
                                     PICK_JUMON_EVENT,
                                     PLAYER_HAS_WON,
                                     MATCH_IS_DRAWN)
from Akuga.ArenaCreator import CreateArena
import Akuga.global_definitions as global_definitions
import Akuga.AkugaStateMachiene as AkugaStateMachiene


def main():
    pygame.init()
    # pygame.display.set_mode(SCREEN_DIMENSION)
    Running = True

    # Create the arena to play in
    arena = CreateArena(global_definitions.BOARD_WIDTH,
                        global_definitions.BOARD_HEIGHT,
                        0, 255)
    # Create the player chain
    player1 = Player("Spieler1")
    player2 = Player("Spieler2")
    neutral_player = NeutralPlayer(arena)
    player_chain = PlayerChain(player1, player2)
    player_chain.InsertPlayer(neutral_player)

    jumon1 = Jumon("1", "red", 400, 2, None, player1)
    jumon3 = Jumon("2", "red", 400, 2, None, player2)
    jumon4 = TestNeutralJumon(neutral_player)

    test_artefact = Test2Artefact()
    test_artefact.AttachTo(jumon4)

    # Create the fsm and add the 'globale' data to it
    state_machiene = AkugaStateMachiene.CreateLastManStandingFSM()
    state_machiene.AddData("arena", arena)
    state_machiene.AddData("player_chain", player_chain)
    state_machiene.AddData("jumon_pick_pool", [jumon1, jumon3])

    neutral_player.SetJumonsToSummon([jumon4])
    player1.AddJumonToSummon(jumon1)
    player2.AddJumonToSummon(jumon3)
    neutral_player.SummonJumons()

    while Running:
        pygame.event.pump()
        event = pygame.event.poll()

        if event.type == PLAYER_HAS_WON:
            print(event.victor.name + " has won!")
            exit()
        if event.type == MATCH_IS_DRAWN:
            print("Match is Drawn")
            exit()
        command = input("Command [[Thomas/Lukas] summon, move, surrender, quit]: ")
        if command == "quit":
            player1.Kill()
            player2.Kill()
            print(player_chain.len)
        if command == "pick":
            jumon = state_machiene.jumon_pick_pool[0]
            event = pygame.event.Event(PICK_JUMON_EVENT, jumon_to_pick=jumon)
            pygame.event.post(event)
        if command == "summon":
            jumon = player_chain.GetCurrentPlayer().jumons_to_summon[0]
            event = pygame.event.Event(SUMMON_JUMON_EVENT, jumon_to_summon=jumon)
            pygame.event.post(event)
        if command == "move":
            cx = int(input("Current X: "))
            cy = int(input("Current Y: "))
            tx = int(input("Target X: "))
            ty = int(input("Target Y: "))
            jumon_to_move = arena.GetUnitAt(Position(cx, cy))
            if player_chain.GetCurrentPlayer().OwnsTile(arena,
                    Position(cx, cy))is False:
                print("Invalid, no Jumon you control found at this position")
                continue
            event = pygame.event.Event(SELECT_JUMON_TO_MOVE_EVENT,
                jumon_to_move=jumon_to_move,
                current_position=Position(cx, cy),
                target_position=Position(tx, ty))
            pygame.event.post(event)
        if command == "surrender":
            player_chain.GetCurrentPlayer().Kill()
        state_machiene.Run(event)
        print("The current player is: " + player_chain.GetCurrentPlayer().name)
        arena.PrintOut()


if __name__ == "__main__":
    main()
