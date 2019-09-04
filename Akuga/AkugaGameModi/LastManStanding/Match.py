import queue
import logging
import socket
from time import sleep

from Akuga.AkugaGameModi.Player import (Player, NeutralPlayer)
from Akuga.AkugaGameModi.PlayerChain import PlayerChain
from Akuga.AkugaGameModi.LastManStanding.ArenaCreator import create_arena
import Akuga.AkugaGameModi.LastManStanding.AkugaStateMachiene as AkugaStateMachiene
import Akuga.AkugaGameModi.MeepleDict as MeepleDict
from Akuga.AkugaGameModi.GlobalDefinitions import USER_DBS_ADDRESS
from Akuga.AkugaGameModi.LastManStanding.GlobalDefinitions import (
    BOARD_WIDTH,
    BOARD_HEIGHT,
    MIN_TILE_BONUS,
    MAX_TILE_BONUS,
    SECONDS_PER_TURN,
    CREDITS_PER_WIN)
from Akuga.AkugaGameModi.NetworkProtocoll import (
    SocketClosed,
    callback_recv_packet,
    handle_match_connection,
    send_gamestate_to_client,
    send_packet,
    propagate_message)
from Akuga.EventDefinitions import (
    Event,
    NOEVENT,
    PACKET_PARSER_ERROR_EVENT,
    TURN_ENDS,
    MATCH_IS_DRAWN,
    PLAYER_HAS_WON,
    MESSAGE)
from Akuga.JumonSet import (serialize_set_to_list, get_set_size)
from Akuga.User import User


running = True
logger = logging.getLogger(__name__)


def check_set_for_lms(active_set):
    """
    Checks if a set is legal for the lms mode
    Every jumon is allowed exactly three times
    and a set must contain exactly seven jumons
    """
    if get_set_size(active_set) != 7:
        print('Invalid set size')
        return False
    for record in active_set.items():
        if record[1] > 3:
            print('To many jumons of the same type')
            return False
    return True


def build_last_man_standing_game_state(player_chain, jumon_sets,
        userdbs_connection, _queue, options={}):
    # Build the arena
    arena = create_arena(BOARD_WIDTH,
                        BOARD_HEIGHT,
                        MIN_TILE_BONUS,
                        MAX_TILE_BONUS)
    # Create the jumon pick pool out of the users active sets
    # Every jumon in the match will have a unique id
    jumon_id = 0
    jumon_pick_pool = []
    # Initialise the JUMON_NAME_CONSTRUCTOR_DICT
    MeepleDict.initialise_jumon_name_constructor_dict(userdbs_connection)
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
                MeepleDict.JUMON_NAME_CONSTRUCTOR_DICT[jumon_name](jumon_id))
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


def handle_fsm_response(event, game_mode, game_state,
        users, userdbs_connection):
    '''
    This function handles the events enqueued by the fsm,
    e.g. TURN_END, PLAYER_HAS_WON, MESSAGE...
    '''
    global running
    if event == PLAYER_HAS_WON:
        # Leave the main loop
        running = False
        victor_name = event.victor.name
        logger.info("Player: " + victor_name + " has won!\n")
        # If the match is not drawn add a victory or loose to the userstats
        if victor_name is not None:
            # Go through all users and add a win or a loose
            for user in users:
                if user.name == victor_name:
                    send_packet(userdbs_connection,
                        ["ADD_WIN", user.name, game_mode])
                    userdbs_connection.recv(128)
                    # Also reward the victor with ingame cash
                    send_packet(userdbs_connection, ["REWARD_USER",
                        user.name, CREDITS_PER_WIN])
                    userdbs_connection.recv(128)
                else:
                    send_packet(userdbs_connection,
                        ["ADD_LOOSE", user.name, game_mode])
                    userdbs_connection.recv(128)
        # Signal the end of the match and the victor
        propagate_message(Event(MESSAGE, users=users,
            tokens=['MATCH_RESULT', victor_name]))
        propagate_message(Event(MESSAGE, users=users, tokens=['MATCH_END']))

    if event == MATCH_IS_DRAWN:
        # If the match is drawn only log it and
        # leave the main loop
        running = False
        logger.info("Match is drawn!\n")

    if event == TURN_ENDS:
        # If a turn ends the game_state has to
        # be propagated to all users
        logger.info("Propagating game state\n")
        send_gamestate_to_client(users, game_state)

    if event == PACKET_PARSER_ERROR_EVENT:
        # Print the event msg but ignore the packet
        logger.info("Packet Parser Error: " + event.msg + "\n")

    if event == MESSAGE:
        # Send a message to a list of users
        # specified in the message event
        propagate_message(event)


def match_server(game_mode, users, options={}):
    """
    The actual game runs here and is propagated to the users
    game_mode: string
    users: list of user instances
    options: A dictionary with options, not used yet
    """
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

    userdbs_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        userdbs_connection.connect(USER_DBS_ADDRESS)
    except ConnectionRefusedError:
        logger.info('Cant connect to akuga database server')
        return -1

    # Get the active jumon sets as a list
    jumon_sets = []
    for user in users:
        jumon_sets.append(user.active_set)

    game_state = None
    if game_mode == "lms":
        logger.info("Game Mode: LastManStanding\n")
        game_state = build_last_man_standing_game_state(player_chain,
                jumon_sets, userdbs_connection, _queue, options)
    else:
        logger.info("Game Mode: Unknown...Terminating\n")
        return

    # Set seconds per turn to be the timeout for all user connections
    for user in users:
        user.connection.settimeout(SECONDS_PER_TURN)

    # Signal the clients that the match starts
    propagate_message(Event(MESSAGE, users=users,
        tokens=['MATCH_START', game_mode]))

    # Propagate the name of all jumons and their ids
    add_jumon_itevent = Event(MESSAGE,
        players=game_state.player_chain.get_players())
    for jumon in game_state.jumon_pick_pool:
        add_jumon_itevent.tokens = ['ADD_JUMON_ITEVENT', jumon.name, jumon.id]
        propagate_message(add_jumon_itevent)

    # Initially propagate the game state
    logger.info("Start match between" + str(player_chain) + "\n")
    logger.info("Propagating game state\n")
    send_gamestate_to_client(users, game_state)

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
                # If the client has disconnected just wait for a second
                # The reconnect attempt is handeld in the game server
                sleep(1)
        # Get an event from the queue and mimic the pygame event behaviour
        try:
            event = _queue.get_nowait()
        except queue.Empty:
            event = Event(NOEVENT)

        # Handle the events which are not handeld by the gamestate itself
        handle_fsm_response(event, game_mode, game_state,
            users, userdbs_connection)
        # Run the rule building state machiene
        game_state.run(event)
        game_state.arena.print_out()

    # Looks weird, but this code block is inside the MatchServer function
    # but outside the matches main loop
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
    set1 = {'Blauta': 1, 'Plodher': 1}
    set2 = {'Blauta': 1, 'Plodher': 1}
    # Create both users with only the first jumon set specified
    # Their dont need a collection cause the set if checked for
    # legality at the game server side
    users = [User('lyding', 'abc', 0, [], set1, [], [], None, None),
             User('lyding2', 'abc', 0, [], set2, [], [], None, None)]
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
