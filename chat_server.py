#!/usr/bin/env python3

import socket
import select
import sys

import requests
import json

from _thread import *


class chat_server():
    """  """

    def __init__(self, port):
        """  """
        self.listOfClients = []

        self.host = self.get_public_ip_address()
        self.port = port

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.server.bind(("", self.port))
        self.server.listen(10)


    def get_public_ip_address(self):
        """ Send a request to ipinfo.io to retreive public ip address. """
        response = requests.get("https://ipinfo.io/json", verify = True)
        if response.status_code != 200:
            print("Status: " + response.status_code + ". Problem with the request. Exiting")
            exit()
        data = response.json()
        return data["ip"]


    def client_thread(self, connection, address):
        """  """
        connection.send("Welcome to this chatroom!".encode())

        while True:
            try:
                message = connection.recv(2048)
                if message.decode() != "":
                    print("<" + str(address[0]) + "> " + message.decode())
                    message_to_send = "<" + str(address[0]) + "> " + message.decode()
                    self.broadcast(message_to_send, connection)
            except:
                self.remove(connection, address)
                break


    def broadcast(self, message, connection):
        """ Broadcasts the message to all other clients. """
        for (conn, address) in self.listOfClients:
            if conn != connection:
                try:
                    conn.send(message.encode())
                except:
                    conn.close()
                    self.remove(conn, address)


    def remove(self, connection, address):
        """  """
        if (connection, address) in self.listOfClients:
            print(str(address[0]) + " left the chat.")
            self.listOfClients.remove((connection, address))


    def run(self):
        """  """
        print("Server hosted on:")
        print("IP Address:   " + self.host)
        print("port:         " + str(self.port))

        while True:
            try:
                connection, address = self.server.accept()

                self.listOfClients.append((connection, address))

                print(address[0] + " connected!")

                start_new_thread(self.client_thread, (connection, address))
            except:
                break

        connection.close()
        self.server.close()



if __name__ == "__main__":
    cs = chat_server(60000)
    cs.run()
