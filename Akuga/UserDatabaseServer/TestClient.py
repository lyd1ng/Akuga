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
        SendPacket(client_socket, ["CHECK_CREDENTIALS", str(i), str(i) + "Pass"])
        result_str = client_socket.recv(256)
        result_str = result_str.decode('utf-8')
        tokens = result_str.split(':')
        result_literal = literal_eval(tokens[1])
        print(result_literal)
    client_socket.close()
