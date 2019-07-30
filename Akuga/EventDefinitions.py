"""
This file contains every user defined event,
0 - 99: Input events for the rule building fsm
100 - 199: Output events from the rule building fsm
200 - 299: Network related events
"""

# An empty event which is thrown if no event is in the queue
# this allows a non blocking get on the queue
NOEVENT = -1

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


class Event:
    def __init__(self, _type, **kwargs):
        self.type = _type
        # Make every element of the kwarg dictionarie a member of this
        # event instance. So e = Event(0, a='a', b='b'); print(e.a)
        # is possible
        self.__dict__.update(kwargs)

    def __eq__(self, other):
        '''
        Allows an equality check between an instance of an Event and an integer
        Only the event type is compared
        '''
        return self.type == other
