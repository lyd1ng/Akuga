import sqlite3
from hashlib import md5
from Akuga.GameServer.User import User

whitelist = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'


def secure_string(string):
    """
    Return True if all characters in the string are part of the
    whitelist. Otherwise return False
    """
    for s in string:
        if s not in whitelist:
            return False
    return True


class UserDataBase:
    """
    An abstraction around a user database where user can be registered,
    credentials are checked and player stats are stored
    """
    def __init__(self, database_path):
        self.database = sqlite3.connect(database_path)
        self.cursor = self.database.cursor()

    def Init(self):
        """
        Creates a user table (name, pass_hash)
        """
        try:
            self.cursor.execute('''CREATE TABLE users
                    (name text, pass_hash text, )''')
        except sqlite3.OperationalError:
            pass

    def CommitUser(self, user):
        """
        Commits a user to the database this presupposes there is a table
        users within the database
        """
        if secure_string(user.name) and secure_string(user.pass_hash):
            """
            Insert the user only if there are no potentially
            malicious characters included
            """
            self.cursor.execute("INSERT INTO users VALUES (?, ?)",
                (user.name, user.pass_hash))
            return 0
        return -1

    def GetUserByName(self, user_name):
        """
        Query the database by the name of the user and return per
        """
        if secure_string(user_name):
            self.cursor.execute("SELECT * from users WHERE name=?", (user_name,))
        else:
            return None
        user_tuple = self.cursor.fetchone()
        if user_tuple is None:
            return None
        return User(user_tuple[0], user_tuple[1], None)

    def GetUserByNameAndHash(self, user_name, user_pass_hash):
        """
        Gets a user by pers name and pass_hash. Used to check the credentials
        of a user.
        """
        if secure_string(user_name) and secure_string(user_pass_hash):
            self.cursor.execute('''SELECT * from users WHERE name=?
                    AND pass_hash=?''', (user_name, user_pass_hash))
        else:
            return None
        user_tuple = self.cursor.fetchone()
        if user_tuple is None:
            return None
        return User(user_tuple[0], user_tuple[1], None)


if __name__ == "__main__":
    user_db = UserDataBase("test.db")
    user_db.Init()
    user = User("TestUser1", md5("passwort".encode('utf-8')).hexdigest(), None)
    user_db.CommitUser(user)
    print(user_db.GetUserByNameAndHash('TestUser1', 'e22a63fb76874c99488435f26b117e37'))
