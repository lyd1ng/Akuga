import socket
from ast import literal_eval

if __name__ == "__main__":
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 10098))
    client_socket.send("select * from userstats".encode('utf-8'))
    result_str = client_socket.recv(256).decode('utf-8')
    result_list = literal_eval(result_str)
    print(type(result_list))
    print(result_list)
    input()
    client_socket.close()
