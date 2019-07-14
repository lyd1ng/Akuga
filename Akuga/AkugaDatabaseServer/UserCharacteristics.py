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
    command = ("select name from user_accounts where name=?", (username, ))
    logger.info('Enqueue command from: ' + str(client_address))
    cmd_queue.put((connection, client_address, command))


def register_user(connection, client_address, cmd_queue,
        username, pass_hash, credits, collection):
    """
    Registers a user with a given name and pers pass hash in the database
    """
    if secure_string(username + pass_hash) is False:
        logger.info("One of the parameters where insecure!\n")
        logger.info("Received from: " + str(client_address))
        send_packet(connection, ["ERROR", "Insecure Parameter"])
        return -1
    command = ("insert into user_accounts(name, pass_hash, credits, collection, set1, set2, set3)\
        select :name, :pass_hash, :credits, :collection, :set1, :set2, :set3\
        where not exists(select 1 from user_accounts where name= :name)", {
        'name': username,
        'pass_hash': pass_hash,
        'credits': credits,
        'collection': collection,
        'set1': "",
        'set2': "",
        'set3': ""})
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
    command = ("select name from user_accounts where name=?\
            and pass_hash=?", (username, pass_hash))
    logger.info('Enqueue command from: ' + str(client_address))
    cmd_queue.put((connection, client_address, command))
