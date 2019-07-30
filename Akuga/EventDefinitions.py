"""
This file contains every user defined event,
0 - 99: Input events for the rule building fsm
100 - 199: Output events from the rule building fsm
200 - 299: Network related events
"""

# Events to leave the idle state
SUMMON_JUMON_EVENT = 1
SELECT_JUMON_TO_MOVE_EVENT = 2
SELECT_JUMON_TO_SPECIAL_MOVE_EVENT = 3
PICK_JUMON_EVENT = 4
TIMEOUT_EVENT = 5


# Events thrown by the state machiene
PLAYER_HAS_WON = 100
MATCH_IS_DRAWN = 101
TURN_ENDS = 102

# Network Protocoll Events
PACKET_PARSER_ERROR_EVENT = 200
