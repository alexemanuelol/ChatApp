#!/usr/bin/env python3

import socket
import select
import sys
import readchar
import curses
import time
import os
import datetime
import pickle
import pyaudio

from textwrap import wrap
from _thread import *


class chat_client():
    """  """

    def __init__(self, host, portChat, portVoice):
        """ Class initialization. """
        self.screen = curses.initscr()
        self.screen.keypad(True)
        curses.noecho()

        curses.start_color()
        curses.use_default_colors()

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

        self.host = host
        self.portChat = portChat
        self.portVoice = portVoice

        self.clientChat = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientVoice = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientChat.connect((self.host, self.portChat))

        self.chatActive = True
        self.voiceActive = False

        self.messages = []
        self.lineQueue = []
        self.scrollIndex = 0

        self.inputString = ""

        self.cursorPos = 0
        self.visualCursorPos = 0

        self.visualLeftPos = 0
        self.visualRightPos = 0

        # PyAudio
        chunk_size = 1024
        audio_format = pyaudio.paInt16
        channels = 1
        rate = 20000

        self.p = pyaudio.PyAudio()
        self.playing_stream = self.p.open(format=audio_format, channels=channels, rate=rate, output=True, frames_per_buffer=chunk_size)
        self.recording_stream = self.p.open(format=audio_format, channels=channels, rate=rate, input=True, frames_per_buffer=chunk_size)

    def __receive_thread(self):
        """  """
        while self.chatActive:
            try:
                received = self.clientChat.recv(2048)
                package = pickle.loads(received)

                if len(package) == 4:
                    pType = package[0]
                    pRequ = package[1]
                    pFrom = package[2]
                    pData = package[3]

                    if pType == 0:          # Forward type
                        self.append_message(pFrom, pData, self.get_time(), curses.color_pair(self.colors["green"]))
                        self.update()

                    elif pType == 1:        # Notification type
                        self.append_notification(pFrom, pData, self.get_time(), curses.color_pair(self.colors["yellow"]))
                        self.update()

                    elif pType == 2:        # Request type
                        if pRequ == 0:          # Users online
                            for line in pData:
                                if self.scrollIndex != 0:
                                    self.scrollIndex -= 1
                                self.messages.append([line, curses.color_pair(self.colors["yellow"])])
                                self.lineQueue.append([line, curses.color_pair(self.colors["yellow"])])
                            self.update()

            except Exception as e:
                #print(repr(e))
                continue


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


    def update_message_formatting(self):
        """ Update messages dependent on screen width. """
        self.lineQueue = []
        for message, color in self.messages:
            lines = wrap(message, self.screenWidth)
            for line in lines:
                self.lineQueue.append([line, color])


    def update_visual_cursor(self):
        """ Update the visual cursor in the inputbox. """
        self.screen.move(self.screenHeight-1, self.visualCursorPos+2)


    def update_refresh(self):
        """ Refresh the screen. """
        self.screen.refresh()


    def update(self):
        """ Update all. """
        self.screen.clear()
        self.update_screen_size()
        self.update_textbox()
        self.update_inputbox()
        self.update_visual_cursor()
        self.update_refresh()


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


    def command_handler(self, string):
        """  """
        if string.startswith("!setNickname "):
            string = string.replace("!setNickname ", "")
            self.clientChat.send(pickle.dumps([2, 0, string]))
            return True
        elif string == "!users":
            self.clientChat.send(pickle.dumps([2, 1, string]))
            return True
        elif string == "!voice":
            if self.voiceActive:
                self.voiceActive = False
                self.clientVoice.close()
            else:
                self.voiceActive = True
                self.clientVoice.connect((self.host, self.portVoice))
                start_new_thread(self.voice_receive, ())
                start_new_thread(self.voice_send, ())
            return True

        return False


    def voice_receive(self):
        """  """
        while self.voiceActive:
            try:
                data = self.clientVoice.recv(1024)
                self.playing_stream.write(data)
            except:
                pass


    def voice_send(self):
        """  """
        while self.voiceActive:
            try:
                data = self.recording_stream.read(1024)
                self.clientVoice.sendall(data)
            except:
                pass


    def run(self):
        """  """
        self.update()

        start_new_thread(self.__receive_thread, ())

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
                        self.clientChat.send(pickle.dumps([0, 0, self.inputString]))
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

        curses.endwin()

    def exit(self):
        """  """
        self.voiceActive = False
        self.chatActive = False



if __name__ == "__main__":
    client = chat_client("81.26.242.196", 60000, 60001)
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
