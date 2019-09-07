import threading
from json import loads
from Akuga.JumonSet import jumon_set_from_list, serialize_set


def user_from_database_response(response, connection, client_address):
    """
    Create and return a user instance created from
    a databse response
    """
    # Convert the coma delimited strings into jumon sets
    collection = loads(response[3])
    set1 = loads(response[4])
    set2 = loads(response[5])
    set3 = loads(response[6])
    return User(response[0], response[1], response[2], collection,
        set1, set2, set3, connection, client_address)


class User:
    """
    Represents a registered user aka one of the poor souls doomed to
    play Akuga
    name: name of the player
    pass_hash: the md5 hash of its password
    credits: The credits a user owns
    set[0,1,2]: The three jumon sets a user once created
    connection: the connection socket
    client_address: The address of the connection
    """
    def __init__(self, name, pass_hash, credits, collection, set0, set1, set2,
            connection, client_address):
        self.name = name
        self.pass_hash = pass_hash
        # The credits of the user
        self.credits = credits
        # The users jumon collection
        self.collection = collection
        # The three sets
        self.sets = [set0, set1, set2]
        self.connection = connection
        self.client_address = client_address
        # The active set (will always set before the user is enqueued)
        self.active_set = 0
        self.in_play = False
        # Make the user class threadsafe even if it should never be altered
        # by more than one thread
        self.lock = threading.Lock()

    def set_in_play(self, in_play):
        """
        Set the in_play flag. Thread-safe
        """
        with self.lock:
            self.in_play = in_play

    def get_collection_serialized(self):
        """
        Return all elements of the collection list as a ',' seperated string.
        This way it can be send to the database server
        """
        return serialize_set(self.collection)

    def get_set_serialized(self, index):
        """
        Return all elements of the set as a ',' seperated string.
        This way it can be send to the database server
        """
        return serialize_set(self.sets[index])

    def __str__(self):
        """
        Returns the user as a string
        """
        return "User: " + self.name + " " + self.pass_hash\
            + " " + str(self.credits) + " " + str(self.collection) + " " +\
            str(self.sets) + " " + str(self.client_address) + " " + \
            str(self.in_play)
