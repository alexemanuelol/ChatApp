#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import json
import os
import requests
import socket
import sys
import threading
import time
from inspect import currentframe, getframeinfo

from badwords import replace_badwords
from emojis import translate_emojis

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + "/common/")

import pkg_type as pt


class ChatAppServer():
    """ ChatAppServer. """

    def __init__(self, port):
        """ Class initialization.
            Arguments:
                port                - The port of the socket.       (str)
        """
        # Initialize config
        self.config = configparser.ConfigParser()
        self.config.read("config.ini", encoding="utf-8")

        # Setup host ip and ports for socket
        self.host = self.get_public_ip_address()
        self.port = port
        self.socket = None

        # General variables
        self.MAX_CLIENTS = 10
        self.clients = list()
        self.password = str(self.config["General"]["password"])


    def start(self):
        """ Start ChatApp server. """
        # Initialize Chat Socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("", self.port))
        self.socket.listen(self.MAX_CLIENTS)

        print("Server hosted on:")
        print(f"IP Address:  {self.host}")
        print(f"port:        {str(self.port)}")

        # Start the wait incoming chat connections thread
        self.__wait_incoming_connections()


    def stop(self):
        """ Stop ChatApp server. """
        self.socket.close()


    def __wait_incoming_connections(self):
        """ Constantly wait for a incoming connection requests. """
        while True:
            # Wait for incoming connection request
            connection, address = self.socket.accept()

            event = threading.Event()
            thread = threading.Thread(target=self.__init_new_client, args=(event, connection, address))
            thread.start()

        connection.close()
        self.stop()


    def __init_new_client(self, event, connection, address):
        """ Setup a new user.
            Arguments:
                event               - Unused argument.          (threading.Event)
                connection          - The client connection.    (connection)
                address             - The client address        (address)
        """
        try:
            # Set initial nickname
            self.set_nickname(address[0])
            nickname = self.get_nickname(address[0])

            # Password check function
            print(f"{nickname} just entered password mode.")
            if not self.password_check(connection):
                return

            print(f"{nickname} connected!")

            # Append connection to clientsChat
            self.clients.append((connection, address))
            self.send_package(pt.P_TYPE["notify"], "Welcome to ChatApp!", "chat_info", "SERVER", connection)

            # Start chat thread
            event = threading.Event()
            thread = threading.Thread(target=self.__chat_thread, args=(event, connection, address))
            thread.start()
        except Exception as e:
            lineNumber = str(getframeinfo(currentframe()).lineno)
            print(f"EXCEPTION:\n    {str(e)}\n    LINE:  {lineNumber}")


    def __chat_thread(self, event, connection, address):
        """ Individual chat thread for clients.
            Arguments:
                event               - Unused argument.          (threading.Event)
                connection          - The client connection.    (connection)
                address             - The client address        (address)
        """
        nickname = self.get_nickname(address[0])
        self.send_update_online_users()
        self.broadcast_package(pt.P_TYPE["notify"], f"{nickname} just connected.", "chat_info", "SERVER", connection)

        while True:
            try:
                recv = connection.recv(2048)
                pkg = json.loads(recv.decode("utf-8"))

                if not pt.valid_package(pkg, False):
                    print(f"INVALID PACKAGE: {str(pkg)}")
                    continue

                print(f"Incoming package from < {nickname} >: {str(pkg)}")

                if pkg["type"] == pt.P_TYPE["command"]:
                    if pkg["info"] == "stop":
                        connection.close()
                        self.remove_client(connection, address)
                        break
                    elif pkg["info"] == "setNickname":
                        oldNickname = self.get_nickname(address[0])
                        data = pkg["data"]
                        data = translate_emojis(data)           # Replace emojis
                        data = replace_badwords(data)      # Replace badwords
                        self.set_nickname(address[0], data)
                        nickname = self.get_nickname(address[0])
                        text = f"< SERVER > {oldNickname} changed nickname to {nickname}"
                        print(text)
                        self.broadcast_package(pt.P_TYPE["notify"], text, "chat_info", "SERVER")
                        self.send_update_online_users()

                elif pkg["type"] == pt.P_TYPE["message"]:
                    print(f"< {nickname} > {pkg['data']}")
                    data = pkg["data"]
                    data = translate_emojis(data)           # Replace emojis
                    data = replace_badwords(data)      # Replace badwords
                    self.broadcast_package(pt.P_TYPE["message"], data, None, nickname)

                elif pkg["type"] == pt.P_TYPE["notify"]:
                    pass

                elif pkg["type"] == pt.P_TYPE["error"]:
                    pass

            except Exception as e:
                lineNumber = str(getframeinfo(currentframe()).lineno)
                print(f"EXCEPTION:\n    {str(e)}\n    LINE:  {lineNumber}")
                connection.close()
                self.remove_client(connection, address)
                break


    def broadcast_package(self, pType, pData, pInfo, pInitiator, ignore=None):
        """ Broadcast a package to clients.
            Arguments:
                pType               - The type of package.                  (int)
                pData               - The data of the package.              (any)
                pInfo               - Additional info about the package     (any)
                pInitiator          - The initiator of the package.         (str)
                ignore              - Connection to be ignored.             (connection)
        """
        package = pt.create_package(pType, pData, pInfo, pInitiator)

        for (connection, address) in self.clients:
            if connection != ignore:
                try:
                    connection.send(package)
                except:
                    connection.close()
                    self.remove_client(connection, address)


    def send_package(self, pType, pData, pInfo, pInitiator, to):
        """ Send a package to a specific client.
            Arguments:
                pType               - The type of package.                  (int)
                pData               - The data of the package.              (any)
                pInfo               - Additional info about the package     (any)
                pInitiator          - The initiator of the package.         (str)
                to                  - The client connection to send to.     (connection)
        """
        package = pt.create_package(pType, pData, pInfo, pInitiator)

        for (connection, address) in self.clients:
            if connection == to:
                try:
                    connection.send(package)
                except:
                    connection.close()
                    self.remove_client(connection, address)
                return


    def remove_client(self, connection, address):
        """ Remove the connection from clients list.
            Arguments:
                connection          - The client connection.    (connection)
                address             - The client address        (address)
        """
        if (connection, address) in self.clients:
            nickname = self.get_nickname(address[0])
            text = f"{nickname} just disconnected."
            print(text)
            self.broadcast_package(pt.P_TYPE["notify"], text, "chat_info", "SERVER", connection)
            try:
                self.clients.remove((connection, address))
                self.send_update_online_users()
            except:
                pass


    def password_check(self, connection):
        """ Continous loop that check incoming data for correct password.
            Arguments:
                connection          - The client connection.    (connection)
        """
        while True:
            try:
                recv = connection.recv(2048).decode()
                if recv != None and recv != "":
                    if recv == self.password:
                        package = pt.create_package(pt.P_TYPE["command"], "Correct password", "password", None)
                        connection.send(package)
                        time.sleep(.5) # Needed so that package gets sent
                        return True
                    else:
                        package = pt.create_package(pt.P_TYPE["command"], "Invalid password", "password", None)
                        connection.send(package)
            except:
                connection.close()
                return False


    def send_update_online_users(self):
        """ Update all clients about online users. """
        users = self.get_users()
        self.broadcast_package(pt.P_TYPE["command"], users, "updateUsers", "SERVER")


    def get_users(self):
        """ Returns a list of all connected users. """
        users = []
        for (connection, address) in self.clients:
            users.append(self.get_nickname(address[0]))
        return users


    def get_public_ip_address(self):
        """ Send a request to ipinfo.io to retreive public ip address. """
        response = requests.get("https://ipinfo.io/json", verify = True)
        if response.status_code != 200:
            print(f"Status: {resplose.status_code}. Problem with the request.")
            return None
        data = response.json()
        return data["ip"]


    def write_config(self):
        """ Write to config file. """
        with open("config.ini", "w", encoding="utf-8") as configfile:
            self.config.write(configfile)


    def get_nickname(self, ip):
        """ Get the nickname of a specific client ip.
            Arguments:
                ip              - The ip address to check in the config.ini file.       (str)
        """
        if self.config.has_option("Users", ip):
            return self.config["Users"][ip]
        return False


    def set_nickname(self, ip, nickname=None):
        """ Set the nickname of a specific client ip.
            Arguments:
                ip              - The client ip.            (str)
                nickname        - The nickname to be set.   (str)
        """
        if nickname == None:
            if not self.config.has_option("Users", ip):
                self.config["Users"][ip] = ip
        else:
            self.config["Users"][ip] = nickname
        self.write_config()
        self.config.read("config.ini", encoding="utf-8")




if __name__ == "__main__":
    port = 60000
    cas = ChatAppServer(port)
    cas.start()
