import socket
from json import (loads, dumps, JSONDecodeError)
from Akuga.AkugaGameModi.Position import Position
from Akuga.EventDefinitions import (Event,
                                    SUMMON_JUMON_EVENT,
                                    SELECT_JUMON_TO_MOVE_EVENT,
                                    SELECT_JUMON_TO_SPECIAL_MOVE_EVENT,
                                    PICK_JUMON_EVENT,
                                    PACKET_PARSER_ERROR_EVENT,
                                    TIMEOUT_EVENT,
                                    MESSAGE)


class SocketClosed(Exception):
    '''
    The socket module does not raise an error, if the foreign site
    closes the socket unexpectatly, the SocketClosed error will be raised
    to signal this situation
    '''
    pass


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
                raise SocketClosed()
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


def callback_recv_packet(communicator, nbytes, callback, args):
    """
    Receive a packet and invoke the callback function with the
    received packet and args as arguments
    """
    try:
        packet = communicator.recv_packet()
    except socket.timeout:
        # If the socket runs into a timeout the time a user has to make
        # a decision has passed, so construct a packet which will trigger
        # the timeout branch within the rule building fsm
        packet = ["TIMEOUT"]
    callback(packet, *args)


def propagate_message(message_event):
    '''
    Use the send_packet function to send a packet made out of tokens to all
    users specified in the message_event.
    Therefor the message_event has to provide:
    users: a list of user instances
    players: can be specified instead of the users
    tokens: a list of tokens building the packet

    Broken connections will be ignored as timeout and reconnects are
    handeld elsewhere in the code
    '''
    try:
        users = message_event.users
    except AttributeError:
        # If no users are provided check if players are provided
        # and extract the list of users from the player list
        users = list(map(lambda x: x.user, message_event.players))
    tokens = message_event.tokens
    for user in users:
        try:
            user.communicator.send_packet(tokens)
        except IOError:
            # If the connection is broken just do nothing it will be
            # handeld elsewhere in the code
            pass


def handle_match_connection(tokens, queue, jumons_in_play):
    """
    Receives a package from connection with a timeout of the defined
    seconds per turn. If the socket times out the current player is killed.
    The same is true if an error occurs while parsing the packet.
    """
    if tokens[0] == "PICK_JUMON" and len(tokens) >= 2:
        """
        Handles a pick jumon command
        PICK_JUMON $id_of_the_jumon_to_pick
        """
        try:
            jumon = jumons_in_play[int(tokens[1])]
        except (KeyError, ValueError):
            event = Event(PACKET_PARSER_ERROR_EVENT,
                    msg="Invalid Meeple")
            queue.put(event)
            return
        jumon_pick_event = Event(PICK_JUMON_EVENT,
                jumon=jumon)
        queue.put(jumon_pick_event)
    if tokens[0] == "SUMMON_JUMON" and len(tokens) >= 2:
        """
        Handles a summon jumon command
        SUMMON_JUMON $id_of_the_jumon_to_summon
        """
        try:
            jumon = jumons_in_play[int(tokens[1])]
        except (KeyError, ValueError):
            event = Event(PACKET_PARSER_ERROR_EVENT,
                    msg="Invalid Meeple")
            queue.put(event)
            return
        jumon = Event(SUMMON_JUMON_EVENT,
                jumon=jumon)
        queue.put(jumon)

    if tokens[0] == "MOVE_JUMON" and len(tokens) >= 3:
        """
        Handles a move jumon command
        MOVE_JUMON $id $target_position
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
            event = Event(PACKET_PARSER_ERROR_EVENT,
                    msg="Invalid Position Data")
            queue.put(event)
            return
        # Get the jumon to move by its id
        try:
            jumon = jumons_in_play[int(tokens[1])]
        except (KeyError, ValueError):
            event = Event(PACKET_PARSER_ERROR_EVENT,
                    msg="Invalid Meeple")
            queue.put(event)
            return
        # If no error occured the event can be thrown
        jumon_move_event = Event(SELECT_JUMON_TO_MOVE_EVENT,
                jumon=jumon,
                current_position=jumon.get_position(),
                target_position=Position(position_x, position_y))
        queue.put(jumon_move_event)

    if tokens[0] == "SPECIAL_MOVE_JUMON" and len(tokens) >= 3:
        """
        Handles a move jumon command
        MOVE_JUMON $id $target_position
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
            event = Event(PACKET_PARSER_ERROR_EVENT,
                    msg="Invalid Position Data")
            queue.put(event)
            return
        # Get the jumon to move by its id
        try:
            jumon = jumons_in_play[int(tokens[1])]
        except (KeyError, ValueError):
            event = Event(PACKET_PARSER_ERROR_EVENT,
                    msg="Invalid Meeple")
            queue.put(event)
            return
        # If no error occured the event can be thrown
        jumon_special_move_event = Event(
            SELECT_JUMON_TO_SPECIAL_MOVE_EVENT,
            jumon=jumon,
            current_position=jumon.get_position(),
            target_position=Position(position_x, position_y))
        queue.put(jumon_special_move_event)

    # Non user event which are created on the server side
    # If the connection timed out enqueue a timeout event
    # to go through the timeout state branch in the rule building fsm
    if tokens[0] == "TIMEOUT":
        event = Event(TIMEOUT_EVENT)
        queue.put(event)
        return


def send_gamestate_to_client(users, game_state):
    """
    Send all neccessary data from the server game state to build the client
    game state. The client game state is an excerpt from the state machiene
    as some data should be hidden or is not necessary for the match client
    """
    # First of all send the pick pool
    pick_pool_data_tokens = ["PICK_POOL_DATA"]
    for jumon in game_state.jumon_pick_pool:
        """
        Send the id of the jumon and the
        id of its equipment if there is one
        """
        pick_pool_data_tokens.append((jumon.id, jumon.equipment.id
            if jumon.equipment is not None
            else ""))
    propagate_message(Event(MESSAGE, users=users,
        tokens=pick_pool_data_tokens))

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
            pld_jumons_to_summon_token.append((jumon.id, jumon.equipment.id
                if jumon.equipment is not None
                else ""))
        # Go through all summoned jumons
        for jumon in player.summoned_jumons:
            pld_summoned_jumons.append((jumon.id, jumon.equipment.id
                if jumon.equipment is not None
                else ""))
        # Send the data
        propagate_message(Event(MESSAGE, users=users,
            tokens=pld_jumons_to_summon_token))
        propagate_message(Event(MESSAGE, users=users,
            tokens=pld_summoned_jumons))

    # Now go through all tiles of the arena and send the meeple occupying
    # this tile
    # packet format: cmd, (width, height), meeple1, meeple2, ... meepleN, END
    packet_tokens = [
        "ARENA_DATA",
        (game_state.arena.board_width, game_state.arena.board_height)]
    # Go through all tiles of the arena and append
    # the ids of the occupying meeple
    for y in range(game_state.arena.board_height):
        for x in range(game_state.arena.board_width):
            meeple = game_state.arena.get_unit_at(Position(x, y))
            packet_tokens.append(meeple.id if meeple is not None else "")
    propagate_message(Event(MESSAGE, users=users, tokens=packet_tokens))

    # Now go through all jumons summoned and send the interferences
    # The interferences has to be sent even if there are none to clear
    # the interferences if there where one during the last turn
    for player in game_state.player_chain.get_players():
        for jumon in player.summoned_jumons:
            # Both interferences are send as a complete dict
            # They can be parsed using the ast.literal_eval function
            nonpersistent_interference_tokens = [
                'JUMON_NONPERSISTENT_INTERFERENCE',
                jumon.id,
                jumon.nonpersistent_interf]
            persistent_interference_tokens = [
                'JUMON_PERSISTENT_INTERFERENCE',
                jumon.id,
                jumon.persistent_interf]
            # Send the packets
            propagate_message(Event(MESSAGE, users=users,
                tokens=nonpersistent_interference_tokens))
            propagate_message(Event(MESSAGE, users=users,
                tokens=persistent_interference_tokens))
    # Now send the name of the current player
    propagate_message(Event(MESSAGE, users=users,
        tokens=['CURRENT_PLAYER',
                game_state.player_chain.get_current_player().name]))
