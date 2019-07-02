import socket
import errno
import pygame
from Akuga.MatchServer.MeepleDict import get_meeple_by_name
from Akuga.MatchServer.Position import Position
from Akuga.EventDefinitions import (SUMMON_JUMON_EVENT,
                                    SELECT_JUMON_TO_MOVE_EVENT,
                                    SELECT_JUMON_TO_SPECIAL_MOVE_EVENT,
                                    PICK_JUMON_EVENT,
                                    PACKET_PARSER_ERROR_EVENT)


class AsyncCallbackReceiver:
    # Store the bytes until a whole packet is received
    cached_str = ""
    current_connection = None
    @staticmethod
    def refresh_connection(connection):
        """
        Drop all bytes until no data is received anymore
        (ddos is possible here) and clear the cached_str.
        This is used to reset the connection for the new turn of a player.
        If this function isnt invoked events may be handeld the player send
        while it is not pers turn. Its uncritically, no invalid moves are
        possible, its just for convenients.
        """
        AsyncCallbackReceiver.cached_str = ""
        while True:
            try:
                # Drop the data
                connection.recv(1024)
            except socket.error as e:
                # Leave the while loop if no data is on the socket anymore
                if e.args[0] == errno.EAGAIN or e.args[0] == errno.EWOULDBLOCK:
                    break
                else:
                    """
                    If the error is a real error close the connection for now
                    TODO: Better connection error handling
                    """
                    connection.close()

    @staticmethod
    def async_callback_recv(connection,
                          nbytes,
                          queue,
                          callback,
                          delimiter,
                          terminator="END"):
        """
        Receives bytes from connection until terminator is received.
        Than invoke callback with the received data
        """
        # If the connection is a new connection refresh it
        if connection != AsyncCallbackReceiver.current_connection:
            AsyncCallbackReceiver.refresh_connection(connection)
            AsyncCallbackReceiver.current_connection = connection
        try:
            """
            Read and decode the packet asynchrounisly
            """
            AsyncCallbackReceiver.cached_str += connection.recv(nbytes).decode('utf-8')
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
                connection.close()
        except UnicodeDecodeError:
            """
            If an decode error occured clear the string and return the function
            """
            event = pygame.event.Event(PACKET_PARSER_ERROR_EVENT,
                    msg="Decode Error")
            queue.put(event)
            AsyncCallbackReceiver.cached_str = ""
            return
        # Search the received string for the terminator
        terminator_index = AsyncCallbackReceiver.cached_str.find(terminator)
        if terminator_index > -1:
            """
            If there is a terminator within this packet invoke the callback
            function with the packet until the terminator
            """
            tokens = AsyncCallbackReceiver.cached_str.split(delimiter)
            if tokens[-1] != terminator:
                callback(['ERROR', 'No terminator\
                    found while recv the packet'], queue)
            else:
                callback(tokens[0:-1], queue)
            # The string has to be cleared to receive a new packet
            AsyncCallbackReceiver.cached_str = ""


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


def handle_match_connection(tokens, queue):
    """
    Receives a package from connection with a timeout of the defined
    seconds per turn. If the socket times out the current player is killed.
    The same is true if an error occurs while parsing the packet.
    """
    if tokens[0] == "PICK_JUMON" and len(tokens) >= 2:
        """
        Handles a pick jumon command
        PICK_JUMON $name_of_the_jumon_to_pick
        """
        try:
            jumon = get_meeple_by_name(tokens[1])
        except KeyError:
            event = pygame.event.Event(PACKET_PARSER_ERROR_EVENT,
                    msg="Invalid Meeple")
            queue.put(event)
            return
        jumon_pick_event = pygame.event.Event(PICK_JUMON_EVENT,
                jumon=jumon)
        queue.put(jumon_pick_event)
    if tokens[0] == "SUMMON_JUMON" and len(tokens) >= 2:
        """
        Handles a summon jumon command
        SUMMON_JUMON $name_of_the_jumon_to_summon
        """
        try:
            jumon = get_meeple_by_name(tokens[1])
        except KeyError:
            event = pygame.event.Event(PACKET_PARSER_ERROR_EVENT,
                    msg="Invalid Meeple")
            queue.put(event)
            return
        jumon = pygame.event.Event(SUMMON_JUMON_EVENT,
                jumon=jumon)
        queue.put(jumon)

    if tokens[0] == "MOVE_JUMON" and len(tokens) >= 3:
        """
        Handles a move jumon command
        MOVE_JUMON $name_of_the_jumon_to_summon $target_position
        The target position is in the format $x,$y
        """
        try:
            """
            Convert the x and y tokens into integers
            """
            # Split the target position string into x an y tokens
            position_x_str, position_y_str = tokens[2].split(",")
            position_x = int(position_x_str)
            position_y = int(position_y_str)
        except ValueError:
            event = pygame.event.Event(PACKET_PARSER_ERROR_EVENT,
                    msg="Invalid Position Data")
            queue.put(event)
            return
        # Get the jumon to move by its name
        try:
            jumon = get_meeple_by_name(tokens[1])
        except KeyError:
            event = pygame.event.Event(PACKET_PARSER_ERROR_EVENT,
                    msg="Invalid Meeple")
            queue.put(event)
            return
        # If no error occured the event can be thrown
        jumon_move_event = pygame.event.Event(SELECT_JUMON_TO_MOVE_EVENT,
                jumon=jumon,
                current_position=jumon.get_position(),
                target_position=Position(position_x, position_y))
        queue.put(jumon_move_event)

    if tokens[0] == "SPECIAL_MOVE_JUMON" and len(tokens) >= 3:
        """
        Handles a move jumon command
        MOVE_JUMON $name_of_the_jumon_to_summon $target_position
        The target position is in the format $x,$y
        """
        try:
            """
            Convert the x and y tokens into integers
            """
            # Split the target position string into x an y tokens
            position_x_str, position_y_str = tokens[2].split(",")
            position_x = int(position_x_str)
            position_y = int(position_y_str)
        except ValueError:
            event = pygame.event.Event(PACKET_PARSER_ERROR_EVENT,
                    msg="Invalid Position Data")
            queue.put(event)
            return
        # Get the jumon to move by its name
        try:
            jumon = get_meeple_by_name(tokens[1])
        except KeyError:
            event = pygame.event.Event(PACKET_PARSER_ERROR_EVENT,
                    msg="Invalid Meeple")
            queue.put(event)
            return
        # If no error occured the event can be thrown
        jumon_special_move_event = pygame.event.Event(
            SELECT_JUMON_TO_SPECIAL_MOVE_EVENT,
            jumon=jumon,
            current_position=jumon.get_position(),
            target_position=Position(position_x, position_y))
        queue.put(jumon_special_move_event)


def send_gamestate_to_client(connection, game_state):
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
    send_packet(connection, pick_pool_data_tokens)

    # Now go through all the players and send the jummons per can summon
    # and the jumons per has already summoned.
    for player in game_state.player_chain.get_players():
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
        send_packet(connection, pld_jumons_to_summon_token)
        send_packet(connection, pld_summoned_jumons)

    # Now go through all tiles of the arena and send the meeple occupying
    # this tile
    # packet format: cmd, (width, height), meeple1, meeple2, ... meepleN, END
    packet_tokens = [
        "ARENA_DATA",
        (game_state.arena.board_width, game_state.arena.board_height)]
    # Go through all tiles of the arena and append
    # the names of the occupying meeple
    for y in range(game_state.arena.board_height):
        for x in range(game_state.arena.board_width):
            meeple = game_state.arena.get_unit_at(Position(x, y))
            packet_tokens.append(meeple.name if meeple is not None else "")
    send_packet(connection, packet_tokens)

    # Now go through all jumons summoned and send the interferences
    # The interferences has to be sent even if there are none to clear
    # the interferences if there where one during the last turn
    for player in game_state.player_chain.get_players():
        for jumon in player.summoned_jumons:
            # Both interferences are send as a complete dict
            # They can be parsed using the ast.literal_eval function
            nonpersistent_interference_tokens = [
                'JUMON_NONPERSISTENT_INTERFERENCE',
                jumon.name,
                jumon.nonpersistent_interf]
            persistent_interference_tokens = [
                'JUMON_PERSISTENT_INTERFERENCE',
                jumon.name,
                jumon.persistent_interf]
            # Send the packets
            send_packet(connection, nonpersistent_interference_tokens)
            send_packet(connection, persistent_interference_tokens)
    # Now send the name of the current player
    send_packet(connection, ["CURRENT_PLAYER",
        game_state.player_chain.get_current_player().name])


if __name__ == "__main__":
    from Akuga.Player import Player
    from Akuga.PlayerChain import PlayerChain
    from Akuga.ArenaCreator import create_arena
    import Akuga.GlobalDefinitions as GlobalDefinitions
    import Akuga.AkugaStateMachiene as AkugaStateMachiene

    pygame.init()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", 12345))
    server_socket.listen(1)

    player1 = Player("player1")
    player2 = Player("player2")
    player_chain = PlayerChain(player1, player2)

    get_meeple_by_name("Jumon1").set_owner(player1)
    get_meeple_by_name("Jumon2").set_owner(player1)
    player1.add_jumon_to_summon(get_meeple_by_name("Jumon1"))
    player1.add_jumon_to_summon(get_meeple_by_name("Jumon2"))

    get_meeple_by_name("Jumon3").set_owner(player2)
    get_meeple_by_name("Jumon4").set_owner(player2)
    player2.add_jumon_to_summon(get_meeple_by_name("Jumon3"))
    player2.add_jumon_to_summon(get_meeple_by_name("Jumon4"))

    arena = create_arena(GlobalDefinitions.BOARD_WIDTH,
                        GlobalDefinitions.BOARD_HEIGHT,
                        0, 255)
    game_state = AkugaStateMachiene.create_last_man_standing_fsm()
    game_state.add_data("arena", arena)
    game_state.add_data("player_chain", player_chain)
    game_state.add_data("jumon_pick_pool", [get_meeple_by_name("Jumon5")])

    arena.place_unit_at(get_meeple_by_name("NeutralJumon1"), Position(0, 0))

    while True:
        connection, address = server_socket.accept()
        send_gamestate_to_client(connection, game_state)
        connection.close()

    server_socket.close()
