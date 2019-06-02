import socket
import sqlite3
import logging
from Akuga.UserStatsDatabaseServer.GlobalDefinitions import (
    server_address,
    max_active_connections,
    database_path)
from queue import Queue
from threading import Thread
logging.basicConfig(filename='UserStatsDatabaseServer.log', level=logging.INFO)
logger = logging.getLogger(__name__)
running = True


def handle_sigint(sig, frame):
    """
    Termintate the programme properly on sigint
    """
    global running
    logger.info("Received sigint, terminating program")
    running = False


def handle_client(connection, client_address, cmd_queue):
    """
    Handles a client connection.
    Read commands from the client and enque them in the cmd_queue.
    The commands are plain text sql.
    The command is enqued with the connection socket and the client
    address so the sql worker can send the answers directly to the clients
    """
    while True:
        try:
            command = connection.recv(512).decode('utf-8')
        except socket.error:
            logger.info("Socket error receiving from: " + str(client_address) +
                " terminating handle_client function")
            connection.close()
            break
        logger.info("Enqueu command from: " + str(client_address))
        cmd_queue.put((connection, client_address, command))


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
