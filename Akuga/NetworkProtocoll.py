import socket
import errno
import pygame
import fcntl
import os
from Akuga.MeepleDict import GetMeepleByName
from Akuga.Position import Position
from Akuga.EventDefinitions import (SUMMON_JUMON_EVENT,
                              SELECT_JUMON_TO_MOVE_EVENT,
                              SELECT_JUMON_TO_SPECIAL_MOVE_EVENT,
                              PICK_JUMON_EVENT,
                              PACKET_PARSER_ERROR_EVENT)


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
        event = pygame.event.Event(PACKET_PARSER_ERROR_EVENT,
                msg="Decode Error")
        pygame.event.post(event)
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
            jumon_to_pick = GetMeepleByName(tokens[1])
        except KeyError:
            event = pygame.event.Event(PACKET_PARSER_ERROR_EVENT,
                    msg="Invalid Meeple")
            pygame.event.post(event)
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
            jumon_to_summon = GetMeepleByName(tokens[1])
        except KeyError:
            event = pygame.event.Event(PACKET_PARSER_ERROR_EVENT,
                    msg="Invalid Meeple")
            pygame.event.post(event)
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
            event = pygame.event.Event(PACKET_PARSER_ERROR_EVENT,
                    msg="Invalid Position Data")
            pygame.event.post(event)
            return
        # Get the jumon to move by its name
        try:
            jumon_to_move = GetMeepleByName(tokens[1])
        except KeyError:
            event = pygame.event.Event(PACKET_PARSER_ERROR_EVENT,
                    msg="Invalid Meeple")
            pygame.event.post(event)
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
            event = pygame.event.Event(PACKET_PARSER_ERROR_EVENT,
                    msg="Invalid Position Data")
            pygame.event.post(event)
            return
        # Get the jumon to move by its name
        try:
            jumon_to_special_move = GetMeepleByName(tokens[1])
        except KeyError:
            event = pygame.event.Event(PACKET_PARSER_ERROR_EVENT,
                    msg="Invalid Meeple")
            pygame.event.post(event)
            return
        # If no error occured the event can be thrown
        jumon_special_move_event = pygame.event.Event(
            SELECT_JUMON_TO_SPECIAL_MOVE_EVENT,
            jumon_to_move=jumon_to_special_move,
            current_position=jumon_to_special_move.GetPosition(),
            target_position=Position(position_x, position_y))
        pygame.event.post(jumon_special_move_event)


def SendClientGameState(connection, game_state):
    """
    Send all neccessary data from the server game state to build the client
    game state. The client game state is an excerpt from the state machiene
    as some data should be hidden or is not necessary for the match client
    """
    # First of all send the pick pool
    pick_pool_data_tokens = ["PICK_POOL_DATA"]
    for jumon in game_state.jumon_pick_pool:
        """
        Send the name of the jumon and the
        name of its equipment if there is one
        """
        pick_pool_data_tokens.append((jumon.name, jumon.equipment.name
            if jumon.equipment is not None
            else ""))
    SendPacket(connection, pick_pool_data_tokens)

    """
    Now go through all the players and send the jummons per can summon
    and the jumons per has already summoned.
    """
    for player in game_state.player_chain.GetPlayers():
        pld_jumons_to_summon_token = [
            "PLAYER_DATA_JUMONS_TO_SUMMON",
            player.name]
        pld_summoned_jumons = [
            "PLAYER_DATA_SUMMONED_JUMONS",
            player.name]
        # Go through all jumons to summon
        for jumon in player.jumons_to_summon:
            pld_jumons_to_summon_token.append((jumon.name, jumon.equipment.name
                if jumon.equipment is not None
                else ""))
        # Go through all summoned jumons
        for jumon in player.summoned_jumons:
            pld_summoned_jumons.append((jumon.name, jumon.equipment.name
                if jumon.equipment is not None
                else ""))
        # Send the data
        SendPacket(connection, pld_jumons_to_summon_token)
        SendPacket(connection, pld_summoned_jumons)

    """
    Now go through all tiles of the arena and send the meeple occupying
    this tile
    """
    # packet format: cmd, (width, height), meeple1, meeple2, ... meepleN, END
    packet_tokens = [
        "ARENA_DATA",
        (game_state.arena.board_width, game_state.arena.board_height)]
    """
    Go through all tiles of the arena and append
    the names of the occupying meeple
    """
    for y in range(game_state.arena.board_height):
        for x in range(game_state.arena.board_width):
            meeple = game_state.arena.GetUnitAt(Position(x, y))
            packet_tokens.append(meeple.name if meeple is not None else "")
    SendPacket(connection, packet_tokens)


if __name__ == "__main__":
    from Akuga.Player import Player
    from Akuga.PlayerChain import PlayerChain
    from Akuga.ArenaCreator import CreateArena
    import Akuga.GlobalDefinitions as GlobalDefinitions
    import Akuga.AkugaStateMachiene as AkugaStateMachiene

    pygame.init()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", 12345))
    server_socket.listen(1)

    player1 = Player("player1")
    player2 = Player("player2")
    player_chain = PlayerChain(player1, player2)

    GetMeepleByName("Jumon1").SetOwner(player1)
    GetMeepleByName("Jumon2").SetOwner(player1)
    player1.AddJumonToSummon(GetMeepleByName("Jumon1"))
    player1.AddJumonToSummon(GetMeepleByName("Jumon2"))

    GetMeepleByName("Jumon3").SetOwner(player2)
    GetMeepleByName("Jumon4").SetOwner(player2)
    player2.AddJumonToSummon(GetMeepleByName("Jumon3"))
    player2.AddJumonToSummon(GetMeepleByName("Jumon4"))

    arena = CreateArena(GlobalDefinitions.BOARD_WIDTH,
                        GlobalDefinitions.BOARD_HEIGHT,
                        0, 255)
    game_state = AkugaStateMachiene.CreateLastManStandingFSM()
    game_state.AddData("arena", arena)
    game_state.AddData("player_chain", player_chain)
    game_state.AddData("jumon_pick_pool", [GetMeepleByName("Jumon5")])

    arena.PlaceUnitAt(GetMeepleByName("NeutralJumon1"), Position(0, 0))

    while True:
        connection, address = server_socket.accept()
        SendClientGameState(connection, game_state)
        connection.close()

    server_socket.close()
