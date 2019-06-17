"""
This module contains all functions related to network communication
"""
import smtplib
from ast import literal_eval
from email.mime.text import MIMEText
from Akuga.GameServer.GlobalDefinitions import (
    EMAIL_SERVER,
    EMAIL_PORT,
    EMAIL_ADDRESS,
    EMAIL_PASSWORD)

whitelist = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'


def send_packet(connection, tokens, terminator="END"):
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


def secure_string(string):
    """
    Return True if all characters in the string are part of the
    whitelist. Otherwise return False
    """
    for s in string:
        if s not in whitelist:
            return False
    return True


def receive_dbs_response(userdbs_connection):
    """
    Receive up to 512 bytes from the database server
    and parse it using the parse_literal function of the
    ast module. This can be done as the pysqlite module
    return its results as a python list
    """
    response_packet = userdbs_connection.recv(512)
    response_packet = response_packet.decode('utf-8')
    tokens = response_packet.split(":")
    # If an error is received return None and the error msg received
    if tokens[0] == "ERROR":
        return (None, tokens[1])
    # If no error is received return the parsed literal and "" as msg
    print("Litetal to parse: " + tokens[1])
    return (literal_eval(tokens[1]), "")


# TODO: Doesnt work yet, authentication fails...
def send_password_to_client_email(username, password, user_email):
    """
    Send the password to the client via email
    """
    # Create the message to send (will be beautified in the future)
    msg = MIMEText("Hello {0}, your password is {1}".format(username, password))
    msg['Subject'] = 'Welcome to Akuga'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = user_email
    # Connect to the email server
    server = smtplib.SMTP(EMAIL_SERVER, EMAIL_PORT)
    import ssl
    server.starttls(ssl.create_default_context())
    # Login and send the email
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    server.sendmail(EMAIL_ADDRESS, user_email, msg.as_string())
    server.quit()
