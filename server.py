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

    def __init__(self, portChat, portVoice):
        """  """
        self.MAX_USERS = 10

        self.config = configparser.ConfigParser()
        self.config.read("config.ini")

        self.host = self.get_public_ip_address()
        self.portChat = portChat
        self.portVoice = portVoice

        # Chat
        self.serverChat = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverChat.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverChat.bind(("", self.portChat))
        self.serverChat.listen(self.MAX_USERS)

        # Voice
        self.serverVoice = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverVoice.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverVoice.bind(("", self.portVoice))
        self.serverVoice.listen(self.MAX_USERS)

        self.clientsChat = []
        self.clientsVoice = []


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
                print("Incoming package from < " + nickname + " >: " + str(package))
                if len(package) == 3:
                    pType = package[0]
                    pRequ = package[1]
                    pData = package[2]

                    if pType == 0:          # Forward type
                        print("< " + nickname + " > " + pData)
                        self.broadcast(0, 0, nickname, pData, connection)

                    elif pType == 1:        # Notification type
                        print(nickname + ":  " + str(len(data)))

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
                #print(repr(e))
                self.remove(connection, address)
                break


    def broadcast(self, pType, pRequ, pFrom, pData, ignored = None):
        """ Broadcasts the message to all other clients. """
        for (connection, address) in self.clientsChat:
            if connection != ignored:
                try:
                    connection.send(pickle.dumps([pType, pRequ, pFrom, pData]))
                except:
                    connection.close()
                    self.remove(connection, address)


    def remove(self, connection, address):
        """  """
        if (connection, address) in self.clientsChat:
            nickname = self.get_nickname(address[0])
            print(nickname + " just disconnected.")
            self.broadcast(1, 0, "SERVER", nickname + " just disconnected.", connection)
            self.clientsChat.remove((connection, address))


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
        for (connection, address) in self.clientsChat:
            if connection != ignored:
                users.append(self.get_nickname(address[0]))
        return users


    def incoming_voice_request(self):
        """  """
        while True:
            try:
                connection, address = self.serverVoice.accept()

                self.clientsVoice.append((connection, address))

                start_new_thread(self.client_voice_thread, (connection, address))
            except Exception as e:
                #print(repr(e))
                pass

    def client_voice_thread(self, connection, address):
        """  """
        while True:
            try:
                data = connection.recv(1024)
                self.broadcast_voice(data, connection)
            except Exception as e:
                #print(repr(e))
                pass

    # TODO broadcast voice


    def run(self):
        """  """
        print("Server hosted on:")
        print("IP Address:   " + self.host)
        print("port chat:    " + str(self.portChat))
        print("port voice:   " + str(self.portVoice))

        start_new_thread(self.incoming_voice_request, ())

        while True:
            try:
                connection, address = self.serverChat.accept()

                # Set initial nickname
                self.set_nickname(address[0])
                username = self.get_nickname(address[0])

                print(username + " connected!")

                # Append connection to currently connected clients
                self.clientsChat.append((connection, address))

                # Start client read thread
                start_new_thread(self.client_thread, (connection, address))
            except Exception as e:
                #print(e)
                break

        connection.close()
        self.serverChat.close()



if __name__ == "__main__":
    cs = chat_server(60000, 60001)
    cs.run()
