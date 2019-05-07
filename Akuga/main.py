import pygame
from Akuga.ArenaCreator import CreateArena
from Akuga.Jumon import Jumon
from Akuga.event_definitions import (SUMMON_JUMON_EVENT, SELECT_JUMON_TO_MOVE_EVENT)
from Akuga.global_definitions import SCREEN_DIMENSION
from Akuga import AkugaStates
from Akuga.StateMachiene import StateMachiene


def main():
    pygame.init()
    state_machiene = StateMachiene([AkugaStates.idle_state, AkugaStates.summon_state], AkugaStates.idle_state)
    pygame.display.set_mode(SCREEN_DIMENSION)
    running = True

    jumon = Jumon(400, 1, None, 0, None)

    while running:
        pygame.event.pump()
        event = pygame.event.poll()
        if event.type == pygame.QUIT:
            running = False
        command = input("Command [summon, draw]: ")
        if command == "quit":
            running = False
        if command == "summon":
            event = pygame.event.Event(SUMMON_JUMON_EVENT, jumon_to_summon=jumon)
            pygame.event.post(event)
        if command == "draw_valid":
            event = pygame.event.Event(SELECT_JUMON_TO_MOVE_EVENT,
                jumon_to_move=jumon,
                current_position=(0, 0),
                target_position=(1, 0))
            pygame.event.post(event)
        if command == "draw_invalid":
            event = pygame.event.Event(SELECT_JUMON_TO_MOVE_EVENT,
                jumon_to_move=jumon,
                current_position=(0, 0),
                target_position=(1, 1))
            pygame.event.post(event)
        if command == "run":
            state_machiene.run(event)
    pass


if __name__ == "__main__":
    main()
