import pygame
from Akuga.Position import Position
from Akuga.Jumon import (Jumon, TestJumon, Test2Jumon)
from Akuga.Player import Player
from Akuga.PlayerChain import PlayerChain
from Akuga.event_definitions import (SUMMON_JUMON_EVENT,
                                     SELECT_JUMON_TO_MOVE_EVENT,
                                     PLAYER_HAS_WON,
                                     MATCH_IS_DRAWN)
import Akuga.global_definitions as global_definitions
from Akuga import AkugaStates
from Akuga.StateMachiene import StateMachiene


def main():
    pygame.init()
    state_machiene = StateMachiene(AkugaStates.idle_state)
    # pygame.display.set_mode(SCREEN_DIMENSION)
    running = True

    player1 = Player("Spieler1")
    player2 = Player("Spieler2")
    global_definitions.PLAYER_CHAIN = PlayerChain(player1, player2)

    jumon1 = Jumon("1", "red", 400, 1, None, player1)
    jumon3 = Test2Jumon("red", 400, 1, None, player2)

    player1.SetJumonsToSummon([jumon1])
    player2.SetJumonsToSummon([jumon3])

    while running:
        pygame.event.pump()
        event = pygame.event.poll()

        if event.type == PLAYER_HAS_WON:
            print(event.victor.name + " has won!")
            exit()
        if event.type == MATCH_IS_DRAWN:
            print("Match is drawn")
            exit()
        command = input("Command [[Thomas/Lukas] summon, move, surrender, quit]: ")
        if command == "quit":
            player1.Kill()
            player2.Kill()
            print(global_definitions.PLAYER_CHAIN.len)
        if command == "summon":
            jumon = global_definitions.PLAYER_CHAIN.GetCurrentPlayer().jumons_to_summon[0]
            event = pygame.event.Event(SUMMON_JUMON_EVENT, jumon_to_summon=jumon)
            pygame.event.post(event)
        if command == "move":
            cx = int(input("Current X: "))
            cy = int(input("Current Y: "))
            tx = int(input("Target X: "))
            ty = int(input("Target Y: "))
            jumon_to_move = global_definitions.ARENA.GetUnitAt(Position(cx, cy))
            if global_definitions.PLAYER_CHAIN.GetCurrentPlayer().OwnsTile(Position(cx, cy)) is False:
                print("Invalid, no Jumon you control found at this position")
                continue
            event = pygame.event.Event(SELECT_JUMON_TO_MOVE_EVENT,
                jumon_to_move=jumon_to_move,
                current_position=Position(cx, cy),
                target_position=Position(tx, ty))
            pygame.event.post(event)
        if command == "surrender":
            global_definitions.PLAYER_CHAIN.GetCurrentPlayer().Kill()
        state_machiene.run(event)
        print("The current player is: " + global_definitions.PLAYER_CHAIN.GetCurrentPlayer().name)
        global_definitions.ARENA.PrintOut()


if __name__ == "__main__":
    main()
