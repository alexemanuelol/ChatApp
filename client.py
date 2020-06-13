#!/usr/bin/env python3

import curses
import datetime
import os
import pickle
import pyaudio
import readchar
import select
import socket
import sys
import time

from _thread import *
from textwrap import wrap


class chat_client():
    """  """

    def __init__(self, host, portChat, portVoice):
        """ Class initialization. """
        # Curses initialization
        self.screen = curses.initscr()
        self.screen.keypad(True)
        curses.noecho()
        curses.start_color()
        curses.use_default_colors()

        # Colors initialization
        self.colors = {
            "black" : 1,
            "blue" : 2,
            "green" : 3,
            "cyan" : 4,
            "red" : 5,
            "magenta" : 6,
            "yellow" : 7,
            "white" : 8,
        }

        for color, value in self.colors.items():
            curses.init_pair(value, value - 1, -1)

        self.update_screen_size()

        # Socket initialization
        self.host = host
        self.portChat = portChat
        self.portVoice = portVoice
        self.clientChat = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientChat.connect((self.host, self.portChat))
        self.chatActive = True
        self.voiceActive = False

        # Curses display items
        self.inputString = ""
        self.messages = []
        self.lineQueue = []
        self.scrollIndex = 0
        self.cursorPos = 0
        self.visualCursorPos = 0
        self.visualLeftPos = 0
        self.visualRightPos = 0

        # PyAudio
        chunkSize = 1024
        audioFormat = pyaudio.paInt16
        channels = 1
        rate = 20000

        self.pyaudio = pyaudio.PyAudio()
        self.playingStream = self.pyaudio.open( format = audioFormat,
                                                channels = channels,
                                                rate = rate,
                                                output = True,
                                                frames_per_buffer = chunkSize)

        self.recordingStream = self.pyaudio.open(   format = audioFormat,
                                                    channels = channels,
                                                    rate = rate,
                                                    input = True,
                                                    frames_per_buffer = chunkSize)


    def run(self):
        """ The main function call. """
        self.update()

        start_new_thread(self.__chat_thread, ())

        self.__key_handler()

        curses.endwin()


    def __key_handler(self):
        """ Handler of key presses. """
        while True:

            char = self.screen.get_wch()

            if char == "\x1b":                  # ESC KEY
                self.exit()
                break

            elif char == 259:                   # ARROW UP KEY (Scroll up)
                if len(self.lineQueue) + self.scrollIndex > self.textboxHeight:
                    self.scrollIndex -= 1

            elif char == 258:                   # ARROW DOWN KEY (Scroll down)
                if self.scrollIndex != 0:
                    self.scrollIndex += 1

            elif char == 260:                   # ARROW LEFT KEY (Scroll left)
                if self.visualCursorPos != 0:
                    self.visualCursorPos -= 1
                if self.cursorPos != 0:
                    self.cursorPos -= 1

            elif char == 261:                   # ARROW RIGHT KEY (Scroll right)
                if self.visualCursorPos < len(self.inputString) and self.visualCursorPos != self.lineWidth:
                    self.visualCursorPos += 1
                if self.cursorPos < len(self.inputString):
                    self.cursorPos += 1

            elif char == "\x00":                # WINDOWS KEY
                pass

            elif char == curses.KEY_RESIZE:     # RESIZE EVENT
                self.cursorPos = 0
                self.visualCursorPos = 0
                self.update_screen_size()
                self.update_message_formatting()

            elif char == 262:                   # HOME KEY
                self.visualCursorPos = 0
                self.cursorPos = 0

            elif char == 358 or char == 360:    # END KEY
                if len(self.inputString) >= self.lineWidth:
                    self.visualCursorPos = self.lineWidth
                else:
                    self.visualCursorPos = len(self.inputString)
                self.cursorPos = len(self.inputString)

            elif char == "\n":                  # ENTER KEY
                if self.inputString != "":
                    if not self.command_handler(self.inputString):
                        self.append_message("You", self.inputString, self.get_time(), curses.color_pair(self.colors["white"]))
                        self.send(0, self.inputString)
                self.inputString = ""
                self.scrollIndex = 0
                self.visualCursorPos = 0
                self.cursorPos = 0

            elif char == 330:                   # DELETE KEY
                self.inputString = self.inputString[:self.cursorPos] + self.inputString[self.cursorPos:][1:]

                if len(self.inputString) >= self.lineWidth:
                    if len(self.inputString) == (self.visualRightPos - 1) and self.visualCursorPos != self.lineWidth:
                        self.visualCursorPos += 1

            elif char == "\x08" or char == 263: # BACKSPACE KEY
                self.inputString = self.inputString[:self.cursorPos][:-1] + self.inputString[self.cursorPos:]

                if self.visualCursorPos != 0 and len(self.inputString) <= self.lineWidth and self.visualLeftPos == 0:
                    self.visualCursorPos -= 1
                elif self.visualCursorPos != 0 and len(self.inputString) >= self.lineWidth and self.visualLeftPos == 0:
                    self.visualCursorPos -= 1
                if self.cursorPos != 0:
                    self.cursorPos -= 1

            elif char == 339:                   # PAGE UP
                self.scrollIndex -= self.textboxHeight
                if self.scrollIndex < -(len(self.lineQueue) - self.textboxHeight):
                    self.scrollIndex = -(len(self.lineQueue) - self.textboxHeight)

            elif char == 338:                   # PAGE DOWN
                self.scrollIndex += self.textboxHeight
                if self.scrollIndex > 0:
                    self.scrollIndex = 0

            else:                               # Append characters to self.inputString
                self.inputString = self.inputString[:self.cursorPos] + str(char) + self.inputString[self.cursorPos:]
                if self.visualCursorPos != self.lineWidth:
                    self.visualCursorPos += 1
                self.cursorPos += 1

            self.update()


    def __chat_thread(self):
        """ Thread for incoming chat data. """
        while self.chatActive:
            try:
                received = self.clientChat.recv(2048)
                package = pickle.loads(received)

                if len(package) == 3:
                    pType = package[0]
                    pFrom = package[1]
                    pData = package[2]

                    if pType == 0:              # Forward type
                        self.append_message(pFrom, pData, self.get_time(), curses.color_pair(self.colors["green"]))
                        self.update()

                    elif pType == 1:            # Notification type
                        self.append_notification(pFrom, pData, self.get_time(), curses.color_pair(self.colors["yellow"]))
                        self.update()

                    elif pType == 2:            # Users online
                        for line in pData:
                            if self.scrollIndex != 0:
                                self.scrollIndex -= 1
                            self.messages.append([line, curses.color_pair(self.colors["yellow"])])
                            self.lineQueue.append([line, curses.color_pair(self.colors["yellow"])])
                        self.update()

            except Exception as e:
                #print(repr(e))
                continue


    def __voice_receive_thread(self):
        """ Thread for receiving voice data. """
        while self.voiceActive:
            try:
                data = self.clientVoice.recv(1024)
                self.playingStream.write(data)
            except:
                pass


    def __voice_send_thread(self):
        """ Thread for sending voice data. """
        while self.voiceActive:
            try:
                data = self.recordingStream.read(1024)
                self.clientVoice.sendall(data)
            except:
                pass


    def send(self, pRequ, pData):
        """ Send request and data to server. """
        self.clientChat.send(pickle.dumps([pRequ, pData]))


    def command_handler(self, string):
        """ Handler for commands. """
        if string.startswith("!setNickname "):
            string = string.replace("!setNickname ", "")
            self.send(1, string)
            return True

        elif string == "!users":
            self.send(2, string)
            return True

        elif string == "!voice":
            if self.voiceActive:
                self.voiceActive = False
                self.clientVoice.close()
            else:
                self.voiceActive = True
                self.clientVoice = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.clientVoice.connect((self.host, self.portVoice))
                start_new_thread(self.__voice_receive_thread, ())
                start_new_thread(self.__voice_send_thread, ())
            return True

        return False


    def update(self):
        """ Update all. """
        self.screen.clear()
        self.update_screen_size()
        self.update_textbox()
        self.update_inputbox()
        self.update_visual_cursor()
        self.update_refresh()


    def update_screen_size(self):
        """ Update the screen size. """
        self.screenHeight, self.screenWidth = self.screen.getmaxyx()
        self.textboxHeight = self.screenHeight - 2
        self.lineWidth = self.screenWidth - 3


    def update_textbox(self):
        """ Update the textbox with data from self.lineQueue. """
        displayText = []
        if len(self.lineQueue) >= self.textboxHeight:
            displayText = self.lineQueue[-self.textboxHeight + self.scrollIndex:][:self.textboxHeight]
        else:
            displayText = self.lineQueue

        for index, line in enumerate(displayText):
            self.screen.addstr(index, 0, line[0], line[1])


    def update_inputbox(self):
        """ Update the inputbox with data from self.inputString. """
        self.visualLeftPos = self.cursorPos - self.visualCursorPos
        self.visualRightPos = self.visualLeftPos + self.lineWidth

        displayString = ""
        if len(self.inputString) >= self.lineWidth:
            displayString = self.inputString[self.visualLeftPos:self.visualRightPos]
        else:
            displayString = self.inputString
        self.screen.addstr(self.screenHeight-1, 0, "> " + displayString)


    def update_visual_cursor(self):
        """ Update the visual cursor in the inputbox. """
        self.screen.move(self.screenHeight-1, self.visualCursorPos+2)


    def update_refresh(self):
        """ Refresh the screen. """
        self.screen.refresh()


    def update_message_formatting(self):
        """ Update messages dependent on screen width. """
        self.lineQueue = []
        for message, color in self.messages:
            lines = wrap(message, self.screenWidth)
            for line in lines:
                self.lineQueue.append([line, color])


    def append_message(self, sender, message, time, color):
        """ Append a message to self.messages and self.lineQueue. """
        first_line = time + " " + "< " + sender + " >"

        self.messages.append([first_line, curses.color_pair(self.colors["white"]) | curses.A_STANDOUT])
        self.messages.append([message, color])
        lines = wrap(message, self.screenWidth)
        self.lineQueue.append([first_line, curses.color_pair(self.colors["white"]) | curses.A_STANDOUT])

        if self.scrollIndex != 0:
            self.scrollIndex -= 1

        for line in lines:
            if self.scrollIndex != 0:
                self.scrollIndex -= 1
            self.lineQueue.append([line, color])


    def append_notification(self, sender, notification, time, color):
        """  """
        line = time + " < " + sender + " > " + notification

        if self.scrollIndex != 0:
            self.scrollIndex -= 1

        self.messages.append([line, color])
        self.lineQueue.append([line, color])


    def get_time(self):
        """ Returns the current time in format 'HH:MM:SS'. """
        time = datetime.datetime.now().strftime("%H:%M:%S")
        return time


    def exit(self):
        """  """
        self.voiceActive = False
        self.chatActive = False



if __name__ == "__main__":
    client = chat_client(SERVER_IP, 60000, 60001)
    client.run()


# Password code
#print("Enter the password:")
#string = ""
#passwd = "Hejsan"
#
#while True:
#    char = readchar.readkey()
#
#    if char == "\r":
#        if string == passwd:
#            print("Correct password!")
#            break
#        else:
#            print("Incorrect password, try again...")
#            string = ""
#            continue
#
#    string += char
