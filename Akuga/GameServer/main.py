import queue
import socket
import logging
from functools import reduce
from threading import Thread
from Akuga.MatchServer.MatchServer import match_server
from Akuga.User import user_from_database_response
from Akuga.GameServer.GlobalDefinitions import (
    SERVER_ADDRESS,
    USER_DBS_ADDRESS,
    MAX_ACTIVE_CONNECTIONS,
    START_CREDITS)
from Akuga.GameServer.Network import (
    recv_packet,
    send_packet,
    receive_dbs_response)
from time import sleep


def handle_client(connection, client_address,
                  lms_queue, amm_queue, active_users):
    """
    Handles the connection of a user (the connection as well as the
    client address is stored within the user instance)
    """
    # Connect to the user database
    userdb_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    userdb_connection.connect(USER_DBS_ADDRESS)
    print("In handle client thread!")
    # The instance of the user: None until a succsefully log in
    user = None
    while True:
        if user is None:
            """
            If the user is not logged in only logging in and register
            commands are allowed
            """
            # Receive a packet
            try:
                tokens = recv_packet(connection, 512)
            except socket.error:
                connection.close()
                logger.info("Connection error")
                # If the user was logged which means part of the active user list
                # remove per from it so per can log in again
                if user is not None:
                    active_users.remove(user.name)
                break

            if tokens[0] == "REGISTER_USER" and len(tokens) >= 3:
                """
                Register the user with pers username and pass hash
                """
                username = tokens[1]
                pass_hash = tokens[2]
                # Check if the username is free
                send_packet(userdb_connection, ["CHECK_USERNAME", username])
                response, error = receive_dbs_response(userdb_connection,
                        512)
                if response is None:
                    """
                    If the response is None an error occured
                    (like inalid chars) send the error msg to the  client
                    """
                    logger.info("Database error: " + error)
                    send_packet(connection, ["ERROR", error])
                elif len(response) > 0:
                    logger.info("User: " + username + " already exists")
                    send_packet(connection, ["ERROR",
                        "User: " + username + " already exists"])
                else:
                    # If the username is free the user can be registeres
                    # Therefor the names of all basic jumons have to be
                    # requested as the user will start with all basic jumons
                    # in pers collection
                    send_packet(userdb_connection, ["GET_BASIC_JUMON_NAMES"])
                    response, error = receive_dbs_response(userdb_connection,
                        512)
                    # The python list stores tuples instead of the strings
                    # itself so their have to be removed
                    jumon_collection = list(map(lambda x: x[0],
                        response))
                    # Now the list only stores jumon names to it can be
                    # reduced to a string of ',' delimited jumon names
                    # to register the user
                    jumon_collection = reduce(lambda x, y: x + ',' + y,
                        jumon_collection)
                    send_packet(userdb_connection, ["REGISTER_USER",
                        username, pass_hash, START_CREDITS, jumon_collection])
                    response, error = receive_dbs_response(userdb_connection,
                        512)
                    if response is None:
                        """
                        If the response is None an error occured, send the
                        error msg to the client
                        """
                        logger.info("Database error: " + error)
                        send_packet(connection, ["ERROR", error])
                    else:
                        """
                        If no error occured send success
                        """
                        logger.info("Register user: " + username)
                        send_packet(connection, ["SUCCESSFULLY_REGISTERED"])
            if tokens[0] == "LOG_IN" and len(tokens) >= 3:
                """
                Check the credentials of the user
                """
                username = tokens[1]
                pass_hash = tokens[2]
                send_packet(userdb_connection,
                    ["CHECK_CREDENTIALS", username, pass_hash])
                response, error = receive_dbs_response(userdb_connection,
                    512)
                if response is None:
                    # An error occured, pass the error to the client
                    logger.info("Database error: " + error)
                    send_packet(connection, ["ERROR", error])
                if len(response) > 0 and username not in active_users:
                    """
                    If there is a result (there should never be one than more
                    but keep > 0 for safety) the credentials are correct.
                    Also the username doesnt have to occure in the list
                    of usernames already logged in so users cant log in
                    multiple times
                    """
                    # Request the whole user structure
                    send_packet(userdb_connection, ['GET_USER_BY_NAME', username])
                    response, error = receive_dbs_response(userdb_connection,
                        512)
                    if response is None:
                        logger.info("Unexpected error occured: " + error)
                        send_packet(connection, ["ERROR", error])
                        continue
                    # Create a user instance from the database response
                    user = user_from_database_response(response, connection,
                        client_address)
                    print(str(user))

                    # Add the user to the active users so per cant
                    # log in a second time
                    active_users.append(username)
                    logger.info("Logging in: " + username)
                    send_packet(connection, ["SUCCESSFULLY_LOGGED_IN"])
        elif user.in_play is False:
            """
            If the user is logged in an not playing a match
            """
            # Receive a packet as long as the user is not in play
            try:
                tokens = recv_packet(connection, 512)
            except socket.error:
                connection.close()
                logger.info("Connection error")
                # If the user was logged which means part of the active user list
                # remove per from it so per can log in again
                if user is not None:
                    active_users.remove(user.name)
                break
            print("logged in and not in play")
            if tokens[0] == 'ENQUEUE_FOR_MATCH' and len(tokens) >= 3:
                """
                Enqueue the user in the queue for the specified game mode
                """
                try:
                    active_set = int(tokens[2])
                    if active_set < 0 or active_set > 2:
                        raise ValueError
                except ValueError:
                    send_packet(connection, ['ERROR',
                        'One of the parameters where malformed'])
                    logger.info('One of the parameters where malformed')
                    logger.info('Received from: ' + str(client_address))
                    continue
                if tokens[1] == 'lms':
                    logger.info("Enqueue " + user.name + "for lms")
                    lms_queue.put((user, active_set))
                    send_packet(connection, ["SUCCESFULLY_ENQUEUED", "lms"])
                elif tokens[1] == 'amm':
                    logger.info("Enqueue " + user.name + "for amm")
                    amm_queue.put((user, active_set))
                    send_packet(connection, ["SUCCESFULLY_ENQUEUED", "amm"])
                else:
                    logger.info("Invalid game mode: " + tokens[1])
                    send_packet(connection, ["ERROR", "Invalid game mode: "
                        + tokens[1]])
        else:
            """
            If the user is logged in but currently playing a match,
            do nothing, not even receive a packet as the connection
            is temporaly unavailable. It is used by a handle_match
            thread now.
            """
            print('From the GameServer: Currently in play')
            sleep(1)
            pass


def handle_lms_queue(lms_queue):
    """
    Invoke a lms match between the two uppermost users
    """
    while True:
        # Get two users from the queue
        user1, user1_active_set = lms_queue.get()
        user1.in_play = True
        user2, user2_active_set = lms_queue.get()
        user2.in_play = True
        logger.info("Got two user for a lms match")
        logger.info("Start MatchServer subprocess")
        match_server_thread = Thread(target=match_server, args=('lms',
            [(user1, user1_active_set), (user2, user2_active_set)], None))
        match_server_thread.start()
        logger.info("Started MatchServer subprocess")
        # Signal that the users has been processed
        lms_queue.task_done()
        lms_queue.task_done()


def handle_amm_queue(amm_queue):
    """
    Invoke a amm match between the two uppermost users
    """
    while True:
        # Get two users from the queue
        user1, user1_active_set = amm_queue.get()
        user1.in_play = True
        user2, user2_active_set = amm_queue.get()
        user2.in_play = True
        logger.info("Got two user for an amm match")
        logger.info("Start MatchServer subprocess")
        match_server_thread = Thread(target=match_server, args=('amm',
            [(user1, user1_active_set), (user2, user2_active_set)], None))
        match_server_thread.start()
        logger.info("Started MatchServer subprocess")
        # Signal that the users has been processed
        amm_queue.task_done()
        amm_queue.task_done()


if __name__ == '__main__':
    # Create a logger
    logging.basicConfig(filename='Akuga.log', level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Listen on the server address
    logger.info("Create a server socket")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(SERVER_ADDRESS)
    server_socket.listen(MAX_ACTIVE_CONNECTIONS)
    logger.info("Created server socket, waiting for: "
        + str(MAX_ACTIVE_CONNECTIONS))

    # The game mode queues
    lms_queue = queue.Queue()
    amm_queue = queue.Queue()

    # A list of all usernames currently logged in
    active_users = []

    # Create and start the handle game mode queue threads for each game mode
    logger.info("Start handle_gamemode_queue threads as daemons")
    handle_lms_queue_thread = Thread(target=handle_lms_queue, args=(lms_queue,))
    handle_amm_queue_thread = Thread(target=handle_amm_queue, args=(amm_queue,))
    handle_lms_queue_thread.daemon = True
    handle_amm_queue_thread.daemon = True
    handle_lms_queue_thread.start()
    handle_amm_queue_thread.start()
    logger.info("Started handle_gamemode_queue threads as daemons")
    logger.info("Enter server loop")
    while True:
        try:
            connection, client_address = server_socket.accept()
        except socket.error:
            logger.info("Error while accepting connections")
            break
        handle_client_thread = Thread(target=handle_client,
            args=(connection, client_address, lms_queue, amm_queue, active_users))
        handle_client_thread.start()
    logger.info("Leave server loop")
    logger.info("Close the server socket, terminate programm")
    server_socket.close()
