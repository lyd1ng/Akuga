import queue
import socket
import random
import logging
from hashlib import md5
from threading import Thread
from multiprocessing import Process
from Akuga.MatchServer.MatchServer import match_server
from Akuga.GameServer.User import User
from Akuga.GameServer.GlobalDefinitions import (
    SERVER_ADDRESS,
    USER_DBS_ADDRESS,
    MAX_ACTIVE_CONNECTIONS)
from Akuga.GameServer.Network import (
    whitelist,
    send_packet,
    receive_dbs_response,
    send_password_to_client_email)


def generate_random_password():
    """
    Returns a random password which is 10 chars long
    """
    password = ""
    for i in range(10):
        password += whitelist[random.randint(0, len(whitelist) - 1)]
    return password


def handle_client(connection, client_address, lms_queue, amm_queue):
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
        try:
            packet = connection.recv(512).decode('utf-8')
        except socket.error:
            connection.close()
            logger.info("Connection error")
            break
        if not packet:
            connection.close()
            logger.info("Connection closed")
            break
        tokens = packet.split(":")
        if user is None:
            """
            If the user is not logged in only logging in and register
            commands are allowed
            """
            if tokens[0] == "REGISTER_USER" and len(tokens) >= 3:
                """
                Register the user with a generated password and email
                the user the password
                """
                username = tokens[1]
                email = tokens[2]
                print("received a 'register_user'")
                # Check if the username is free
                send_packet(userdb_connection, ["CHECK_USERNAME", username])
                response, error = receive_dbs_response(userdb_connection)
                print("Received a response from the udbs")
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
                    # If the username is free generate a password
                    # and register the user
                    password = generate_random_password()
                    pass_hash = md5(password.encode('utf-8')).hexdigest()
                    # Register the user with pers username and pers hash
                    send_packet(userdb_connection, ["REGISTER_USER",
                        username, pass_hash])
                    response, error = receive_dbs_response(userdb_connection)
                    if response is None:
                        """
                        If the response is None an error occured, send the
                        error msg to the client
                        """
                        logger.info("Database error: " + error)
                        send_packet(connection, ["ERROR", error])
                    else:
                        """
                        If no error occured email the client
                        """
                        logger.info("Register user: " + username)
                        send_password_to_client_email(username,
                            password, email)
                        send_packet(connection, ["SUCCESSFULLY_REGISTERED"])
            if tokens[0] == "LOG_IN" and len(tokens) >= 3:
                """
                Check the credentials of the user
                """
                username = tokens[1]
                pass_hash = tokens[2]
                send_packet(userdb_connection,
                    ["CHECK_CREDENTIALS", username, pass_hash])
                response, error = receive_dbs_response(userdb_connection)
                if response is None:
                    # An error occured, pass the error to the client
                    logger.info("Database error: " + error)
                    send_packet(connection, ["ERROR", error])
                if len(response) > 0:
                    """
                    If there is a result (there should never be one than more)
                    But keep > 0 for safety
                    """
                    # Unlock the logged in functionalities
                    user = User(username, pass_hash,
                        connection, client_address)
                    logger.info("Logging in: " + username)
                    send_packet(connection, ["SUCCESSFULLY_LOGGED_IN"])
        elif user.in_play is False:
            """
            If the user is logged in an not playing a match
            """
            print("logged in and not in play")
            if tokens[0] == 'ENQUEUE_FOR_MATCH' and len(tokens) >= 2:
                """
                Enqueue the user in the queue for the specified game mode
                """
                if tokens[1] == 'lms':
                    logger.info("Enqueue " + user.name + "for lms")
                    lms_queue.put(user)
                    send_packet(connection, ["SUCCESFULLY_ENQUEUED", "lms"])
                elif tokens[1] == 'amm':
                    logger.info("Enqueue " + user.name + "for amm")
                    amm_queue.put(user)
                    send_packet(connection, ["SUCCESFULLY_ENQUEUED", "amm"])
                else:
                    logger.info("Invalid game mode: " + tokens[1])
                    send_packet(connection, ["ERROR", "Invalid game mode: "
                        + tokens[1]])
        else:
            """
            If the user is logged in but currently playing a match,
            do nothing
            """
            pass


def handle_lms_queue(lms_queue):
    """
    Invoke a lms match between the two uppermost users
    """
    # Get two users from the queue
    user1 = lms_queue.get()
    user1.in_play = True
    user2 = lms_queue.get()
    user2.in_play = True
    logger.info("Got two user for a lms match")
    users = {user1.name: user1.connection, user2.name: user2.connection}
    logger.info("Start MatchServer subprocess")
    MatchServerProcess = Process(target=match_server, args=('lms', users, None))
    MatchServerProcess.start()
    logger.info("Started MatchServer subprocess")
    # Signal that the users has been processed
    queue.task_done()
    queue.task_done()


def handle_amm_queue(amm_queue):
    """
    Invoke a amm match between the two uppermost users
    """
    # Get two users from the queue
    user1 = amm_queue.get()
    user1.in_play = True
    user2 = amm_queue.get()
    user2.in_play = True
    logger.info("Got two user for an amm match")
    users = {user1.name: user1.connection, user2.name: user2.connection}
    logger.info("Start MatchServer subprocess")
    MatchServerProcess = Process(target=match_server, args=('amm', users, None))
    MatchServerProcess.start()
    logger.info("Started MatchServer subprocess")
    # Signal that the users has been processed
    queue.task_done()
    queue.task_done()


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
            args=(connection, client_address, lms_queue, amm_queue))
        handle_client_thread.start()
    logger.info("Leave server loop")
    logger.info("Close the server socket, terminate programm")
    server_socket.close()
