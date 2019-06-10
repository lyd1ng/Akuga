import socket
import sqlite3
import logging
from Akuga.UserDatabaseServer.GlobalDefinitions import (
    SERVER_ADDRESS,
    MAX_ACTIVE_CONNECTIONS,
    DATABASE_PATH)
from queue import Queue
from threading import Thread
from datetime import datetime


def today():
    """
    Get the current date in the format %Y-%m-%-d
    """
    return datetime.today().strftime("%Y-%m-%d")


def secure_string(string):
    """
    Return True if all characters in the string are part of the
    whitelist. Otherwise return False
    """
    whitelist = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    for s in string:
        if s not in whitelist:
            return False
    return True


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


def init_dayly_entry(cmd_queue, username, game_mode):
    """
    Creates an empty userstats entry (0 wins, 0 looses)
    for the user named username in the specified game mode.
    The date is always today to avoid tampering entries from the past
    """
    command = ('''insert into userstats (name, mode, date, wins, looses)
        select :name, :mode, :date, 0, 0
        where not exists(select 1 from userstats where name=:name
        and mode=:mode and date=:date)''',
        {'name': username, 'mode': game_mode, 'date': today()})
    print(command)
    logger.info("Enqueued command from: local\n")
    cmd_queue.put((None, "local", command))


def add_win(connection, client_address, cmd_queue, username, game_mode):
    """
    Adds a win for the user username in the game mode game_mode
    the date is always today to avoid tempering data in the past
    """
    # If on of the parameters are insecure log it and return
    if secure_string(username) is False or secure_string(game_mode) is False:
        logger.info("Username or gamemode where insecure!\n")
        logging.info("Received from: " + str(client_address))
        send_packet(connection, ["ERROR", "Insecure Parameter"])
        return -1
    # Enqueues to create an empty stats field if none exists
    # Cause the queue is a fifo structure this will be executed before
    # the update command
    init_dayly_entry(cmd_queue, username, game_mode)
    # Create the update command
    command = ('''update userstats set wins=wins+1 where name=? and mode=?\
        and date=? ''', (username, game_mode, today()))
    logging.info('Enqueue command from: ' + str(client_address))
    cmd_queue.put((connection, client_address, command))
    return 0


def add_loose(connection, client_address, cmd_queue, username, game_mode):
    """
    Adds a loose for the user username in the game mode game_mode
    the date is always today to avoid tempering data in the past
    """
    # If on of the parameters are insecure log it and return
    if secure_string(username) is False or secure_string(game_mode) is False:
        logger.info("Username or gamemode where insecure!\n")
        logging.info("Received from: " + str(client_address))
        send_packet(connection, ["ERROR", "Insecure Parameter"])
        return -1
    # Enqueues to create an empty stats field if none exists
    # Cause the queue is a fifo structure this will be executed before
    # the update command
    init_dayly_entry(cmd_queue, username, game_mode)
    # Create the update command
    command = ('''update userstats set looses=looses+1 where name=? and mode=?\
        and date=? ''', (username, game_mode, today()))
    logging.info('Enqueue command from: ' + str(client_address))
    cmd_queue.put((connection, client_address, command))
    return 0


def get_stats(connection, client_address, cmd_queue, username, game_mode,
        from_year, from_month, from_day, to_year, to_month, to_day):
    """
    Queries all the user stats of a user in a certain game mode between and
    including the from and the to date
    """
    # if on of the parameters are insecure log it and return
    if secure_string(username + game_mode + from_year + from_month + from_day
            + to_year + to_month + to_day) is False:
        logger.info("One of the parameters where insecure!\n")
        logging.info("Received from: " + str(client_address))
        send_packet(connection, ["ERROR", "Insecure Parameter"])
        return -1
    # Create the date strings
    from_date = from_year + '-' + from_month + '-' + from_day
    to_date = to_year + '-' + to_month + '-' + to_day
    # Create the query command
    command = ('''select date,wins,looses from userstats where name=? and
        mode=? and date >= ? and date <= ?''',
        (username, game_mode, from_date, to_date))
    print(command)
    logging.info('Enqueue command from: ' + str(client_address))
    cmd_queue.put((connection, client_address, command))
    return 0


def check_username(connection, client_address, cmd_queue, username):
    """
    Checks if a username is free or not
    """
    if secure_string(username) is False:
        logger.info("One of the parameters where insecure!\n")
        logging.info("Received from: " + str(client_address))
        send_packet(connection, ["ERROR", "Insecure Parameter"])
        return -1
    command = ("select name from credentials where name=?", (username, ))
    logging.info('Enqueue command from: ' + str(client_address))
    cmd_queue.put((connection, client_address, command))


def register_user(connection, client_address, cmd_queue, username, pass_hash):
    """
    Registers a user with a given name and pers pass hash in the database
    """
    if secure_string(username + pass_hash) is False:
        logger.info("One of the parameters where insecure!\n")
        logging.info("Received from: " + str(client_address))
        send_packet(connection, ["ERROR", "Insecure Parameter"])
        return -1
    command = ("insert into credentials(name, pass_hash)\
        select :name, :pass_hash\
        where not exists(select 1 from credentials where name= :name)",
        {'name': username, 'pass_hash': pass_hash})
    logging.info('Enqueue command from: ' + str(client_address))
    cmd_queue.put((connection, client_address, command))


def check_user_credentials(connection, client_address,
        cmd_queue, username, pass_hash):
    """
    Checks the credentials of a user
    """
    if secure_string(username + pass_hash) is False:
        logger.info("One of the parameters where insecure!\n")
        logging.info("Recieved from: " + str(client_address))
        send_packet(connection, ["ERROR", "Insecure Parameter"])
        return -1
    command = ("select name from credentials where name=?\
            and pass_hash=?", (username, pass_hash))
    logging.info('Enqueue command from: ' + str(client_address))
    cmd_queue.put((connection, client_address, command))


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
        if packet.find('END') < 0:
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
        if tokens[0] == "CHECK_USERNAME" and len(tokens) >= 2:
            """
            If the command token is check_username and enough tokens
            are received check if the username in token[1] is free or not
            """
            check_username(connection, client_address, cmd_queue, tokens[1])
        if tokens[0] == "REGISTER_USER" and len(tokens) >= 3:
            """
            If the command token is register_user and enough tokens are
            received insert a new entry into the credentials table
            """
            register_user(connection, client_address, cmd_queue,
                tokens[1], tokens[2])
        if tokens[0] == "CHECK_CREDENTIALS" and len(tokens) >= 3:
            """
            If the command token is check_credentials and enough tokens
            are received, check the credentials
            """
            check_user_credentials(connection, client_address, cmd_queue,
                tokens[1], tokens[2])


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
            logging.info("SQL Error from: " + str(client_address))
            # Set the sql error msg as the result so its send to the user
            result = e.args[0]
            # If the command wasnt a locale command send the result
            # to the client using the ERROR command token
            # to signal the error
            if connection is not None:
                logging.info("Send result to: " + str(client_address))
                send_packet(connection, ["ERROR", result])
        # If the command wasnt a locale command send the result
        # to the client using the SUCCESS command token
        # to signal the success
        if connection is not None:
            logging.info("Send result to: " + str(client_address))
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
        logger.info("Create a credentials table\n")
        cursor.execute("create table credentials (name text, pass_hash text)")
        database.commit()
    except sqlite3.Error:
        logger.info("Failed to create the table credentials\n")
        logger.info("Does it already exists?\n")


if __name__ == "__main__":
    # Create a logger
    logging.basicConfig(filename='UserDatabaseServer.log', level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Build the server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(SERVER_ADDRESS)
    server_socket.listen(MAX_ACTIVE_CONNECTIONS)
    logging.info("Server socket listening at " + str(SERVER_ADDRESS))
    logging.info("Server socket listening for " + str(MAX_ACTIVE_CONNECTIONS))

    # Create the cmd queue with a max of 512 entries
    cmd_queue = Queue(512)

    # Spawn the sql worker process. It will work on the queue
    # containing the sql commands and the socket they where send
    # on. The results are directly send to the clients
    logger.info("Start the sql_worker thread as a daemon")
    sql_worker_process = Thread(target=sql_worker, args=(cmd_queue, ))
    sql_worker_process.daemon = True
    sql_worker_process.start()
    logger.info("Started sql_worker thread as a daemon")
    logger.info("Enter server loop")
    while True:
        # Accept new connections
        try:
            connection, client_address = server_socket.accept()
        except socket.Error:
            logging.info("Error while accepting connections")
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
