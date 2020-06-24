#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import json
import pickle
import re
import requests
import select
import socket
import sys
import time

from _thread import *
from badwords import badwords
from emojis import emojis
from inspect import currentframe, getframeinfo

class chat_server():
    """  """

    def __init__(self, portChat, portVoice):
        """  """
        # Constants
        self.MAX_USERS = 10

        # Initialize config
        self.config = configparser.ConfigParser()
        self.config.read("config.ini", encoding="utf-8")

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
        self.socketVoice.listen(self.MAX_USERS - 8)

        # Initialize lists to store active clients
        self.clientsChat = []
        self.clientsVoice = []

        # Password
        self.password = str(self.config["General"]["password"])


    def run(self):
        """ The main function call. """
        print("Server hosted on:")
        print("IP Address:   " + self.host)
        print("port chat:    " + str(self.portChat))
        print("port voice:   " + str(self.portVoice))

        start_new_thread(self.__wait_incoming_voice_request, ())
        self.__wait_incoming_chat_request()


    def __wait_incoming_voice_request(self):
        """ Constantly wait for a incoming socket connect request for voice. """
        while True:
            try:
                # Wait for incoming connection request
                connection, address = self.socketVoice.accept()

                nickname = self.get_nickname(address[0])

                userOnline = False
                for conn, add in self.clientsChat:
                    if address[0] == add[0]:
                        userOnline = True

                if userOnline and nickname != False:
                    print(nickname + " joined voice chat.")

                    # Append connection to clientsVoice
                    self.clientsVoice.append((connection, address))

                    # Start voice thread
                    start_new_thread(self.__voice_thread, (connection, address))
                else:
                    connection.close()

            except Exception as e:
                print("LINE: " + str(getframeinfo(currentframe()).lineno) + ", EXCEPTION: " + '"' + str(e) + '"')
                break

        connection.close()
        self.socketVoice.close()


    def __wait_incoming_chat_request(self):
        """ Constantly wait for a incoming socket connect request for chat. """
        while True:
            # Wait for incoming connection request
            connection, address = self.socketChat.accept()

            start_new_thread(self.__init_new_user, (connection, address))

        connection.close()
        self.socketChat.close()


    def __init_new_user(self, connection, address):
        """ Setup a new user. """
        try:
            # Set initial nickname
            self.set_nickname(address[0])

            # Password check
            print(self.get_nickname(address[0]) + " just entered password mode.")
            if not self.password_check(connection):
                return

            print(self.get_nickname(address[0]) + " connected!")

            # Append connection to clientsChat
            self.clientsChat.append((connection, address))
            self.chat_send(1, "SERVER", "Welcome to ChatApp!", connection)

            # Start chat thread
            start_new_thread(self.__chat_thread, (connection, address))
        except Exception as e:
            print("LINE: " + str(getframeinfo(currentframe()).lineno) + ", EXCEPTION: " + '"' + str(e) + '"')


    def __voice_thread(self, connection, address):
        """ Individual voice thread for clients. """
        nickname = self.get_nickname(address[0])
        self.chat_broadcast(1, "SERVER", nickname + " just joined voice chat.")
        while True:
            try:
                data = connection.recv(1024)
                self.voice_broadcast(data, connection)

            except Exception as e:
                #print("LINE: " + str(getframeinfo(currentframe()).lineno) + ", EXCEPTION: " + '"' + str(e) + '"')
                self.remove_voice(connection, address)
                break


    def __chat_thread(self, connection, address):
        """ Individual chat thread for clients. """
        nickname = self.get_nickname(address[0])
        time.sleep(.5)
        self.send_update_online_users()
        self.chat_broadcast(1, "SERVER", nickname + " just connected.", connection)


        while True:
            try:
                received = connection.recv(2048)

                package = pickle.loads(received)
                print("Incoming package from < " + nickname + " >: " + str(package))

                if len(package) == 2:
                    pRequ = package[0]      # Request
                    pData = package[1]      # Data

                    if pRequ == 0:              # Forward message
                        print("< " + nickname + " > " + pData)
                        pData = self.replace_emojis(pData)                  # Replace emojis
                        pData = self.replace_badwords(pData)                # Replace badwords
                        self.chat_send(5, "SERVER", pData, connection)
                        self.chat_broadcast(0, nickname, pData, connection)

                    elif pRequ == 1:            # Nickname change
                        oldNickname = self.get_nickname(address[0])
                        pData = self.replace_emojis(pData)                  # Replace emojis
                        pData = self.replace_badwords(pData)                # Replace badwords
                        self.set_nickname(address[0], pData)
                        nickname = self.get_nickname(address[0])
                        print("< SERVER > " + oldNickname + " changed nickname to " + nickname)
                        self.chat_broadcast(1, "SERVER", oldNickname + " changed nickname to " + nickname)
                        self.send_update_online_users()

                    elif pRequ == 2:            # Users online
                        users = self.get_users(connection)
                        self.chat_send(2, None, users, connection)

                    elif pRequ == 3:            # Notify all, nickname's mic has been muted
                        self.chat_broadcast(1, "SERVER", nickname + " just muted mic.")
                        self.send_update_online_users()

                    elif pRequ == 4:            # Notify all, nickname's mic has been unmuted
                        self.chat_broadcast(1, "SERVER", nickname + " just unmuted mic.")
                        self.send_update_online_users()

                    elif pRequ == 5:            # Notify all, nickname's headset has been mute
                        self.chat_broadcast(1, "SERVER", nickname + " just muted headset.")
                        self.send_update_online_users()

                    elif pRequ == 6:            # Notify all, nickname's headset has been unmuted
                        self.chat_broadcast(1, "SERVER", nickname + " just unmuted headset.")
                        self.send_update_online_users()


            except Exception as e:
                print("LINE: " + str(getframeinfo(currentframe()).lineno) + ", EXCEPTION: " + '"' + str(e) + '"')
                self.remove_chat(connection, address)
                break


    def voice_broadcast(self, data, ignored = None):
        """ Broadcasts the voice to all other clients. """
        for (connection, address) in self.clientsVoice:
            if connection != ignored:
                try:
                    connection.send(data)
                except:
                    connection.close()
                    self.remove_voice(connection, address)


    def chat_broadcast(self, pType, pFrom, pData, ignored = None):
        """ Broadcasts the message to all other clients. """
        for (connection, address) in self.clientsChat:
            if connection != ignored:
                try:
                    connection.send(pickle.dumps([pType, pFrom, pData]))
                except:
                    connection.close()
                    self.remove_chat(connection, address)


    def chat_send(self, pType, pFrom, pData, pTo):
        """ Send a message to a specified receiver. """
        for (connection, address) in self.clientsChat:
            if connection == pTo:
                try:
                    connection.send(pickle.dumps([pType, pFrom, pData]))
                except:
                    connection.close()
                    self.remove_chat(connection, address)


    def remove_voice(self, connection, address):
        """ Remove the connection from clientsVoice list. """
        if (connection, address) in self.clientsVoice:
            nickname = self.get_nickname(address[0])
            print(nickname + " just left voice chat.")
            self.chat_broadcast(1, "SERVER", nickname + " just left voice chat.")
            try:
                self.clientsVoice.remove((connection, address))
            except:
                pass


    def remove_chat(self, connection, address):
        """ Remove the connection from clientsChat list. """
        if (connection, address) in self.clientsChat:
            nickname = self.get_nickname(address[0])
            print(nickname + " just disconnected.")
            self.chat_broadcast(1, "SERVER", nickname + " just disconnected.", connection)
            try:
                self.clientsChat.remove((connection, address))
                self.send_update_online_users()
            except:
                pass


    def password_check(self, connection):
        """ Security before entering the chat. """
        while True:
            try:
                received = connection.recv(1024).decode()
                if received != None and received != "":
                    if received == self.password:
                        connection.send(pickle.dumps([4, "SERVER", "Correct password."]))
                        return True
                    else:
                        connection.send(pickle.dumps([4, "SERVER", "Invalid password, please try again."]))
            except:
                connection.close()
                return False


    def replace_emojis(self, string):
        """ Append emojis to string. """
        for key, value in emojis.items():
            if key in string:
                string = string.replace(key, emojis[key])
        return string


    def replace_badwords(self, string):
        """ Replace bad words with ****. """
        copy = string
        stringLowercase = string.lower()
        for word in badwords:
            if word in stringLowercase:
                replacement = len(word) * "*"
                for match in re.finditer(word, stringLowercase):
                    copy = copy[:match.start()] + replacement + copy[match.end():]
        return copy


    def write_config(self):
        """ Write to config file. """
        with open("config.ini", "w", encoding="utf-8") as configfile:
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
        """ Get the nickname associated with the ip. """
        if self.config.has_option("Users", ip):
            return self.config["Users"][ip]
        return False


    def set_nickname(self, ip, nickname = None):
        """ Set a nickname for a specific ip. """
        if nickname == None:
            if not self.config.has_option("Users", ip):
                self.config["Users"][ip] = ip
        else:
            self.config["Users"][ip] = nickname
        self.write_config()
        self.config.read("config.ini", encoding="utf-8")


    def send_update_online_users(self):
        """ Update all clients about online users. """
        users = self.get_users()
        self.chat_broadcast(3, None, users)



    def get_users(self, ignored = None):
        """ Returns a list of all connected users. """
        users = []
        for (connection, address) in self.clientsChat:
            if connection != ignored:
                users.append(self.get_nickname(address[0]))
        return users



if __name__ == "__main__":
    cs = chat_server(60000, 60001)
    cs.run()
