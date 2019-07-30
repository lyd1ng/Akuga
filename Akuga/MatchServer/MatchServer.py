import queue
import logging
import socket
from time import sleep

from Akuga.MatchServer.Player import (Player, NeutralPlayer)
from Akuga.MatchServer.PlayerChain import PlayerChain
from Akuga.MatchServer.ArenaCreator import create_arena
from Akuga.MatchServer.MeepleDict import JUMON_NAME_CONSTRUCTOR_DICT
from Akuga.MatchServer import GlobalDefinitions
import Akuga.MatchServer.AkugaStateMachiene as AkugaStateMachiene
from Akuga.MatchServer.NetworkProtocoll import (
    SocketClosed,
    callback_recv_packet,
    handle_match_connection,
    send_gamestate_to_client,
    send_packet)
from Akuga.EventDefinitions import (
    Event,
    NOEVENT,
    PACKET_PARSER_ERROR_EVENT,
    TURN_ENDS,
    MATCH_IS_DRAWN,
    PLAYER_HAS_WON)
from Akuga.JumonSet import serialize_set_to_list
from Akuga.User import User


logger = logging.getLogger(__name__)


def build_last_man_standing_game_state(player_chain, jumon_sets,
        _queue, options={}):
    # Build the arena
    arena = create_arena(GlobalDefinitions.BOARD_WIDTH,
                        GlobalDefinitions.BOARD_HEIGHT,
                        GlobalDefinitions.MIN_TILE_BONUS,
                        GlobalDefinitions.MAX_TILE_BONUS)
    # Create the jumon pick pool out of the users active sets
    # Every jumon in the match will have a unique id
    jumon_id = 0
    jumon_pick_pool = []
    # Go through all jumon sets
    for jumon_set in jumon_sets:
        # Convert the set to a list for easier processing
        jumon_set_as_name_list = serialize_set_to_list(jumon_set)
        # Now generate the correct jumon instance for every name
        # in the list of jumon names representing the set of a player
        for jumon_name in jumon_set_as_name_list:
            # The JUMON_NAME_CONSTRUCTOR_DICT is a dictionary storing
            # the right constructor under the name of the jumon, only the
            # id has to be passed
            jumon_pick_pool.append(
                JUMON_NAME_CONSTRUCTOR_DICT[jumon_name](jumon_id))
            # Simply increment the jumon id to make sure every jumon
            # has a unique id
            jumon_id += 1

    # Beside the jumon pick pool a dictionary mapping the id of a jumon to
    # its instance is needed. So go through the pick pool and add every jumon
    # to this dictionary when a neutral player is added all of its jumons
    # should be added to this dictionary as well
    jumons_in_play = {}
    for jumon in jumon_pick_pool:
        jumons_in_play[jumon.id] = jumon

    # Build the state machiene which represents the whole game state
    game_state = AkugaStateMachiene.create_last_man_standing_fsm()
    game_state.add_data("queue", _queue)
    game_state.add_data("arena", arena)
    game_state.add_data("player_chain", player_chain)
    game_state.add_data("jumons_in_play", jumons_in_play)
    game_state.add_data("jumon_pick_pool", jumon_pick_pool)
    game_state.add_data("post_turn_state_changes", [])
    game_state.add_data("timeout_timer", 0)
    game_state.add_data("old_time", 0)
    game_state.add_data("current_time", 0)
    print('succsessfully passed the build lms game state function!')
    return game_state


def match_server(game_mode, users, options={}):
    """
    The actual game runs here and is propagated to the users
    game_mode: string
    users: list of user instances
    options: A dictionary with options, not used yet
    """
    # Will hold the victor at the end
    victor_name = None
    # Set all players to be in play
    # This will deactivate the game server connection
    for user in users:
        user.in_play = True
    player1 = Player(users[0])
    player2 = Player(users[1])
    player_chain = PlayerChain(player1, player2)
    for i in range(2, len(users)):
        player_chain.insert_player(Player(users[i]))
    # Create the queue
    _queue = queue.Queue()

    # Get the active jumon sets as a list
    jumon_sets = []
    for user in users:
        jumon_sets.append(user.active_set)

    game_state = None
    if game_mode == "lms":
        logger.info("Game Mode: LastManStanding\n")
        game_state = build_last_man_standing_game_state(player_chain,
                jumon_sets, _queue, options)
    else:
        logger.info("Game Mode: Unknown...Terminating\n")
        return

    # Set seconds per turn to be the timeout for all user connections
    for user in users:
        user.connection.settimeout(GlobalDefinitions.SECONDS_PER_TURN)

    # Signal the clients that the match starts
    for user in users:
        send_packet(user.connection, ["MATCH_START", game_mode])

    # Initially propagate the game state
    logger.info("Start match between" + str(player_chain) + "\n")
    logger.info("Propagating game state\n")
    for user in users:
        send_gamestate_to_client(user.connection, game_state)

    running = True
    while running:
        """
        Receive and handle packets from the current player only
        The handle_match_connection will throw the right event which will
        be handeld by the gamestate statemachiene.
        Only some events have to be handeld here.
        """
        if type(game_state.player_chain.get_current_player())\
                is not NeutralPlayer and\
                game_state.current_state is\
                game_state.wait_for_user_state:
            # Receive packets only from the current user
            user = game_state.player_chain.get_current_player().user
            try:
                callback_recv_packet(user.connection, 512,
                    handle_match_connection,
                    [_queue, game_state.jumons_in_play])
            except SocketClosed:
                # _queue.put(Event(TIMEOUT_EVENT))
                sleep(1)
        # Get an event from the queue and mimic the pygame event behaviour
        try:
            event = _queue.get_nowait()
        except queue.Empty:
            event = Event(NOEVENT)

        game_state.run(event)
        # Handle the events which are not handeld by the gamestate itself
        game_state.arena.print_out()
        if event.type == PACKET_PARSER_ERROR_EVENT:
            # Print the event msg but ignore the packet
            logger.info("Packet Parser Error: " + event.msg + "\n")
        if event.type == TURN_ENDS:
            """
            If a turn ends the game_state has to be propagated to all users
            """
            logger.info("Propagating game state\n")
            for user in users:
                send_gamestate_to_client(user.connection, game_state)

        if event.type == MATCH_IS_DRAWN:
            running = False
            logger.info("Match is drawn!\n")
        if event.type == PLAYER_HAS_WON:
            running = False
            victor_name = event.victor.name
            logger.info("Player: " + victor_name + " has won!\n")

    # If the match is not drawn add a victory or loose to the userstats
    if victor_name is not None:
        userdbs_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            userdbs_connection.connect(GlobalDefinitions.USER_DBS_ADDRESS)
        except ConnectionRefusedError:
            userdbs_connection = None
        # Do nothing if the userdatabase server is unreachable
        if userdbs_connection is not None:
            for user in users:
                logger.info("Logger in player_chain: " + user.name)
                if user.name == victor_name:
                    send_packet(userdbs_connection,
                        ["ADD_WIN", user.name, game_mode])
                    userdbs_connection.recv(128)
                else:
                    send_packet(userdbs_connection,
                        ["ADD_LOOSE", user.name, game_mode])
                    userdbs_connection.recv(128)
            userdbs_connection.close()
    # Signal the end of the match and the victor
    for user in users:
        send_packet(user.connection, ["MATCH_END"])
        send_packet(user.connection, ["MATCH_RESULT", victor_name])

    # Set all players to be out of play
    # This will activate the game server connection
    for user in users:
        user.in_play = False


if __name__ == "__main__":
    logging.basicConfig(filename='MatchServer.log', level=logging.INFO)
    logger = logging.getLogger(__name__)
    import random
    from multiprocessing import Process

    port = random.randint(1000, 4000)
    print("Listening on port: " + str(port))
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', port))
    server_socket.listen(2)

    # Create the two sets the players are going to play with
    set1 = {'Blauta': 3, 'Plodher': 3, 'Steppenlauefer': 1}
    set2 = {'Blauta': 3, 'Plodher': 3, 'Steppenlauefer': 1}
    # Create both users with only the first jumon set specified
    # Their dont need a collection cause the set if checked for
    # legality at the game server side
    users = [User('lyding', 'magical_hash', 0, [], set1, [], [], None, None),
             User('lyding2', 'magical_hash', 0, [], set2, [], [], None, None)]
    # Now set the active set to be the first one
    users[0].active_set = set1
    users[1].active_set = set2

    try:
        print('Waiting for players')
        users[0].connection, _ = server_socket.accept()
        print('Found player1')
        users[1].connection, _ = server_socket.accept()
        print('Found player2')
        print('Start match!')
        match_process = Process(target=match_server,
            args=('lms', users))
        match_process.start()
    except socket.error:
        for connection in users.values():
            connection.close()
    server_socket.close()
