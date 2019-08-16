"""
This module contain the name_constructor dict and other functions
to build up the pickpool and translate the active sets of all users
to a list of jumon instances
"""
from Akuga.MatchServer.Meeple import Jumon
from Akuga.MatchServer.GlobalDefinitions import USER_DBS_ADDRESS
from Akuga.MatchServer.NetworkProtocoll import (
    send_packet,
    receive_dbs_response)


JUMON_NAME_CONSTRUCTOR_DICT = {}


def get_vanilla_jumons_from_dbs(userdbs_connection):
    '''
    Read all vanilla jumons from the dbs and create a constructor
    dict out of them. This constructor dict will store preconfigured
    constructor calls which will be used to create vanilla jumon instances
    with different ids.
    '''
    # Get the stats of all vanilla jumons
    send_packet(userdbs_connection, ['GET_ALL_VANILLA_JUMON_STATS'])
    response, error = receive_dbs_response(userdbs_connection, 1024)
    if response is None:
        return ('ERROR', error)
    # The response is a list of tuples containing all stats of a jumon in
    # the form: name, color, attack, defense, movement
    # Now add a preconfigured constructor call under the name of the jumon
    jumon_dictionary = {}
    for jumon in response:
        # Here a lambda inside a lambda has to be used as the jumon
        # variable has to be bound, otherwise all lambdaterms would
        # refer to the same (the last) jumon in the response list
        jumon_dictionary[jumon[0]] =\
            (lambda j: lambda _id: Jumon(j[0], _id, j[1], j[2], j[3], j[4]))(jumon)
    return jumon_dictionary


def initialise_jumon_name_constructor_dict(userdbs_connection):
    '''
    Initialise the JUMON_NAME_CONSTRUCTOR_DICT
    '''
    global JUMON_NAME_CONSTRUCTOR_DICT
    JUMON_NAME_CONSTRUCTOR_DICT = get_vanilla_jumons_from_dbs(
        userdbs_connection)
    # Here all the special jumons have to be added manually
    pass


if __name__ == '__main__':
    import socket
    userdbs_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    userdbs_connection.connect(USER_DBS_ADDRESS)
    initialise_jumon_name_constructor_dict(userdbs_connection)
    orgenthor = JUMON_NAME_CONSTRUCTOR_DICT['Orgenthor die Zwillingsbrut'](0)
    print(orgenthor.name)
    print(orgenthor.attack)
    print(orgenthor.defense)
    print(orgenthor.movement)
