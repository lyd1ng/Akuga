import logging
from Akuga.AkugaDatabaseServer.Network import (
    weak_secure_string,
    send_packet)

# Get the logger
logger = logging.getLogger('AkugaDatabaseServer.Jumons')


def get_all_jumon_names(connection, client_address, cmd_queue):
    """
    Query the database for the names of all jumons
    """
    command = ("select name from jumons", ())
    logger.info("Enqueue 'get_all_jumon_names' from: " + str(client_address))
    cmd_queue.put((connection, client_address, command))


def get_all_basic_jumon_names(connection, client_address, cmd_queue):
    """
    Query the database for the name of all basic jumons
    aka all jumons a user starts with
    """
    command = ("select name from jumons where basic=1", ())
    logger.info("Enqueue 'get_all_basic_jumon_names' from: "
        + str(client_address))
    cmd_queue.put((connection, client_address, command))


def get_all_vanilla_jumon_stats(connection, client_address, cmd_queue):
    """
    Query the database for all battle related values of all vanilla jumons
    aka all jumons without a special effect
    """
    command = ("select name, color, attack, defense, movement from jumons where special=0", ())
    logger.info("Enqueue 'get_all_vanilla_jumon_stats' from: "
        + str(client_address))
    cmd_queue.put((connection, client_address, command))


def get_jumon_by_name(connection, client_address, cmd_queue, jumon_name):
    """
    Query the database for a jumon by its name
    """
    command = ("select * from jumons where name=?", (jumon_name, ))
    logger.info("Enqueue 'get_jumon_by_name' from: "
        + str(client_address))
    cmd_queue.put((connection, client_address, command))
