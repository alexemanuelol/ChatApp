#!/usr/bin/env python3

import socket
import select
import sys

from _thread import *

HOST = SERVER_IP
#HOST = "127.0.0.1"
PORT = 60000

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

def receive():
    while True:
        try:
            msg = sock.recv(10).decode("utf-8")
            print(msg)
        except OSError:
            break


start_new_thread(receive,())

while True:
    command = input()
    if command == "!q":
        sock.close()
        exit()
    sock.sendall(command.encode("utf-8"))

#with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#    s.connect((HOST, PORT))
#    s.sendall(b'Hello, world')
#    data = s.recv(1024)

#print('Received', repr(data))



#server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#if len(sys.argv) != 3:
#    print("Correct usage: script, IP address, port number")
#    exit()

#IP_address = str(sys.argv[1])
#Port = int(sys.argv[2])
#IP_address = "127.0.0.1"
#Port = 60000
#server.connect((IP_address, Port))
#
#while True:
#    # maintains a list of possible input streams
#    sockets_list = [sys.stdin, server]
#
#    """ There are two possible input situations. Either the
#    user wants to give  manual input to send to other people,
#    or the server is sending a message  to be printed on the
#    screen. Select returns from sockets_list, the stream that
#    is reader for input. So for example, if the server wants
#    to send a message, then the if condition will hold true
#    below.If the user wants to send a message, the else
#    condition will evaluate as true"""
#    read_sockets,write_socket, error_socket = select.select(sockets_list,[],[])
#
#    for socks in read_sockets:
#        if socks == server:
#            message = socks.recv(2048)
#            print(message)
#        else:
#            message = sys.stdin.readline()
#            server.send(message)
#            sys.stdout.write("<You>")
#            sys.stdout.write(message)
#            sys.stdout.flush()
#server.close()
