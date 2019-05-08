import pygame
from Akuga.Jumon import Jumon
from Akuga.Player import Player
from Akuga.PlayerChain import PlayerChain
from Akuga.event_definitions import (SUMMON_JUMON_EVENT, SELECT_JUMON_TO_MOVE_EVENT)
import Akuga.global_definitions as global_definitions
from Akuga import AkugaStates
from Akuga.StateMachiene import StateMachiene


def main():
    pygame.init()
    state_machiene = StateMachiene([AkugaStates.idle_state, AkugaStates.summon_state], AkugaStates.idle_state)
    # pygame.display.set_mode(SCREEN_DIMENSION)
    running = True

    jumon1 = Jumon("1", 400, 2, None, None)
    jumon2 = Jumon("2", 450, 2, None, None)
    jumon3 = Jumon("3", 400, 2, None, None)
    jumon4 = Jumon("4", 450, 2, None, None)

    player1 = Player("Thomas", [jumon1, jumon2])
    player2 = Player("Lukas", [jumon3, jumon4])
    global_definitions.PLAYER_CHAIN = PlayerChain(player1, player2)

    while running:
        pygame.event.pump()
        event = pygame.event.poll()
        command = input("Command [[Thomas/Lukas] summon, move, quit]: ")
        if command == "quit":
            running = False
        if command == "summon":
            jumon = global_definitions.PLAYER_CHAIN.GetCurrentPlayer().jumons_to_summon[0]
            event = pygame.event.Event(SUMMON_JUMON_EVENT, jumon_to_summon=jumon)
            pygame.event.post(event)
        if command == "move":
            cx = int(input("Current X: "))
            cy = int(input("Current Y: "))
            tx = int(input("Target X: "))
            ty = int(input("Target Y: "))
            jumon_to_move = global_definitions.ARENA.GetUnitAt((cx, cy))
            if global_definitions.PLAYER_CHAIN.GetCurrentPlayer().OwnsTile((cx, cy)) is False:
                print("Invalid, no Jumon you control found at this position")
                continue
            event = pygame.event.Event(SELECT_JUMON_TO_MOVE_EVENT,
                jumon_to_move=jumon_to_move,
                current_position=(cx, cy),
                target_position=(tx, ty))
            pygame.event.post(event)
        state_machiene.run(event)
        print("The current player is: " + global_definitions.PLAYER_CHAIN.GetCurrentPlayer().name)
        global_definitions.ARENA.PrintOut()


if __name__ == "__main__":
    main()
