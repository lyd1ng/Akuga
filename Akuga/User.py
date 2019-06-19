import threading


class User:
    """
    Represents a registered user aka one of the poor souls doomed to
    play Akuga
    name: name of the player
    pass_hash: the md5 hash of its password
    connection: the connection socket
    """
    def __init__(self, name, pass_hash, connection, client_address):
        self.name = name
        self.pass_hash = pass_hash
        self.connection = connection
        self.client_address = client_address
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

    def __str__(self):
        """
        Returns the user as a string
        """
        return "User: " + self.name + " " + self.pass_hash\
            + " " + str(self.client_address)
