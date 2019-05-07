import pygame
from copy import copy
from Akuga.Jumon import Jumon
from Akuga.event_definitions import (SUMMON_JUMON_EVENT, SELECT_JUMON_TO_MOVE_EVENT)
import Akuga.global_definitions as global_definitions
from Akuga import AkugaStates
from Akuga.StateMachiene import StateMachiene


def main():
    pygame.init()
    state_machiene = StateMachiene([AkugaStates.idle_state, AkugaStates.summon_state], AkugaStates.idle_state)
    # pygame.display.set_mode(SCREEN_DIMENSION)
    running = True

    jumon = Jumon("1", 400, 1, None, global_definitions.CURRENT_PLAYER, None)

    while running:
        pygame.event.pump()
        event = pygame.event.poll()
        command = input("Command [summon, move, quit]: ")
        if command == "quit":
            running = False
        if command == "summon":
            jumon_to_summon = copy(jumon)
            jumon_to_summon.owned_by = global_definitions.CURRENT_PLAYER
            print("owned by: " + str(global_definitions.CURRENT_PLAYER))
            event = pygame.event.Event(SUMMON_JUMON_EVENT, jumon_to_summon=jumon_to_summon)
            pygame.event.post(event)
        if command == "move":
            cx = int(input("Current X: "))
            cy = int(input("Current Y: "))
            tx = int(input("Target X: "))
            ty = int(input("Target Y: "))
            jumon_to_move = global_definitions.ARENA.GetUnitAt((cx, cy))
            if jumon_to_move is None or jumon_to_move.owned_by != global_definitions.CURRENT_PLAYER:
                print("Invalid, no Jumon you control found at this position")
                continue
            event = pygame.event.Event(SELECT_JUMON_TO_MOVE_EVENT,
                jumon_to_move=jumon_to_move,
                current_position=(cx, cy),
                target_position=(tx, ty))
            pygame.event.post(event)
        state_machiene.run(event)
        print("The current player is: " + str(global_definitions.CURRENT_PLAYER))
        global_definitions.ARENA.PrintOut()


if __name__ == "__main__":
    main()
