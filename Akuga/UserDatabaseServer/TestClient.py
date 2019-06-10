import socket
from ast import literal_eval


def SendPacket(connection, tokens, terminator="END"):
    """
    Send a packet containing out of multiple tokens
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


if __name__ == "__main__":
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 10098))
    for i in range(10):
        SendPacket(client_socket, ["ADD_WIN", 'lyding', 'lms'])
        result = client_socket.recv(128)
        SendPacket(client_socket, ["ADD_LOOSE", 'lyding2', 'lms'])
        result = client_socket.recv(128)
    client_socket.close()
