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
        # Constants
        self.MAX_USERS = 10

        # Initialize config
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")

        # Setup host ip and ports
        self.host = self.get_public_ip_address()
        self.portChat = portChat
        self.portVoice = portVoice

        # Socket Chat
        self.socketChat = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socketChat.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socketChat.bind(("", self.portChat))
        self.socketChat.listen(self.MAX_USERS)

        # Socket Voice
        self.socketVoice = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socketVoice.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socketVoice.bind(("", self.portVoice))
        self.socketVoice.listen(self.MAX_USERS)

        self.clientsChat = []
        self.clientsVoice = []


    def run(self):
        """  """
        print("Server hosted on:")
        print("IP Address:   " + self.host)
        print("port chat:    " + str(self.portChat))
        print("port voice:   " + str(self.portVoice))

        start_new_thread(self.wait_incoming_voice_request, ())
        self.wait_incoming_chat_request()


    def wait_incoming_voice_request(self):
        """  """
        while True:
            try:
                # Wait for incoming connection request
                connection, address = self.socketVoice.accept()

                # Append connection to clientsVoice
                self.clientsVoice.append((connection, address))

                # Start voice thread
                start_new_thread(self.voice_thread, (connection, address))
            except Exception as e:
                #print(repr(e))
                break

        connection.close()
        self.socketVoice.close()


    def wait_incoming_chat_request(self):
        """  """
        while True:
            try:
                # Wait for incoming connection request
                connection, address = self.socketChat.accept()

                # Set initial nickname
                self.set_nickname(address[0])
                username = self.get_nickname(address[0])
                print(username + " connected!")

                # Append connection to clientsChat
                self.clientsChat.append((connection, address))

                # Start chat thread
                start_new_thread(self.chat_thread, (connection, address))
            except Exception as e:
                #print(repr(e))
                break

        connection.close()
        self.socketChat.close()


    def voice_thread(self, connection, address):
        """  """
        while True:
            try:
                data = connection.recv(1024)
                self.broadcast_voice(data, connection)

            except Exception as e:
                #print(repr(e))
                self.remove(connection, address, self.clientsVoice)
                break


    def chat_thread(self, connection, address):
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
                self.remove(connection, address, self.clientsChat)
                break


    def remove(self, connection, address, clientsList):
        """  """
        if (connection, address) in clientsList:
            nickname = self.get_nickname(address[0])
            print(nickname + " just disconnected.")
            self.broadcast(1, 0, "SERVER", nickname + " just disconnected.", connection)
            self.clientsList.remove((connection, address))


    def broadcast_chat(self, pType, pRequ, pFrom, pData, ignored = None):
        """ Broadcasts the message to all other clients. """
        for (connection, address) in self.clientsChat:
            if connection != ignored:
                try:
                    connection.send(pickle.dumps([pType, pRequ, pFrom, pData]))
                except:
                    connection.close()
                    self.remove(connection, address, self.clientsChat)


    def broadcast_voice(self, data, ignored = None):
        """ Broadcasts the voice to all other clients. """
        for (connection, address) in self.clientsVoice:
            if connection != ignored:
                try:
                    connection.send(data)
                except:
                    connection.close()
                    self.remove(connection, address, self.clientsVoice)


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



if __name__ == "__main__":
    cs = chat_server(60000, 60001)
    cs.run()
