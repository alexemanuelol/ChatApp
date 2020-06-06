#!/usr/bin/env python3

import socket
import select
import sys
import configparser
import pickle

import requests
import json

from _thread import *


class chat_server():
    """  """

    def __init__(self, port):
        """  """
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")

        self.host = self.get_public_ip_address()
        self.port = port

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.server.bind(("", self.port))
        self.server.listen(10)

        self.clients = []


    def write_config(self):
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


    def client_thread(self, connection, address):
        """  """
        nickname = self.get_nickname(address[0])
        connection.send(pickle.dumps([1, 0, "SERVER", "Welcome to ChatApp!"]))
        self.broadcast(1, 0, "SERVER", nickname + " just connected.", connection)

        while True:
            try:
                received = connection.recv(2048)
                package = pickle.loads(received)
                print("Incoming package: " + str(package))
                if len(package) == 3:
                    pType = package[0]
                    pRequ = package[1]
                    pData = package[2]

                    if pType == 0:          # Forward type
                        print("< " + nickname + " > " + pData)
                        self.broadcast(0, 0, nickname, pData, connection)

                    elif pType == 1:        # Notification type
                        pass

                    elif pType == 2:        # Request type
                        if pRequ == 0:          # Nickname change
                            oldNickname = self.get_nickname(address[0])
                            self.set_nickname(address[0], pData)
                            nickname = self.get_nickname(address[0])
                            print("< SERVER > " + oldNickname + " changed nickname to " + nickname)
                            self.broadcast(1, 0, "SERVER", oldNickname + " changed nickname to " + nickname)
                        elif pRequ == 1:        # Users online
                            users = self.get_users(connection)
                            connection.send(pickle.dumps([2, 0, None, users]))

            except Exception as e:
                #print(e)
                self.remove(connection, address)
                break


    def broadcast(self, pType, pRequ, pFrom, pData, ignored = None):
        """ Broadcasts the message to all other clients. """
        for (connection, address) in self.clients:
            if connection != ignored:
                try:
                    connection.send(pickle.dumps([pType, pRequ, pFrom, pData]))
                except:
                    connection.close()
                    self.remove(connection, address)


    def remove(self, connection, address):
        """  """
        if (connection, address) in self.clients:
            nickname = self.get_nickname(address[0])
            print(nickname + " just disconnected.")
            self.broadcast(1, 0, "SERVER", nickname + " just disconnected.", connection)
            self.clients.remove((connection, address))


    def get_nickname(self, ip):
        """  """
        if self.config.has_option("Users", ip):
            return self.config["Users"][ip]
        return False


    def set_nickname(self, ip, nickname = None):
        """  """
        if nickname == None:
            if not self.config.has_option("Users", ip):
                self.config["Users"][ip] = ip
        else:
            self.config["Users"][ip] = nickname
        self.write_config()
        self.config.read("config.ini")


    def get_users(self, ignored = None):
        """  """
        users = []
        for (connection, address) in self.clients:
            if connection != ignored:
                users.append(self.get_nickname(address[0]))
        return users


    def run(self):
        """  """
        print("Server hosted on:")
        print("IP Address:   " + self.host)
        print("port:         " + str(self.port))

        while True:
            try:
                connection, address = self.server.accept()

                # Set initial nickname
                self.set_nickname(address[0])
                username = self.get_nickname(address[0])

                print(username + " connected!")

                # Append connection to currently connected clients
                self.clients.append((connection, address))

                # Start client read thread
                start_new_thread(self.client_thread, (connection, address))
            except Exception as e:
                #print(e)
                break

        connection.close()
        self.server.close()



if __name__ == "__main__":
    cs = chat_server(60000)
    cs.run()
