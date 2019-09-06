import queue
import socket
import logging
from functools import reduce
from threading import Thread
from Akuga.AkugaGameModi.LastManStanding.Match import (
    match_server, check_set_for_lms)
from Akuga.User import user_from_database_response
from Akuga.GameServer.GlobalDefinitions import (
    SERVER_ADDRESS,
    USER_DBS_ADDRESS,
    MAX_ACTIVE_CONNECTIONS,
    START_CREDITS)
from Akuga.GameServer.Network import StreamSocketCommunicator
from Akuga.JumonSet import (
    is_subset,
    insert_name,
    jumon_set_from_list)
from time import sleep


def handle_client(communicator, client_address,
                  lms_queue, active_users):
    """
    Handles the connection of a user (the connection as well as the
    client address is stored within the user instance)
    """
    # Connect to the user database
    dbs_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dbs_connection.connect(USER_DBS_ADDRESS)
    dbs_communicator = StreamSocketCommunicator(dbs_connection, 1024)
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
                tokens = communicator.recv_packet()
            except socket.error:
                # This triggers when the user disconects
                connection.close()
                logger.info("Connection error")
                # If the user was logged which means part of the
                # active user list remove per from it so per can log in again
                if user is not None:
                    active_users.remove(user)
                break

            if tokens[0] == "REGISTER_USER" and len(tokens) >= 3:
                """
                Register the user with pers username and pass hash
                """
                username = tokens[1]
                pass_hash = tokens[2]
                # Check if the username is free
                dbs_communicator.send_packet(["CHECK_USERNAME", username])
                response = dbs_communicator.recv_packet()
                if response[0] == 'ERROR':
                    # If an error occured propagate it to the client
                    logger.info("Database error: " + response[1])
                    communicator.send_packet(["ERROR", response[1]])
                elif len(response) > 0:
                    logger.info("User: " + username + " already exists")
                    communicator.send_packet(["ERROR",
                        "User: " + username + " already exists"])
                else:
                    # If the username is free the user can be registeres
                    # Therefor the names of all basic jumons have to be
                    # requested as the user will start with all basic jumons
                    # in pers collection
                    communicator.send_packet(["GET_BASIC_JUMON_NAMES"])
                    response = dbs_communicator.recv_packet()
                    # The python list stores tuples instead of the strings
                    # itself so their have to be removed
                    jumon_collection = list(map(lambda x: x[0],
                        response))
                    # Now the list only stores jumon names to it can be
                    # reduced to a string of ',' delimited jumon names
                    # to register the user
                    jumon_collection = reduce(lambda x, y: x + ',' + y,
                        jumon_collection, '')
                    dbs_communicator.send_packet(["REGISTER_USER",
                        username, pass_hash, START_CREDITS, jumon_collection])
                    response = dbs_communicator.recv_packet()
                    if response[0] == 'ERROR':
                        """
                        If the response is None an error occured, send the
                        error msg to the client
                        """
                        logger.info("Database error: " + response[1])
                        communicator.send_packet(["ERROR", response[1]])
                    else:
                        """
                        If no error occured send success
                        """
                        logger.info("Register user: " + username)
                        communicator.send_packet(["SUCCESS", "registered"])
            if tokens[0] == "LOG_IN" and len(tokens) >= 3:
                """
                Check the credentials of the user
                """
                username = tokens[1]
                pass_hash = tokens[2]
                dbs_communicator.send_packet(
                    ["CHECK_CREDENTIALS", username, pass_hash])
                response = dbs_communicator.recv_packet()
                if response[0] == 'ERROR':
                    # An error occured, pass the error to the client
                    logger.info("Database error: " + response[1])
                    communicator.send_packet(["ERROR", response[1]])
                if len(response) > 0 and username not in\
                        list(map(lambda x: x.name, active_users)):
                    """
                    If there is a result (there should never be one than more
                    but keep > 0 for safety) the credentials are correct.
                    Also the username doesnt have to occure in the list
                    of usernames already logged in so users cant log in
                    multiple times
                    """
                    # Request the whole user structure
                    dbs_communicator.send_packet(
                        ['GET_USER_BY_NAME', username])
                    response = dbs_communicator.recv_packet()
                    if response[0] == 'ERROR':
                        logger.info("Unexpected error occured: " + response[1])
                        communicator.send_packet(["ERROR", response[1]])
                        continue
                    # Create a user instance from the database response
                    user = user_from_database_response(response, connection,
                        client_address)

                    # Add the user to the active users so per cant
                    # log in a second time
                    active_users.append(user)
                    logger.info("Logging in: " + username)
                    communicator.send_packet(["SUCCESS", "logged_in"])
                elif len(response) > 0:
                    """
                    If the user is in the active user list check if per is in
                    play. If the user is in play per disconnected and this
                    is pers reconnection attempt, so just set the user
                    instance to the already stored user instance
                    """
                    # Get the user instance of the given name
                    user_index = list(map(lambda x: x.name, active_users)).\
                        index(username)
                    tmp_user = active_users[user_index]
                    if tmp_user.in_play is True:
                        # This is a reconnect atttempt so update the
                        # connection and the client address of the user
                        # instance
                        tmp_user.connection = connection
                        tmp_user.client_address = client_address
                        logger.info("Logging in: " + username)
                        communicator.send_packet(["SUCCESS", "logged_in"])
                        return
        elif user.in_play is False:
            """
            If the user is logged in an not playing a match
            """
            # Receive a packet as long as the user is not in play
            try:
                tokens = communicator.recv_packet()
            except socket.error:
                connection.close()
                # This triggers if the user disconnects
                logger.info("Connection error")
                # If the user was logged which means part of the
                # active user list remove per from it so per can log in again
                if user is not None:
                    active_users.remove(user)
                break
            if tokens[0] == 'ENQUEUE_FOR_MATCH' and len(tokens) >= 3:
                """
                Enqueue the user in the queue for the specified game mode
                """
                try:
                    active_set_index = int(tokens[2])
                    if active_set_index < 0 or active_set_index > 2:
                        raise ValueError
                except ValueError:
                    communicator.send_packet(
                        ['ERROR', 'One of the parameters where malformed'])
                    logger.info('One of the parameters where malformed')
                    logger.info('Received from: ' + str(client_address))
                    continue
                # At this point int the code it is proofen that the
                # active set index is valid so set the users active set
                user.active_set = user.sets[active_set_index]
                if tokens[1] == 'lms':
                    logger.info("Enqueue " + user.name + "for lms")
                    if not check_set_for_lms(user.active_set):
                        communicator.send_packet(['ERROR', 'Illegal set'])
                        continue
                    # At this point in the code the set is proofed to be valid
                    lms_queue.put(user)
                    communicator.send_packet(["SUCCESS", "enqueued", "lms"])
                else:
                    logger.info("Invalid game mode: " + tokens[1])
                    communicator.send_packet(["ERROR", "Invalid game mode: "
                        + tokens[1]])
            if tokens[0] == "GET_JUMON_NAMES" and len(tokens) >= 1:
                """
                Query the database for all jumons and forward the result
                """
                dbs_communicator.send_packet(["GET_JUMON_NAMES"])
                response = dbs_communicator.recv_packet()
                if response[0] == 'ERROR':
                    communicator.send_packet(['ERROR', response[1]])
                    logger.info("An unexpected error occured: " + response[1])
                    continue
                communicator.send_packet(['SUCCESS', str(response)])
            if tokens[0] == "GET_JUMON_COLLECTION" and len(tokens) >= 1:
                """
                Convert the collection of the user into a ',' seperated
                string and send it to the client
                """
                collection = user.get_collection_serialized()
                communicator.send_packet(['SUCCESS', collection])
            if tokens[0] == "GET_JUMON_SET" and len(tokens) >= 1:
                """
                Convert the requestes jumon set of the user into a ','
                seperated string and send it to the client
                """
                try:
                    index = int(tokens[1])
                    if index < 0 or index > 2:
                        raise ValueError
                except ValueError:
                    logger.info("One of the parameter where malformed")
                    logger.info("Received from: " + str(client_address))
                    communicator.send_packet(
                        ['ERROR', 'One of the paramter where malformed'])
                    continue
                jumon_set = user.get_set_serialized(index)
                communicator.send_packet(['SUCCESS', jumon_set])
            if tokens[0] == "SET_JUMON_SET" and len(tokens) >= 2:
                """
                Receive a jumon set and its index. Update the specified set
                if all jumons in the set are part of the users collection
                """
                try:
                    index = int(tokens[1])
                    if index < 0 or index > 2:
                        raise ValueError
                except ValueError:
                    logger.info("One of the parameter where malformed")
                    logger.info("Received from: " + str(client_address))
                    communicator.send_packet(
                        ['ERROR', 'One of the parameters where malformed'])
                    continue
                # Convert the string into a list of jumon names
                jumon_set = jumon_set_from_list(tokens[2].split(','))
                # Check if all jumons in the set are part of the collection
                if is_subset(jumon_set, user.collection) is False:
                    logger.info('Invalid Set')
                    logger.info('Received from: ' + str(client_address))
                    communicator.send_packet(['ERROR', 'Invalid Set'])
                    continue
                # Set the jumon set
                user.sets[index] = jumon_set
                # And update the user datastructure in the database
                dbs_communicator.send_packet(['UPDATE_USER', user.name,
                    int(user.credits), user.get_collection_serialized(),
                    user.get_set_serialized(0),
                    user.get_set_serialized(1),
                    user.get_set_serialized(2)])
                response = dbs_communicator.recv_packet()
                if response[0] == 'ERROR':
                    logger.info('Unexpected error: ' + response[1])
                    communicator.send_packet(['ERROR', response[1]])
                    continue
                communicator.send_packet(['SUCCESS'])
            if tokens[0] == 'BUY_JUMON' and len(tokens) >= 2:
                """
                If the jumon is not already owned, the jumons exists and the
                user has enough money decrement the credits of the user by
                the jumons price, add the jumon to the collection of the user
                and update the user in the database
                """
                # First, get the jumons datastructure
                dbs_communicator.send_packet(['GET_JUMON_BY_NAME', tokens[1]])
                response = dbs_communicator.recv_packet()
                # If the length of the response tuple is zero
                # the queried jumon doesnt exists
                if response[0] == 'ERROR' or len(response) == 0:
                    logger.info("An error occured getting the jumon." + response[1])
                    logger.info("Received from: " + str(client_address))
                    # If the error message is '' the length
                    # of the tuple was zero cause no jumon was found
                    # State this clearly in the error message
                    error = response[1]
                    if error == '':
                        error = 'Invalid jumonname'
                    communicator.send_packet(connection, ['ERROR', error])
                    continue
                # The price is the 6th element of the tuple so at index 5
                jumon_tuple = response[0]
                jumon_price = jumon_tuple[5]
                if user.credits < jumon_price:
                    """
                    The user cant affort to buy the jumon
                    """
                    communicator.send_packet(['ERROR', 'To expansive'])
                    continue
                # At this point in the code the jumon exists
                # and the user can afford to buy the jumon
                # so decrement the credits by the jumon price, add the jumon
                # to the collection and update the database
                jumon_name = jumon_tuple[0]
                user.credits -= jumon_price
                # Add the jumon to the jumon set
                insert_name(user.collection, jumon_name)
                dbs_communicator.send_packet(['UPDATE_USER',
                    user.name,
                    int(user.credits),
                    user.get_collection_serialized(),
                    user.get_set_serialized(0),
                    user.get_set_serialized(1),
                    user.get_set_serialized(2)])
                response = dbs_communicator.recv_packet()
                if response is None:
                    logger.info('An unexpected error occured: ' + response[1])
                    communicator.send_packet(['ERROR', response[1]])
                    continue
                communicator.send_packet(['SUCCESS', 'Bought jumon'])
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
    # Close the dbs connection
    dbs_connection.close()


def handle_lms_queue(lms_queue):
    """
    Invoke a lms match between the two uppermost users
    """
    while True:
        # Get two users from the queue
        user1 = lms_queue.get()
        user1.in_play = True
        user2 = lms_queue.get()
        user2.in_play = True
        logger.info("Got two user for a lms match")
        logger.info("Start MatchServer subprocess")
        match_server_thread = Thread(target=match_server,
            args=([user1, user2], None))
        match_server_thread.start()
        logger.info("Started MatchServer subprocess")
        # Signal that the users has been processed
        lms_queue.task_done()
        lms_queue.task_done()


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

    # A list of all users currently logged in
    active_users = []

    # Create and start the handle game mode queue threads for each game mode
    logger.info("Start handle_gamemode_queue threads as daemons")
    handle_lms_queue_thread = Thread(target=handle_lms_queue,
        args=(lms_queue,))
    handle_lms_queue_thread.daemon = True
    handle_lms_queue_thread.start()
    logger.info("Started handle_gamemode_queue threads as daemons")
    logger.info("Enter server loop")
    while True:
        try:
            connection, client_address = server_socket.accept()
        except socket.error:
            logger.info("Error while accepting connections")
            break
        # Create a stream socket communicator for the client
        communicator = StreamSocketCommunicator(connection, 1024)
        handle_client_thread = Thread(target=handle_client,
            args=(communicator, client_address, lms_queue, active_users))
        handle_client_thread.start()
    logger.info("Leave server loop")
    logger.info("Close the server socket, terminate programm")
    server_socket.close()
