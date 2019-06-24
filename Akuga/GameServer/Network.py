"""
This module contains all functions related to network communication
"""
import socket
from ast import literal_eval

whitelist = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'


def recv_packet(connection, nbytes, delimiter, terminator):
    """
    Receive a packet and convert it into tokens using the delimiter.
    Return ['ERROR', $msg] if there no terminator is found,
    return all tokens except the terminator token otherwise.
    If the connection was closed raise a socket.error
    """
    packet = connection.recv(nbytes)
    if not packet:
        raise socket.error
    packet = packet.decode('utf-8')
    tokens = packet.split(delimiter)
    if tokens[-1] == terminator:
        return tokens[0:-1]
    return ['ERROR', 'No terminator found while recv the packet']


def send_packet(connection, tokens, terminator="END"):
    """
    Send a packet containing multiple tokens.
    Every token is converted to a string using the str function
    for better convenients and is encoded using utf-8 encoding.
    A packet has the form token1:token2:...:tokenN:terminator
    """
    query = ""
    for t in tokens:
        query += str(t) + ":"
    if terminator is not None:
        query += str(terminator)
    query = query.encode('utf-8')
    connection.send(query)


def secure_string(string):
    """
    Return True if all characters in the string are part of the
    whitelist. Otherwise return False
    """
    for s in string:
        if s not in whitelist:
            return False
    return True


def receive_dbs_response(userdbs_connection, nbytes, delimiter, terminator):
    """
    Receive up to 512 bytes from the database server
    and parse it using the parse_literal function of the
    ast module. This can be done as the pysqlite module
    return its results as a python list
    """
    tokens = recv_packet(userdbs_connection, nbytes, delimiter, terminator)
    # If an error is received return None and the error msg received
    if tokens[0] == "ERROR":
        return (None, tokens[1])
    # If no error is received return the parsed literal and "" as msg
    print("Litetal to parse: " + tokens[1])
    return (literal_eval(tokens[1]), "")


# TODO: Doesnt work yet, authentication fails...
def send_password_to_client_email(username, password, user_email):
    """
    Send the password to the client via email
    """
    pass
