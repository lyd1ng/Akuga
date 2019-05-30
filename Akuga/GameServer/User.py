class User:
    """
    Represents a registered user aka one of the poor souls doomed to
    play Akuga
    name: name of the player
    pass_hash: the md5 hash of its password
    stats: a dictionary with the game mode as the key and wins and looses
           stored as a tupel as the value
           eg.: {'LastManStanding': (wins, looses)}
    connection: the connection socket
    """
    def __init__(self, name, pass_hash, stats, connection):
        self.name = name
        self.pass_hash = pass_hash
        self.stats = stats
        self.connection = connection

    def __str__(self):
        """
        Returns the user as a string
        """
        return "User: " + self.name + " " + self.pass_hash\
            + " " + str(self.connection)
