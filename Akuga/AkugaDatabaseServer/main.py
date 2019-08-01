import socket
import sqlite3
import logging
from Akuga.AkugaDatabaseServer.GlobalDefinitions import (
    SERVER_ADDRESS,
    MAX_ACTIVE_CONNECTIONS,
    DATABASE_PATH)
from Akuga.AkugaDatabaseServer.Network import (send_packet)
from Akuga.AkugaDatabaseServer.UserStats import (
    add_win,
    add_loose,
    get_stats)
from Akuga.AkugaDatabaseServer.UserCharacteristics import (
    check_username,
    register_user,
    get_user_by_name,
    check_user_credentials,
    get_jumon_collection,
    get_jumon_set,
    set_jumon_set,
    update_user,
    reward_user)
from Akuga.AkugaDatabaseServer.Jumons import (
    get_all_jumon_names,
    get_all_basic_jumon_names,
    get_jumon_by_name)
from queue import Queue
from threading import Thread


def handle_client(connection, client_address, cmd_queue):
    while True:
        try:
            packet = connection.recv(512).decode('utf-8')
        except socket.error:
            logger.info("Socket Error")
            break
        if not packet:
            logger.info("Socket Close")
            break
        if packet.find('END\n') < 0:
            """
            Simply discard the packet if there is not terminator found
            """
            continue
        # Split the packet into tokens with the ":" delim
        tokens = packet.split(":")
        if tokens[0] == "ADD_WIN" and len(tokens) >= 3:
            """
            If the command token is ADD_WIN and enough tokens are received
            add a win to the stats of a user in a certain game mode
            """
            username = tokens[1]
            game_mode = tokens[2]
            add_win(connection, client_address, cmd_queue, username, game_mode)
        if tokens[0] == "ADD_LOOSE" and len(tokens) >= 3:
            """
            If the command token is ADD_LOOSE and enough tokens are received
            add a loose to the stats of a user in a certain game mode
            """
            username = tokens[1]
            game_mode = tokens[2]
            add_loose(connection, client_address, cmd_queue, username, game_mode)
        if tokens[0] == "REWARD_USER" and len(tokens) >= 3:
            """
            Increment the credits by the integer value of tokens[2]
            """
            username = tokens[1]
            credits = tokens[2]
            reward_user(connection, client_address, cmd_queue, username, credits)
        if tokens[0] == "GET_STATS" and len(tokens) >= 5:
            """
            If the command token is get_stats and enough tokens are received
            request the stats of a user in a certain game mode from a start
            to an end date
            """
            username = tokens[1]
            game_mode = tokens[2]
            from_year = tokens[3]
            from_month = tokens[4]
            from_day = tokens[5]
            to_year = tokens[6]
            to_month = tokens[7]
            to_day = tokens[8]
            get_stats(connection, client_address, cmd_queue, username, game_mode,
                     from_year, from_month, from_day,
                     to_year, to_month, to_day)
        if tokens[0] == "GET_USER_BY_NAME" and len(tokens) >= 1:
            """
            Query for the whole user datastructure
            """
            get_user_by_name(connection, client_address, cmd_queue, tokens[1])
        if tokens[0] == "CHECK_USERNAME" and len(tokens) >= 1:
            """
            If the command token is check_username and enough tokens
            are received check if the username in token[1] is free or not
            """
            check_username(connection, client_address, cmd_queue, tokens[1])
        if tokens[0] == "REGISTER_USER" and len(tokens) >= 5:
            """
            If the command token is register_user and enough tokens are
            received insert a new entry into the user_accounts table
            """
            try:
                credits = int(tokens[3])
            except ValueError:
                send_packet(connection,
                    ["ERROR", "Credits token cant be converted to integer"])
                logger.info("Received invalid credit token from: " +
                    str(client_address))
                continue

            register_user(connection, client_address, cmd_queue,
                tokens[1], tokens[2], credits, tokens[4])
        if tokens[0] == "CHECK_CREDENTIALS" and len(tokens) >= 3:
            """
            If the command token is check_credentials and enough tokens
            are received, check the credentials
            """
            check_user_credentials(connection, client_address, cmd_queue,
                tokens[1], tokens[2])
        if tokens[0] == "GET_JUMON_COLLECTION" and len(tokens) > 2:
            """
            Get all jumons a user owns
            """
            get_jumon_collection(connection, client_address,
                cmd_queue, tokens[1])
        if tokens[0] == "GET_JUMON_SET" and len(tokens) >= 3:
            """
            Get all jumon of the specified set of a user
            """
            get_jumon_set(connection, client_address, cmd_queue,
                tokens[1], tokens[2])
        if tokens[0] == "SET_JUMON_SET" and len(tokens) >= 4:
            """
            Set all jumon of the specified set of a user
            """
            set_jumon_set(connection, client_address, cmd_queue,
                tokens[1], tokens[2], tokens[3])
        if tokens[0] == "UPDATE_USER" and len(tokens) >= 8:
            """
            Update all fields except the name and the pass_hash of a user
            """
            update_user(connection, client_address, cmd_queue,
                tokens[1], tokens[2], tokens[3], tokens[4],
                tokens[5], tokens[6])
        if tokens[0] == "GET_JUMON_NAMES" and len(tokens) >= 1:
            """
            Get the names of of all jumons
            """
            get_all_jumon_names(connection, client_address, cmd_queue)
        if tokens[0] == "GET_BASIC_JUMON_NAMES" and len(tokens) >= 1:
            """
            Get the name of all basic jumons
            """
            get_all_basic_jumon_names(connection, client_address, cmd_queue)
        if tokens[0] == "GET_JUMON_BY_NAME" and len(tokens) >= 2:
            """
            Get the whole datastructure of a jumon and send it to
            the client
            """
            get_jumon_by_name(connection, client_address, cmd_queue,
                tokens[1])


def sql_worker(cmd_queue):
    """
    Reads commands from cmd_queue and execute them using cursor
    Terminate if a command is None.
    Send the results directly to the clients, the connection socket
    is part of the event enqueued in the cmd_queue
    """
    # Open the database (stop having it be close)
    database = sqlite3.connect(DATABASE_PATH)
    cursor = database.cursor()

    # Create a userstats table if non exists
    init_database(database, cursor)

    while True:
        connection, client_address, command = cmd_queue.get()
        if command is None:
            logger.info("Received None command. SQL Worker shutting down\n")
            break
        """
        The result can be turned into a string and send to the client
        as the ast.literal_eval function can be used to turn this string
        into a list safely.
        """
        result = ""
        try:
            cursor.execute(command[0], command[1])
            result = str(cursor.fetchall())
            print("Result :" + result)
        except sqlite3.Error as e:
            logger.info("SQL Error from: " + str(client_address))
            # Set the sql error msg as the result so its send to the user
            result = e.args[0]
            # If the command wasnt a locale command send the result
            # to the client using the ERROR command token
            # to signal the error
            if connection is not None:
                logger.info("Send result to: " + str(client_address))
                send_packet(connection, ["ERROR", result])
        # If the command wasnt a locale command send the result
        # to the client using the SUCCESS command token
        # to signal the success
        if connection is not None:
            logger.info("Send result to: " + str(client_address))
            send_packet(connection, ["SUCCESS", result])
        cmd_queue.task_done()
        # Commit to the database to make the changes visible
        database.commit()
    database.commit()
    database.close()


def init_database(database, cursor):
    """
    Just create a userstats table if there is none
    """
    try:
        logger.info("Create a userstats table\n")
        cursor.execute("create table userstats\
            (name text, mode text, date text, wins real, looses real)")
        database.commit()
    except sqlite3.Error:
        logger.info("Failed to create the table userstats\n")
        logger.info("Does it already exists?\n")
    try:
        logger.info("Create a user_accounts table\n")
        cursor.execute("create table user_accounts (name text, pass_hash text,\
            credits real, collection text, set1 text, set2 text, set3 text)")
        database.commit()
    except sqlite3.Error:
        logger.info("Failed to create the table user_accounts\n")
        logger.info("Does it already exists?\n")


if __name__ == "__main__":
    # Create a logger
    logging.basicConfig(filename='AkugaDatabaseServer.log', level=logging.INFO)
    logger = logging.getLogger('AkugaDatabaseServer')

    # Build the server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(SERVER_ADDRESS)
    server_socket.listen(MAX_ACTIVE_CONNECTIONS)
    logger.info("Server socket listening at " + str(SERVER_ADDRESS))
    logger.info("Server socket listening for " + str(MAX_ACTIVE_CONNECTIONS))

    # Create the cmd queue with a max of 512 entries
    cmd_queue = Queue(512)

    # Spawn the sql worker process. It will work on the queue
    # containing the sql commands and the socket they where send
    # on. The results are directly send to the clients
    logger.info("Start the sql_worker thread as a daemon")
    sql_worker_thread = Thread(target=sql_worker, args=(cmd_queue, ))
    sql_worker_thread.daemon = True
    sql_worker_thread.start()
    logger.info("Started sql_worker thread as a daemon")
    logger.info("Enter server loop")
    while True:
        # Accept new connections
        try:
            connection, client_address = server_socket.accept()
        except socket.error:
            logger.info("Error while accepting connections")
            break
        # And handle them using the handle_client function
        handle_client_thread = Thread(target=handle_client,
            args=(connection, client_address, cmd_queue))
        handle_client_thread.daemon = True
        handle_client_thread.start()
    logger.info("Leave the server loop")
    # Handle all remaining requests
    logger.info("Wait for the command queue to be processed completly")
    cmd_queue.join()
    logger.info("Command queue was processed completly")

    # Close the server socket to free the address
    logger.info("Close the server socket, terminate programm")
    server_socket.close()
