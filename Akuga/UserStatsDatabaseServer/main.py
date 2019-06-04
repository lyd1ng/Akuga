import socket
import sqlite3
import logging
from Akuga.UserStatsDatabaseServer.GlobalDefinitions import (
    server_address,
    max_active_connections,
    database_path)
from queue import Queue
from threading import Thread
from datetime import datetime
logging.basicConfig(filename='UserStatsDatabaseServer.log', level=logging.INFO)
logger = logging.getLogger(__name__)
running = True

# TODO: wrap the sql output inside the akuga network protocoll

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
    whitelist = '-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    for s in string:
        if s not in whitelist:
            return False
    return True


def handle_sigint(sig, frame):
    """
    Termintate the programme properly on sigint
    """
    global running
    logger.info("Received sigint, terminating program")
    running = False


def InitDaylyEntry(cmd_queue, username, game_mode):
    """
    Creates an empty userstats entry (0 wins, 0 looses)
    for the user named username in the specified game mode.
    The date is always today to avoid tampering entries from the past
    """
    command = '''insert into userstats (name, mode, date, wins, looses)
        select '{0}', '{1}', '{2}', 0, 0
        where not exists(select 1 from userstats where name='{0}'
        and mode='{1}' and date='{2}') '''.format(username, game_mode,
            today())
    print(command)
    logging.info("Enqueued command from: local")
    cmd_queue.put((None, "local", command))


def AddWin(connection, client_address, cmd_queue, username, game_mode):
    """
    Adds a win for the user username in the game mode game_mode
    the date is always today to avoid tempering data in the past
    """
    # If on of the parameters are insecure log it and return
    if secure_string(username) is False or secure_string(game_mode) is False:
        logger.info("Username or gamemode where insecure!")
        logger.info("Received from: " + str(client_address))
        return -1
    # Enqueues to create an empty stats field if none exists
    # Cause the queue is a fifo structure this will be executed before
    # the update command
    InitDaylyEntry(cmd_queue, username, game_mode)
    # Create the update command
    command = '''update userstats set wins=wins+1 where name='{0}' and mode=\
        '{1}' and date='{2}' '''.format(username, game_mode, today())
    logger.info('Enqueue command from: ' + str(client_address))
    cmd_queue.put((connection, client_address, command))
    return 0


def AddLoose(connection, client_address, cmd_queue, username, game_mode):
    """
    Adds a loose for the user username in the game mode game_mode
    the date is always today to avoid tempering data in the past
    """
    # If on of the parameters are insecure log it and return
    if secure_string(username) is False or secure_string(game_mode) is False:
        logger.info("Username or gamemode where insecure!")
        logger.info("Received from: " + str(client_address))
        return -1
    # Enqueues to create an empty stats field if none exists
    # Cause the queue is a fifo structure this will be executed before
    # the update command
    InitDaylyEntry(cmd_queue, username, game_mode)
    # Create the update command
    command = '''update userstats set looses=looses+1 where name='{0}' and mode=\
        '{1}' and date='{2}' '''.format(username, game_mode, today())
    logger.info('Enqueue command from: ' + str(client_address))
    cmd_queue.put((connection, client_address, command))
    return 0


def GetStats(connection, client_address, cmd_queue, username,
        game_mode, from_date, to_date):
    """
    Queries all the user stats of a user in a certain game mode between and
    including the from and the to date
    """
    # if on of the parameters are insecure log it and return
    if secure_string(username + game_mode + from_date + to_date) is False:
        logger.info("One of the parameters where insecure!")
        logger.info("Received from: " + str(client_address))
        return -1
    # Create the query command
    command = '''select date,wins,looses from userstats where name='{0}' and
        mode='{1}' and date >= '{2}' and date <= '{3}'
        '''.format(username, game_mode, from_date, to_date)
    print(command)
    logger.info('Enqueue command from: ' + str(client_address))
    cmd_queue.put((connection, client_address, command))
    return 0


def handle_client(connection, client_address, cmd_queue):
    while True:
        try:
            packet = connection.recv(512).decode('utf-8')
        except socket.error:
            connection.close()
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
            AddWin(connection, client_address, cmd_queue, username, game_mode)
        if tokens[0] == "ADD_LOOSE" and len(tokens) >= 3:
            """
            If the command token is ADD_LOOSE and enough tokens are received
            add a loose to the stats of a user in a certain game mode
            """
            username = tokens[1]
            game_mode = tokens[2]
            AddLoose(connection, client_address, cmd_queue, username, game_mode)
        if tokens[0] == "GET_STATS" and len(tokens) >= 5:
            """
            If the command token is get_stats and enough tokens are received
            request the stats of a user in a certain game mode from a start
            to an end date
            """
            username = tokens[1]
            game_mode = tokens[2]
            from_date = tokens[3]
            to_date = tokens[4]
            GetStats(connection, client_address, cmd_queue, username,
                game_mode, from_date, to_date)


def sql_worker(cmd_queue):
    """
    Reads commands from cmd_queue and execute them using cursor
    Terminate if a command is None.
    Send the results directly to the clients, the connection socket
    is part of the event enqueued in the cmd_queue
    """
    # Open the database (stop having it be close)
    database = sqlite3.connect(database_path)
    cursor = database.cursor()

    # Create a userstats table if non exists
    InitDatabase(database, cursor)

    while True:
        connection, client_address, command = cmd_queue.get()
        if command is None:
            logger.info("Received None command. SQL Worker shutting down")
            break
        """
        The result can be turned into a string and send to the client
        as the ast.literal_eval function can be used to turn this string
        into a list safely.
        """
        result = ""
        try:
            cursor.execute(command)
            result = str(cursor.fetchall())
        except sqlite3.Error as e:
            logger.info("SQL Error from: " + str(client_address))
            result = e.args[0]
        if connection is not None:
            result = result.encode('utf-8')
            connection.send(result)
            logger.info("Send result to: " + str(client_address))
        cmd_queue.task_done()
        # Commit to the database to make the changes visible
        database.commit()
    database.commit()
    database_path.close()


def InitDatabase(database, cursor):
    """
    Just create a userstats table if there is none
    """
    try:
        logger.info("Create a userstats table")
        cursor.execute("create table userstats\
            (name text, mode text, date text, wins real, looses real)")
        database.commit()
    except sqlite3.Error:
        logger.info("Failed to create the table userstats")
        logger.info("Does it already exists?")


if __name__ == "__main__":
    # Build the server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(server_address)
    server_socket.listen(max_active_connections)
    logger.info("Server socket listening at " + str(server_address))
    logger.info("Server socket listening for " + str(max_active_connections))

    # Create the cmd queue with a max of 512 entries
    cmd_queue = Queue(512)

    # Spawn the sql worker process. It will work on the queue
    # containing the sql commands and the socket they where send
    # on. The results are directly send to the clients
    sql_worker_process = Thread(target=sql_worker, args=(cmd_queue, ))
    sql_worker_process.daemon = True
    sql_worker_process.start()

    while running:
        # Accept new connections
        connection, client_address = server_socket.accept()
        # And handle them using the handle_client function
        handle_client_thread = Thread(target=handle_client,
            args=(connection, client_address, cmd_queue))
        handle_client_thread.daemon = True
        handle_client_thread.start()
    # Handle all remaining requests
    cmd_queue.join()
    # Close the server socket to free the address
    server_socket.close()
