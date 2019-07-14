import logging
from datetime import datetime
from Akuga.AkugaDatabaseServer.Network import (
    secure_string,
    send_packet)


# Get the logger
logger = logging.getLogger('AkugaDatabaseServer.UserStats')


def today():
    """
    Get the current date in the format %Y-%m-%-d
    """
    return datetime.today().strftime("%Y-%m-%d")


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
        logger.info("Received from: " + str(client_address))
        send_packet(connection, ["ERROR", "Insecure Parameter"])
        return -1
    # Enqueues to create an empty stats field if none exists
    # Cause the queue is a fifo structure this will be executed before
    # the update command
    init_dayly_entry(cmd_queue, username, game_mode)
    # Create the update command
    command = ('''update userstats set wins=wins+1 where name=? and mode=?\
        and date=? ''', (username, game_mode, today()))
    logger.info('Enqueue command from: ' + str(client_address))
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
        logger.info("Received from: " + str(client_address))
        send_packet(connection, ["ERROR", "Insecure Parameter"])
        return -1
    # Enqueues to create an empty stats field if none exists
    # Cause the queue is a fifo structure this will be executed before
    # the update command
    init_dayly_entry(cmd_queue, username, game_mode)
    # Create the update command
    command = ('''update userstats set looses=looses+1 where name=? and mode=?\
        and date=? ''', (username, game_mode, today()))
    logger.info('Enqueue command from: ' + str(client_address))
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
        logger.info("Received from: " + str(client_address))
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
    logger.info('Enqueue command from: ' + str(client_address))
    cmd_queue.put((connection, client_address, command))
    return 0
