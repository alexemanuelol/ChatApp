#!/usr/bin/env python3

import socket
import select
import sys
import configparser

import requests
import json

from _thread import *


class chat_server():
    """  """

    def __init__(self, port):
        """  """
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")

        self.listOfClients = []

        self.host = self.get_public_ip_address()
        self.port = port

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.server.bind(("", self.port))
        self.server.listen(10)

    def save_config(self):
        """  """
        with open("config.ini", "w") as configfile:
            self.config.write(configfile)


    def get_public_ip_address(self):
        """ Send a request to ipinfo.io to retreive public ip address. """
        response = requests.get("https://ipinfo.io/json", verify = True)
        if response.status_code != 200:
            print("Status: " + response.status_code + ". Problem with the request. Exiting")
            exit()
        data = response.json()
        return data["ip"]


    def client_thread(self, connection, address, username):
        """  """
        connection.send("Welcome to this chatroom!".encode())
        self.broadcast(username + " just connected." ,connection)

        while True:
            try:
                message = connection.recv(2048)
                if message.decode() != "":
                    if message.decode().startswith("!setUsername "):
                        self.listOfClients.remove((connection, address, username))
                        oldName = username
                        username = message.decode().replace("!setUsername ", "")
                        self.config["Users"][address[0]] = username
                        self.save_config()
                        self.listOfClients.append((connection, address, username))
                        print("<SERVER> " + oldName + " changed name to " + username)
                        self.broadcast("<SERVER> " + oldName + " changed name to " + username, "placeholder")
                        continue

                    print("<" + username + "> " + message.decode())
                    message_to_send = "<" + username + "> " + message.decode()
                    self.broadcast(message_to_send, connection)
            except:
                self.remove(connection, address, username)
                break


    def broadcast(self, message, connection):
        """ Broadcasts the message to all other clients. """
        for (conn, address, username) in self.listOfClients:
            if conn != connection:
                try:
                    conn.send(message.encode())
                except:
                    conn.close()
                    self.remove(conn, address, username)


    def remove(self, connection, address, username):
        """  """
        if (connection, address, username) in self.listOfClients:
            print(username + " just disconnected.")
            self.broadcast(username + " just disconnected.", connection)
            self.listOfClients.remove((connection, address, username))


    def run(self):
        """  """
        print("Server hosted on:")
        print("IP Address:   " + self.host)
        print("port:         " + str(self.port))

        while True:
            try:
                connection, address = self.server.accept()

                username = ""
                if self.config.has_option("Users", address[0]):
                    username = self.config["Users"][address[0]]
                else:
                    self.config["Users"][address[0]] = address[0]
                    username = address[0]
                self.save_config()

                self.listOfClients.append((connection, address, username))

                print(username + " connected!")

                start_new_thread(self.client_thread, (connection, address, username))
            except:
                break

        connection.close()
        self.server.close()



if __name__ == "__main__":
    cs = chat_server(60000)
    cs.run()
