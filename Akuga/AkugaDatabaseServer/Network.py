"""
This module contains all functions related to network communication
"""
import socket
from json import (loads, dumps, JSONDecodeError)


class StreamSocketCommunicator:
    def __init__(self, connection, nbytes):
        '''
        connection: The stream socket to work on
        nbytes: Max bytes to read once at a time
        '''
        self.connection = connection
        self.nbytes = nbytes
        self.cached_string = ''

    def receive_line(self):
        '''
        Receives a complete line from a stream socket.
        Therefor the stream of bytes have to be cached and scaned for
        terminator signs. The newline character in this case
        '''
        index = self.cached_string.find('\n')
        while index < 0:
            # As long as there is no complete line cached receive bytes
            # from the wire
            new_data = self.connection.recv(self.nbytes).decode('utf-8')
            if not new_data:
                # If the connection was closed by the foreign host
                # raise a socket error
                raise socket.error
            self.cached_string += new_data
            # Again look for the newline character
            index = self.cached_string.find('\n')
        # Now a complete line is cached so return it and remove it from
        # the cache
        complete_line = self.cached_string[:index]
        self.cached_string = self.cached_string[index + 1:]
        return complete_line

    def recv_packet(self):
        """
        Receive a packet, aka a complete line, from the wire and use json
        to deserialize it. Only lists are accepted as valid datatypes
        """
        json_line = self.receive_line()
        try:
            packet = loads(json_line)
        except JSONDecodeError:
            self.send_packet(['ERROR', 'Invalid Packet'])
            return ['ERROR', 'Invalid Packet']
        if type(packet) is not list:
            self.send_packet(['ERROR', 'Invalid Packet'])
            return ['ERROR', 'Invalid Packet']
        return packet

    def send_packet(self, tokens):
        """
        Send a python list by serialising it using json
        """
        json_dump = dumps(tokens) + '\n'
        json_dump = json_dump.encode('utf-8')
        self.connection.send(json_dump)

    def close(self):
        """
        Closes the socket the communicator uses and cleares the chache
        """
        self.connection.close()
        self.cached_string = ''

    def refresh(self, new_communicator):
        """
        Overwrite the connection the communicator uses
        but leaves the cache untouched. This will be
        used if a user reconnects while playing
        """
        self.connection = new_communicator.connection


# TODO: Doesnt work yet, authentication fails...
def send_password_to_client_email(username, password, user_email):
    """
    Send the password to the client via email
    """
    pass
