import curses
import time
import os

from textwrap import wrap


class chat_client():
    """  """

    def __init__(self):
        """  """
        self.screen = curses.initscr()
        curses.noecho()

        self.screenHeight, self.screenWidth = self.screen.getmaxyx()
        self.textboxHeight = self.screenHeight - 2
        self.lineWidth = self.screenWidth - 3

        self.lineQueue = []
        self.lineQueueDisplay = []

        self.inputString = ""


    def update_screen_size(self):
        """  """
        self.screenHeight, self.screenWidth = self.screen.getmaxyx()
        self.textboxHeight = self.screenHeight - 2
        self.lineWidth = self.screenWidth - 3


    def update_input_string_display(self):
        """  """
        displayString = ""
        if len(self.inputString) >= self.lineWidth:
            displayString = self.inputString[-self.lineWidth:]
        else:
            displayString = self.inputString
        self.screen.addstr(self.screenHeight-1, 0, "> " + displayString)


    def update_textbox(self):
        """  """
        displayText = []
        if len(self.lineQueue) >= self.textboxHeight:
            displayText = self.lineQueue[-self.textboxHeight:]
        else:
            displayText = self.lineQueue

        for index, line in enumerate(displayText):
            self.screen.addstr(index, 0, line)


    def update_refresh(self):
        """  """
        self.screen.refresh()


    def update(self):
        """  """
        self.screen.clear()
        self.update_screen_size()
        self.update_textbox()
        self.update_input_string_display()
        self.update_refresh()


    def append_to_line_queue(self):
        """  """
        if self.inputString != "":
            lines = wrap(self.inputString, self.screenWidth)
            for line in lines:
                self.lineQueue.append(line)
            self.inputString = ""


    def run(self):
        """  """
        while True:
            self.update()
            char = self.screen.getch()
            if char == 27: # ESC
                break
            elif char == curses.KEY_RESIZE:
                self.screenHeight, self.screenWidth = self.screen.getmaxyx()
            elif char == 10: # ENTER
                self.append_to_line_queue()
            elif char == 8 or char == 127: # BACKSPACE
                self.inputString = self.inputString[:-1]
            else:
                self.inputString += str(chr(char))

        curses.endwin()


if __name__ == "__main__":
    client = chat_client()
    client.run()
