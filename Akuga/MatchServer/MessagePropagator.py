'''
This module contains all functions to propagate messages
to users or a subset of users
'''
from Akuga.MatchServer.NetworkProtocoll import (send_packet)


def propagate_message(message_event):
    '''
    Use the send_packet function to send a packet made out of tokens to all
    users specified in the message_event.
    Therefor the message_event has to provide:
    users: a list of user instances
    tokens: a list of tokens building the packet

    Brokene connections will be ignored as timeout and reconnects are
    handeld elsewhere in the code
    '''
    users = message_event.users
    tokens = message_event.tokens
    for user in users:
        try:
            send_packet(user.connection, tokens)
        except IOError:
            # If the connection is broken just do nothing it will be
            # handeld elsewhere in the code
            pass
