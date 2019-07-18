def secure_string(string):
    """
    Return True if all characters in the string are part of the
    whitelist. Otherwise return False
    """
    whitelist = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    for s in string:
        if s not in whitelist:
            return False
    return True


def weak_secure_string(string, exceptions):
    """
    Checks the string again a bit weeker defined whitelist
    """
    whitelist = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'\
        + exceptions
    for s in string:
        if s not in whitelist:
            return False
    return True


def send_packet(connection, tokens, terminator="END\n"):
    """
    Send a packet containing multiple tokens.
    Every token is converted to a string using the str function
    for better convenients and is encoded using utf-8 encoding.
    A packet has the form token1:token2:...:tokenN:terminator
    """
    query = ""
    for t in tokens:
        query += str(t) + ":"
    if terminator is not None:
        query += str(terminator)
    query = query.encode('utf-8')
    connection.send(query)
