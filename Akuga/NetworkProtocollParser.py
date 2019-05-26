import socket
import pygame
from Akuga import MeepleDict
from Akuga import GlobalDefinitions
from Akuga.Position import Position
from Akuga.EventDefinitions import (SUMMON_JUMON_EVENT,
                              SELECT_JUMON_TO_MOVE_EVENT,
                              SELECT_JUMON_TO_SPECIAL_MOVE_EVENT,
                              PICK_JUMON_EVENT)


def HandleMatchConnection(player, connection):
    """
    Receives a package from connection with a timeout of the defined
    seconds per turn. If a packet was received parse it and handle it by
    throwing the appropriate events.
    If the socket times out the current player is killed.
    The same is true if an error occurs while parsing the packet.
    """
    connection.settimeout(GlobalDefinitions.SECONDS_PER_TURN)
    try:
        """
        Receive the packet from the players connection
        """
        packet = connection.recv(1024)
    except socket.timeout:
        """
        The player timed out so he looses the game
        """
        player.Kill()
        return
    try:
        """
        Decode the bytes to a string using utf-8 and split it into tokens
        using ':' as delimeter
        """
        tokens = packet.decode('utf-8').split(":")
    except UnicodeDecodeError:
        """
        If there is an error decoding the players packet. It contained
        invalid data. Just kill the player
        """
        player.Kill()
        return

    if tokens[0] == "PICK_JUMON" and len(tokens) >= 2:
        """
        Handles a pick jumon command
        PICK_JUMON $name_of_the_jumon_to_pick
        """
        try:
            jumon_to_pick = MeepleDict.GetMeepleByName(tokens[1])
        except KeyError:
            player.Kill()
            return
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
            player.Kill()
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
            Default: Kill the player if an error occures
            """
            player.Kill()
            return
        # Get the jumon to move by its name
        try:
            jumon_to_move = MeepleDict.GetMeepleByName(tokens[1])
        except KeyError:
            player.Kill()
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
            player.Kill()
            return
        # Get the jumon to move by its name
        try:
            jumon_to_special_move = MeepleDict.GetMeepleByName(tokens[1])
        except KeyError:
            player.Kill()
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

    while True:
        connection, connection_address = server_socket.accept()
        HandleMatchConnection(None, connection)

        pygame.event.pump()
        event = pygame.event.poll()
        if event.type == PICK_JUMON_EVENT:
            print("Pick Jumon Event: " + event.jumon_to_pick.name)
        if event.type == SUMMON_JUMON_EVENT:
            print("Summon Jumon Event: " + event.jumon_to_summon.name)
        if event.type == SELECT_JUMON_TO_MOVE_EVENT:
            print("Move Jumon Event: " + event.jumon_to_move.name)
            print("Current Position: " + str(event.current_position))
            print("Target Position: " + str(event.target_position))
        if event.type == SELECT_JUMON_TO_SPECIAL_MOVE_EVENT:
            print("Special Move Jumon Event: " + event.jumon_to_move.name)
            print("Current Position: " + str(event.current_position))
            print("Target Position: " + str(event.target_position))
