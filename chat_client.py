#!/usr/bin/env python3

import socket
import select
import sys
import readchar

from _thread import *


class chat_client():
    """  """

    def __init__(self, host, port):
        """  """
        self.host = host
        self.port = port

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.host, self.port))

        self.stop = False


    def __receive_thread(self):
        """  """
        while True:
            try:
                data = self.client.recv(1024)
                data = data.decode()
                if data != "":
                    print(data)
            except:
                continue


    def run(self):
        """  """
        start_new_thread(self.__receive_thread, ())

        while True:
            send = input()
            if send != "":
                if send == "!q":
                    self.stop = True
                    break
                self.client.sendall(send.encode())



if __name__ == "__main__":
    print("Enter the password:")
    string = ""
    passwd = "Hejsan"

    while True:
        char = readchar.readkey()

        if char == "\r":
            if string == passwd:
                print("Correct password!")
                break
            else:
                print("Incorrect password, try again...")
                string = ""
                continue

        string += char

    cc = chat_client("81.26.242.196", 60000)
    cc.run()



