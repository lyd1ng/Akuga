import socket
import errno
import pygame
import fcntl
import os
from Akuga import MeepleDict
from Akuga.Position import Position
from Akuga.EventDefinitions import (SUMMON_JUMON_EVENT,
                              SELECT_JUMON_TO_MOVE_EVENT,
                              SELECT_JUMON_TO_SPECIAL_MOVE_EVENT,
                              PICK_JUMON_EVENT)


def AsyncCallbackRecv(connection, nbytes, callback, terminator="END"):
    """
    Receives bytes from connection until terminator is received.
    Than invoke callback with the received data
    """
    try:
        """
        Read and decode the packet asynchrounisly
        """
        AsyncCallbackRecv.cached_str += connection.recv(nbytes).decode('utf-8')
    except socket.error as e:
        if e.args[0] == errno.EAGAIN or e.args[0] == errno.EWOULDBLOCK:
            """
            If the error is just cause by the lack of data do nothin
            """
            pass
        else:
            """
            If the error is a real error close the connection for now
            TODO: Better connection error handling
            """
            print("Fatal error occured on " + str(connection))
            connection.close()
    except UnicodeDecodeError:
        """
        If an decode error occured clear the string and return the function
        """
        AsyncCallbackRecv.cached_str = ""
        return
    # Search the received string for the terminator
    terminator_index = AsyncCallbackRecv.cached_str.find(terminator)
    if terminator_index > -1:
        """
        If there is a terminator within this packet invoke the callback
        function with the packet until the terminator
        """
        callback(AsyncCallbackRecv.cached_str[:terminator_index])
        # The string has to be cleared to receive a new packet
        AsyncCallbackRecv.cached_str = ""


# Attach this variable to the function to fake static variables in python
AsyncCallbackRecv.cached_str = ""


def SendPacket(connection, tokens, terminator="END"):
    """
    Send a packet containing out of multiple tokens
    Every token is converted to a string using the str function
    for better convenients and is encoded using utf-8 encoding.
    A packet has the form token1:token2:...:tokenN:terminator
    """
    for t in tokens:
        connection.send((str(t) + ":").encode('utf-8'))
    if terminator is not None:
        connection.send(str(terminator).encode('utf-8'))


def HandleMatchConnection(packet):
    """
    Receives a package from connection with a timeout of the defined
    seconds per turn. If a packet was received parse it and handle it by
    throwing the appropriate events.
    If the socket times out the current player is killed.
    The same is true if an error occurs while parsing the packet.
    """
    tokens = packet.split(":")
    print(tokens)

    if tokens[0] == "PICK_JUMON" and len(tokens) >= 2:
        """
        Handles a pick jumon command
        PICK_JUMON $name_of_the_jumon_to_pick
        """
        try:
            jumon_to_pick = MeepleDict.GetMeepleByName(tokens[1])
        except KeyError:
            return
        print("Throw pick event!")
        jumon_pick_event = pygame.event.Event(PICK_JUMON_EVENT,
                jumon_to_pick=jumon_to_pick)
        pygame.event.post(jumon_pick_event)

    if tokens[0] == "SUMMON_JUMON" and len(tokens) >= 2:
        """
        Handles a summon jumon command
        SUMMON_JUMON $name_of_the_jumon_to_summon
        """
        try:
            jumon_to_summon = MeepleDict.GetMeepleByName(tokens[1])
        except KeyError:
            return
        jumon_summon_event = pygame.event.Event(SUMMON_JUMON_EVENT,
                jumon_to_summon=jumon_to_summon)
        pygame.event.post(jumon_summon_event)

    if tokens[0] == "MOVE_JUMON" and len(tokens) >= 3:
        """
        Handles a move jumon command
        MOVE_JUMON $name_of_the_jumon_to_summon $target_position
        The target position is in the format $x,$y
        """
        # Split the target position string into x an y tokens
        position_x_str, position_y_str = tokens[2].split(",")
        try:
            """
            Convert the x and y tokens into integers
            """
            position_x = int(position_x_str)
            position_y = int(position_y_str)
        except ValueError:
            """
            """
            return
        # Get the jumon to move by its name
        try:
            jumon_to_move = MeepleDict.GetMeepleByName(tokens[1])
        except KeyError:
            return
        # If no error occured the event can be thrown
        jumon_move_event = pygame.event.Event(SELECT_JUMON_TO_MOVE_EVENT,
                jumon_to_move=jumon_to_move,
                current_position=jumon_to_move.GetPosition(),
                target_position=Position(position_x, position_y))
        pygame.event.post(jumon_move_event)

    if tokens[0] == "SPECIAL_MOVE_JUMON" and len(tokens) >= 3:
        """
        Handles a move jumon command
        MOVE_JUMON $name_of_the_jumon_to_summon $target_position
        The target position is in the format $x,$y
        """
        # Split the target position string into x an y tokens
        position_x_str, position_y_str = tokens[2].split(",")
        try:
            """
            Convert the x and y tokens into integers
            """
            position_x = int(position_x_str)
            position_y = int(position_y_str)
        except ValueError:
            """
            Default: Kill the player if an error occures
            """
            return
        # Get the jumon to move by its name
        try:
            jumon_to_special_move = MeepleDict.GetMeepleByName(tokens[1])
        except KeyError:
            return
        # If no error occured the event can be thrown
        jumon_special_move_event = pygame.event.Event(
            SELECT_JUMON_TO_SPECIAL_MOVE_EVENT,
            jumon_to_move=jumon_to_special_move,
            current_position=jumon_to_special_move.GetPosition(),
            target_position=Position(position_x, position_y))
        pygame.event.post(jumon_special_move_event)


if __name__ == "__main__":
    pygame.init()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", 12345))
    server_socket.listen(1)

    connection, connection_address = server_socket.accept()
    fcntl.fcntl(connection, fcntl.F_SETFL, os.O_NONBLOCK)

    while True:
        AsyncCallbackRecv(connection, 128, HandleMatchConnection)

        pygame.event.pump()
        event = pygame.event.poll()
        if event.type == PICK_JUMON_EVENT:
            print("Pick Jumon Event: " + event.jumon_to_pick.name)
        if event.type == SUMMON_JUMON_EVENT:
            print("Summon Jumon Event: " + event.jumon_to_summon.name)
            SendPacket(connection, ["A", "pick", "jumon", "event",
                "was", "thrown"])
        if event.type == SELECT_JUMON_TO_MOVE_EVENT:
            print("Move Jumon Event: " + event.jumon_to_move.name)
            print("Current Position: " + str(event.current_position))
            print("Target Position: " + str(event.target_position))
        if event.type == SELECT_JUMON_TO_SPECIAL_MOVE_EVENT:
            print("Special Move Jumon Event: " + event.jumon_to_move.name)
            print("Current Position: " + str(event.current_position))
            print("Target Position: " + str(event.target_position))
    server_socket.close()
