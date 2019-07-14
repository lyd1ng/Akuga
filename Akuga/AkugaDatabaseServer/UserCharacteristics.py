import logging
from Akuga.AkugaDatabaseServer.Network import (
    secure_string,
    send_packet)

# Get the logger
logger = logging.getLogger('AkugaDatabaseServer.UserCharacteristics')


def check_username(connection, client_address, cmd_queue, username):
    """
    Checks if a username is free or not
    """
    if secure_string(username) is False:
        logger.info("One of the parameters where insecure!\n")
        logger.info("Received from: " + str(client_address))
        send_packet(connection, ["ERROR", "Insecure Parameter"])
        return -1
    command = ("select name from credentials where name=?", (username, ))
    logger.info('Enqueue command from: ' + str(client_address))
    cmd_queue.put((connection, client_address, command))


def register_user(connection, client_address, cmd_queue, username, pass_hash):
    """
    Registers a user with a given name and pers pass hash in the database
    """
    if secure_string(username + pass_hash) is False:
        logger.info("One of the parameters where insecure!\n")
        logger.info("Received from: " + str(client_address))
        send_packet(connection, ["ERROR", "Insecure Parameter"])
        return -1
    command = ("insert into credentials(name, pass_hash)\
        select :name, :pass_hash\
        where not exists(select 1 from credentials where name= :name)",
        {'name': username, 'pass_hash': pass_hash})
    logger.info('Enqueue command from: ' + str(client_address))
    cmd_queue.put((connection, client_address, command))


def check_user_credentials(connection, client_address,
        cmd_queue, username, pass_hash):
    """
    Checks the credentials of a user
    """
    if secure_string(username + pass_hash) is False:
        logger.info("One of the parameters where insecure!\n")
        logger.info("Recieved from: " + str(client_address))
        send_packet(connection, ["ERROR", "Insecure Parameter"])
        return -1
    command = ("select name from credentials where name=?\
            and pass_hash=?", (username, pass_hash))
    logger.info('Enqueue command from: ' + str(client_address))
    cmd_queue.put((connection, client_address, command))
