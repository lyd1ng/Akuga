import queue
import random
import socket
import logging
import smtplib
from hashlib import md5
from threading import Thread
from multiprocessing import Process
from ast import literal_eval
from email.mime.text import MIMEText
from Akuga.GameServer.User import User
from Akuga.MatchServer.MatchServer import MatchServer
from Akuga.GameServer.GlobalDefinitions import (
    server_address,
    user_dbs_address,
    max_active_connection,
    email_server,
    email_port,
    email_address,
    email_password)

logging.basicConfig(filename='Akuga.log', level=logging.INFO)
logger = logging.getLogger(__name__)
whitelist = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'


def SendPacket(connection, tokens, terminator="END"):
    """
    Send a packet containing out of multiple tokens
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


def secure_string(string):
    """
    Return True if all characters in the string are part of the
    whitelist. Otherwise return False
    """
    for s in string:
        if s not in whitelist:
            return False
    return True


def generate_random_password():
    """
    Returns a random password which is 10 chars long
    """
    password = ""
    for i in range(10):
        password += whitelist[random.randint(0, len(whitelist) - 1)]
    return password


def receive_dbs_response(userdbs_connection):
    """
    Receive up to 512 bytes from the database server
    and parse it using the parse_literal function of the
    ast module. This can be done as the pysqlite module
    return its results as a python list
    """
    response_packet = userdbs_connection.recv(512)
    response_packet = response_packet.decode('utf-8')
    tokens = response_packet.split(":")
    # If an error is received return None and the error msg received
    if tokens[0] == "ERROR":
        return (None, tokens[1])
    # If no error is received return the parsed literal and "" as msg
    print("Litetal to parse: " + tokens[1])
    return (literal_eval(tokens[1]), "")


# TODO: Doesnt work yet, authentication fails...
def SendPasswordToClientEmail(username, password, user_email):
    """
    Send the password to the client via email
    """
    # Create the message to send (will be beautified in the future)
    msg = MIMEText("Hello {0}, your password is {1}".format(username, password))
    msg['Subject'] = 'Welcome to Akuga'
    msg['From'] = email_address
    msg['To'] = user_email
    # Connect to the email server
    server = smtplib.SMTP(email_server, email_port)
    import ssl
    server.starttls(ssl.create_default_context())
    # Login and send the email
    server.login(email_address, email_password)
    server.sendmail(email_address, user_email, msg.as_string())
    server.quit()


def handle_client(connection, client_address, lms_queue, amm_queue):
    """
    Handles the connection of a user (the connection as well as the
    client address is stored within the user instance)
    """
    # Connect to the user database
    userdb_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    userdb_connection.connect(user_dbs_address)
    print("In handle client thread!")
    # The instance of the user: None until a succsefully log in
    user = None
    while True:
        try:
            packet = connection.recv(512).decode('utf-8')
        except socket.error:
            connection.close()
            break
        print("Received: " + packet)
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
                SendPacket(userdb_connection, ["CHECK_USERNAME", username])
                response, error = receive_dbs_response(userdb_connection)
                print("Received a response from the udbs")
                if response is None:
                    """
                    If the response is None an error occured
                    (like inalid chars) send the error msg to the  client
                    """
                    logger.info("Database error: " + error)
                    SendPacket(connection, ["ERROR", error])
                elif len(response) > 0:
                    logger.info("User: " + username + " already exists\n")
                    SendPacket(connection, ["ERROR",
                        "User: " + username + " already exists"])
                else:
                    # If the username is free generate a password
                    # and register the user
                    password = generate_random_password()
                    pass_hash = md5(password.encode('utf-8')).hexdigest()
                    # Register the user with pers username and pers hash
                    SendPacket(userdb_connection, ["REGISTER_USER",
                        username, pass_hash])
                    response, error = receive_dbs_response(userdb_connection)
                    if response is None:
                        """
                        If the response is None an error occured, send the
                        error msg to the client
                        """
                        logger.info("Database error: " + error)
                        SendPacket(connection, ["ERROR", error])
                    else:
                        """
                        If no error occured email the client
                        """
                        logger.info("Register user: " + username)
                        SendPasswordToClientEmail(username, password, email)
                        SendPacket(connection, ["SUCCESSFULLY_REGISTERED"])
            if tokens[0] == "LOG_IN" and len(tokens) >= 3:
                """
                Check the credentials of the user
                """
                username = tokens[1]
                pass_hash = tokens[2]
                SendPacket(userdb_connection,
                    ["CHECK_CREDENTIALS", username, pass_hash])
                response, error = receive_dbs_response(userdb_connection)
                if response is None:
                    # An error occured, pass the error to the client
                    logger.info("Database error: " + error)
                    SendPacket(connection, ["ERROR", error])
                if len(response) > 0:
                    """
                    If there is a result (there should never be one than more)
                    But keep > 0 for safety
                    """
                    # Unlock the logged in functionalities
                    user = User(username, pass_hash,
                        connection, client_address)
                    logger.info("Logging in: " + username)
                    SendPacket(connection, ["SUCCESSFULLY_LOGGED_IN"])
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
                elif tokens[1] == 'amm':
                    logger.info("Enqueue " + user.name + "for amm")
                    amm_queue.put(user)
                else:
                    logger.info("Invalid game mode: " + tokens[1])
                    SendPacket(connection, ["ERROR", "Invalid game mode: "
                        + tokens[1]])
        else:
            """
            If the user is logged in but currently playing a match,
            do nothin
            """
            pass


def HandleLMSQueue(lms_queue):
    """
    Invoke a lms match between the two uppermost users
    """
    # Get two users from the queue
    user1 = lms_queue.get()
    user1.in_play = True
    user2 = lms_queue.get()
    user2.in_play = True
    logger.info("Got two user for an lms match\n")
    users = {user1.name: user1.connection, user2.name: user2.connection}
    MatchServerProcess = Process(target=MatchServer, args=('lms', users, None))
    MatchServerProcess.start()
    logger.info("Started MatchServer subprocess\n")


def HandleAMMQueue(amm_queue):
    """
    Invoke a amm match between the two uppermost users
    """
    # Get two users from the queue
    user1 = amm_queue.get()
    user1.in_play = True
    user2 = amm_queue.get()
    user2.in_play = True
    logger.info("Got two user for an amm match\n")
    users = {user1.name: user1.connection, user2.name: user2.connection}
    MatchServerProcess = Process(target=MatchServer, args=('amm', users, None))
    MatchServerProcess.start()
    logger.info("Started MatchServer subprocess\n")


if __name__ == '__main__':
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(server_address)
    server_socket.listen(max_active_connection)
    logger.info("Creates server socket, waiting for: "
        + str(max_active_connection))

    # The game mode queues
    lms_queue = queue.Queue()
    amm_queue = queue.Queue()

    # Create and start the handle game mode queue threads for each game mode
    handle_lms_queue_thread = Thread(target=HandleLMSQueue, args=(lms_queue,))
    handle_amm_queue_thread = Thread(target=HandleAMMQueue, args=(amm_queue,))
    handle_lms_queue_thread.daemon = True
    handle_amm_queue_thread.daemon = True
    handle_lms_queue_thread.start()
    handle_amm_queue_thread.start()
    logger.info("Started handle_gamemode_queue threads as daemons\n")

    while True:
        try:
            connection, client_address = server_socket.accept()
        except socket.error:
            break
        handle_client_thread = Thread(target=handle_client,
            args=(connection, client_address, lms_queue, amm_queue))
        handle_client_thread.start()
    server_socket.close()
