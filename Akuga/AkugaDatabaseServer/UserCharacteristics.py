import logging
from Akuga.AkugaDatabaseServer.Network import (send_packet)

# Get the logger
logger = logging.getLogger('AkugaDatabaseServer.UserCharacteristics')


def get_user_by_name(connection, client_address, cmd_queue, username):
    """
    Query for the whole user datastructure
    """
    command = ("select * from user_accounts where name=?", (username, ))
    cmd_queue.put((connection, client_address, command))


def check_username(connection, client_address, cmd_queue, username):
    """
    Checks if a username is free or not
    """
    command = ("select name from user_accounts where name=?", (username, ))
    logger.info('Enqueue command from: ' + str(client_address))
    cmd_queue.put((connection, client_address, command))


def register_user(connection, client_address, cmd_queue,
        username, pass_hash, credits, collection):
    """
    Registers a user with a given name and pers pass hash in the database
    """
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
    command = ("select name from user_accounts where name=?\
            and pass_hash=?", (username, pass_hash))
    logger.info('Enqueue command from: ' + str(client_address))
    cmd_queue.put((connection, client_address, command))


def get_jumon_collection(connection, client_address, cmd_queue, username):
    """
    Get the collection of a user
    """
    command = ("select collection from user_accounts where name=?",
        (username, ))
    cmd_queue.put((connection, client_address, command))


def update_user(connection, client_address, cmd_queue,
        username, credits, collection, set1, set2, set3):
    """
    Update every field except the name and the pass_hash of a user.
    The name of a user cant be changed cause it it used as the id
    and the pass hash should not be send over the network unneccesarily
    """
    try:
        credits_value = int(credits)
    except ValueError:
        logger.info("The credits string was malformed")
        if connection is not None:
            send_packet(connection, ["ERROR", "A parameter was malformed"])
            return -1

    command = ('''update user_accounts set
        credits=:credits, collection=:collection,
        set1=:set1, set2=:set2, set3=:set3 where name=:name''',
        {
            'credits': credits_value,
            'collection': collection,
            'set1': set1,
            'set2': set2,
            'set3': set3,
            'name': username
        })
    cmd_queue.put((connection, client_address, command))


def get_jumon_set(connection, client_address, cmd_queue, username, index):
    """
    Get a jumons set of a user.
    $jumon_set e [0, 1, 2]
    """
    try:
        set_index = int(index)
        # Only 0, 1, 2 is allowed as index
        if set_index < 0 or set_index > 2:
            raise ValueError
    except ValueError:
        logger.info("The index parameter is malformed")
        # If its not a local command
        if connection is not None:
            send_packet(connection, ["ERROR", "Malformed Parameter"])
        logger.info("Recieved from: " + str(client_address))
        return -1
    command = ("select " + ['set1', 'set2', 'set3'][set_index]
        + " from user_accounts where name=?", (username, ))
    cmd_queue.put((connection, client_address, command))


def set_jumon_set(connection, client_address, cmd_queue,
        username, index, jumon_set):
    """
    Set the jumon set $index to jumon_set
    jumon_set is a string containing the names of all jumons delimited by
    a comma
    """
    try:
        set_index = int(index)
        # Only 0, 1, 2 is allowed as index
        if set_index < 0 or set_index > 2:
            raise ValueError
    except ValueError:
        logger.info("The index parameter is malformed")
        # If its not a local command
        if connection is not None:
            send_packet(connection, ["ERROR", "Malformed Parameter"])
        logger.info("Recieved from: " + str(client_address))
        return -1
    command = ("update user_accounts set " + ['set1', 'set2', 'set3'][set_index] + "=? where name=?",
        (jumon_set, username))
    cmd_queue.put((connection, client_address, command))


def reward_user(connection, client_address, cmd_queue, username, credits):
    """
    Increment the credits of a user by the integer value of credits
    """
    # if one of the paramaters are insecure log it and return
    try:
        credits_int = int(credits)
    except ValueError:
        logger.info("Credits parameter was insecure!")
        logger.info("Received from: " + str(client_address))
        send_packet(connection, ["ERROR", "Insecure Parameter"])
        return -1
    command = ('update user_accounts set credits=credits+? where name=?',
        (credits_int, username))
    cmd_queue.put((connection, client_address, command))
