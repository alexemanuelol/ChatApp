#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import json
import os
import socket
import sys
import threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + "/terminal-text-boxes/src/")
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + "/common/")

import terminalTextBoxes as ttb
import unicode as uni
import pkg_type as pt


class ChatAppClient():
    """ ChatAppClient. """

    def __init__(self, host, port):
        """ Class initialization.
            Arguments:
                host                - The host IP to connect to.    (str)
                port                - The port of the server.       (int)
        """
        # Initialize terminalTextBoxes
        self.tb = ttb.TerminalTextBoxes(self.character_callback, self.enter_callback)
        self.tb.create_text_box_setup("main")
        self.tb.create_text_box("main", "chat", hOrient=ttb.H_ORIENT["left"], wTextIndent=1, frameAttr="green",
                                frameChar="doubleLine")
        self.tb.create_text_box("main", "info", 25, hOrient=ttb.H_ORIENT["right"], wTextIndent=1, frameAttr="yellow",
                                frameChar="doubleLine", scrollVisable=False)
        self.tb.debug = False
        self.tb.set_focus_box("main", "chat")

        # Socket variables
        self.host = host
        self.port = port
        self.serverComm = None

        # General variables
        self.active = False
        self.onlineUsers = list()
        self.commandPrefix = "!"
        self.passwordMode = True
        self.passwordString = ""


    def start(self):
        """ Start ChatApp client. """
        # Initialize socket
        self.serverComm = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverComm.settimeout(10)
        try:
            self.serverComm.connect((self.host, self.port))
        except:
            print("Could not connect to the server")
            return

        # Start the GUI
        self.tb.start()
        self.add_chat_info_message("SERVER", "Please enter the correct password to enter ChatApp", "yellow")

        # Start the incoming package thread
        self.active = True
        self.__incoming_package_thread()


    def stop(self):
        """ Stop ChatApp client. """
        self.active = False
        self.send_package(pt.P_TYPE["command"], None, "stop", None)
        self.serverComm.close()


    def character_callback(self, character):
        """ Callback function from TerminalTextBoxes module for every key press.
            Arguments:
                character               - The character sent from the TerminalTextBoxes module.     (character)
        """
        if character == "\x1b":
            self.stop()
            return

        # Password mode
        if self.passwordMode and uni.isUnicode(character):
            cPos = self.tb.get_prompt_cursor_pos()
            self.passwordString = self.passwordString[:cPos] + str(character) + self.passwordString[cPos:]
            self.tb.set_prompt_string(len(self.passwordString) * "*")
            return


    def enter_callback(self, message):
        """ Callback function from TerminalTextBoxes module for every enter pressed.
            Arguments:
                message                 - The message received from the TerminalTextBoxes module.   (str)
        """
        if message == "":
            return

        # Password mode
        if self.passwordMode:
            self.serverComm.send(self.passwordString.encode())
            self.passwordString = ""
            return

        # Regular mode
        if not self.command_handler(message):
            # If not a command, send as regular message
            self.send_package(pt.P_TYPE["message"], message, None, None)


    def command_handler(self, string):
        """ Handler for commands.
            Arguments:
                string          - the string to be evaluated as a command or not.       (str)
        """
        p = self.commandPrefix

        # Local commands
        if string == f"{p}c" or string == f"{p}clear":
            self.tb.clear_text_items("main", "chat")
            self.tb.update()
            return True
        elif string == f"{p}getUsers":
            users = str(self.onlineUsers)
            users = users[1:][:-1]
            string = f"Online users: {users}"
            self.add_info_prompt_message(string, "yellow")
            return True


        # Send the command to the server if the command wasn't local
        if string.startswith(self.commandPrefix):
            string = string[len(self.commandPrefix):]
            for command in pt.CLIENT_COMMANDS:
                if string.startswith(command + " "):
                    string = string.replace(command + " ", "")
                    self.send_package(pt.P_TYPE["command"], string, command, None)
                    return True

        return False


    def send_package(self, pType, pData, pInfo, pInitiator):
        """ Send a package to the server.
            Arguments:
                pType               - The type of message P_TYPE.   (int)
                pData               - The data to be sent.          (any)
                pInfo               - Additional info.              (any)
                pInitiator          - The initiator of the message. (str)
        """
        package = pt.create_package(pType, pData, pInfo, pInitiator)
        self.serverComm.send(package)


    def __incoming_package_thread(self):
        """ Thread for incoming package data. """
        while self.active:
            try:
                recv = self.serverComm.recv(2048)
                pkg = json.loads(recv.decode("utf-8"))

                if not pt.valid_package(pkg, False):
                    # Invalid package, skip this time
                    continue

                if pkg["type"] == pt.P_TYPE["command"]:
                    if pkg["info"] == "updateUsers":
                        self.onlineUsers = list()
                        for user in pkg["data"]:
                            self.onlineUsers.append(user)
                        self.update_infobox()
                    elif pkg["info"] == "password":
                        if "Correct" in pkg["data"]:
                            self.add_info_prompt_message(pkg["data"], "green")
                            self.passwordMode = False
                        else:
                            self.add_info_prompt_message(pkg["data"], "red")

                elif pkg["type"] == pt.P_TYPE["message"]:
                    self.add_chat_user_message(pkg["initiator"], pkg["data"], "green")

                elif pkg["type"] == pt.P_TYPE["notify"]:
                    if pkg["info"] == "chat_info":
                        self.add_chat_info_message(pkg["initiator"], pkg["data"], "yellow")
                    elif pkg["info"] == "info_prompt":
                        self.add_info_prompt_message(pkg["data"], "yellow")

                elif pkg["type"] == pt.P_TYPE["error"]:
                    if pkg["info"] == "chat_error":
                        self.add_chat_info_message(pkg["initiator"], pkg["data"], "red")
                    elif pkg["info"] == "info_prompt":
                        self.add_info_prompt_message(pkg["data"], "red")

            except Exception as e:
                pass


    def update_infobox(self):
        """ Update the infobox that displays the online users. """
        self.tb.clear_text_items("main", "info")
        self.tb.add_text_item("main", "info", " Online users:", "yellow")
        for user in self.onlineUsers:
            self.tb.add_text_item("main", "info", f"  - {user}")
        self.tb.update()


    def add_chat_user_message(self, who, message, attributes):
        """ Adds a chat user message to the chat text box.
            Arguments:
                who             - Who initiated the info message.                   (str)
                message         - The message to be added to the chat text box.     (str)
                attributes      - The attributes of the message.                    (str/list)
        """
        who = f"{self.get_time()} < {who} >"
        self.tb.add_text_item("main", "chat", who, ["white", "standout"])
        self.tb.add_text_item("main", "chat", message, attributes)
        self.tb.update()


    def add_chat_info_message(self, who, message, attributes):
        """ Adds info message to the chat text box.
            Arguments:
                who             - Who initiated the info message.                   (str)
                message         - The message to be added to the chat text box.     (str)
                attributes      - The attributes of the message.                    (str/list)
        """
        message = f"{self.get_time()} < {who} > {message}"
        self.tb.add_text_item("main", "chat", message, attributes)
        self.tb.update()


    def add_info_prompt_message(self, message, attributes, timeout=5000):
        """ Adds a message to the info prompt for timeout amount of ms.
            Arguments:
                message         - The message to be added to the info prompt.   (str)
                attributes      - Attributes of the message.                    (str/list)
                timeout         - The timeout before the message disappears.    (int)
        """
        self.tb.set_info_prompt_text_attr(attributes)
        self.tb.set_info_prompt_text(message, timeout)
        self.tb.update()


    def get_time(self):
        """ Returns the current time in format 'HH:MM:SS'. """
        return datetime.datetime.now().strftime("%H:%M:%S")



if __name__ == "__main__":
    host = SERVER_IP
    port = 60000

    cac = ChatAppClient(host, port)
    cac.start()
