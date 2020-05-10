#!/usr/bin/env python3

"""  """


import socket
import select
import sys

import requests
import json

from _thread import *


# Global variables
list_of_clients = []


def get_public_ip_address():
    """ Send a request to ipinfo.io to retreive public ip address """
    response = requests.get("https://ipinfo.io/json", verify = True)
    if response.status_code != 200:
        print("Status: " + response.status_code + ". Problem with the request. Exiting")
        exit()
    data = response.json()
    return data["ip"]


def client_thread(connection, address):
    """  """
    # sends a message to the client whose user object is conn
    connection.send(b'Welcome to this chatroom!')

    while True:
        try:
            message = connection.recv(2048)
            if message:
                print("<" + address[0] + "> " + message)

                # Calls broadcast function to send message to all
                message_to_send = "<" + address[0] + "> " + message
                broadcast(message_to_send, connection)
            else:
                remove(connection)
        except:
            continue


def broadcast(message, connection):
    """  """
    for client in list_of_clients:
        if client != connection:
            try:
                client.send(message)
            except:
                client.close()
                remove(client)


def remove(connection):
    """  """
    if connection in list_of_clients:
        list_of_clients.remove(connection)


if __name__ == "__main__":
    ip = str(get_public_ip_address())
    port = 60000

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind(("", port))
    server.listen(10)

    while True:
        connection, address = server.accept()

        list_of_clients.append(connection)

        # prints the address of the user that just connected
        print(address[0] + " connected")

        # creates and individual thread for every user that connects
        start_new_thread(clientthread,(connection,address))

    connection.close()
    server.close()
