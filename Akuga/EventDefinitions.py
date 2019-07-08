import pygame
"""
This file contains every user defined events
"""

# Events to leave the idle state
SUMMON_JUMON_EVENT = pygame.USEREVENT + 1
SELECT_JUMON_TO_MOVE_EVENT = pygame.USEREVENT + 2
SELECT_JUMON_TO_SPECIAL_MOVE_EVENT = pygame.USEREVENT + 3
PICK_JUMON_EVENT = pygame.USEREVENT + 4

# Events thrown by the state machiene
PLAYER_HAS_WON = pygame.USEREVENT + 5
MATCH_IS_DRAWN = pygame.USEREVENT + 6
TURN_ENDS = pygame.USEREVENT + 7

# Network Protocoll Events
PACKET_PARSER_ERROR_EVENT = pygame.USEREVENT + 8

# Serverside events
TIMEOUT_EVENT = pygame.USEREVENT + 9
