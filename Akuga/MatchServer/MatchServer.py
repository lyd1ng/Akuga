import pygame
import queue
import logging
import socket

from Akuga.MatchServer.Player import (Player, NeutralPlayer)
from Akuga.MatchServer.PlayerChain import PlayerChain
from Akuga.MatchServer.ArenaCreator import create_arena
from Akuga.MatchServer.MeepleDict import (get_neutral_meeples, get_not_neutral_meeples)
from Akuga.MatchServer import GlobalDefinitions
import Akuga.MatchServer.AkugaStateMachiene as AkugaStateMachiene
from Akuga.MatchServer.NetworkProtocoll import (
    callback_recv_packet,
    handle_match_connection,
    send_gamestate_to_client,
    send_packet)
from Akuga.EventDefinitions import (
    PACKET_PARSER_ERROR_EVENT,
    TURN_ENDS,
    MATCH_IS_DRAWN,
    PLAYER_HAS_WON)
from Akuga.User import User


logger = logging.getLogger(__name__)


def find_user_by_name(username, users):
    """
    Find an instance of a user in users by pers name
    """
    result = [user for user in users if user.name == username]
    if len(result) == 1:
        return result[0]
    return None


def build_last_man_standing_game_state(player_chain, _queue, options={}):
    # Build the arena
    arena = create_arena(GlobalDefinitions.BOARD_WIDTH,
                        GlobalDefinitions.BOARD_HEIGHT,
                        GlobalDefinitions.MIN_TILE_BONUS,
                        GlobalDefinitions.MAX_TILE_BONUS)
    # Add a neutral player to the player chain
    neutral_player = NeutralPlayer(arena)
    neutral_player.set_jumons_to_summon(get_neutral_meeples(1))
    neutral_player.summon_jumons()
    player_chain.insert_player(neutral_player)
    # Build the state machiene which represents the whole game state
    game_state = AkugaStateMachiene.create_last_man_standing_fsm()
    game_state.add_data("queue", _queue)
    game_state.add_data("arena", arena)
    game_state.add_data("player_chain", player_chain)
    game_state.add_data("jumon_pick_pool", get_not_neutral_meeples(2))
    game_state.add_data("post_turn_state_changes", [])
    return game_state


def match_server(game_mode, users, options={}):
    """
    The actual game runs here and is propagated to the users
    game_mode: string
    users: list of (player_name, player_connection)
    options: A dictionary with options, not used yet
    """
    # Will hold the victor at the end
    victor_name = None
    # Set all players to be in play
    # This will deactivate the game server connection
    for user in users:
        user.in_play = True
    # Build the player chain
    player_name_list = list(map(lambda x: x.name, users))
    player1 = Player(player_name_list[0])
    player2 = Player(player_name_list[1])
    player_chain = PlayerChain(player1, player2)
    for i in range(2, len(player_name_list)):
        player_chain.insert_player(Player(player_name_list[i]))
    # Create the queue
    _queue = queue.Queue()

    game_state = None
    if game_mode == "lms":
        logger.info("Game Mode: LastManStanding\n")
        game_state = build_last_man_standing_game_state(player_chain,
                _queue, options)
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
            user = find_user_by_name(game_state.player_chain.
                get_current_player().name, users)
            callback_recv_packet(user.connection, 512, handle_match_connection,
                [_queue])
        # Get an event from the queue and mimic the pygame event behaviour
        try:
            event = _queue.get_nowait()
        except queue.Empty:
            event = pygame.event.Event(pygame.NOEVENT)

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
    users = [User('lyding', 'magical_hash', None, None),
             User('lyding2', 'magical_hash', None, None)]

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
