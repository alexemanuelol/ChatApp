import curses
import time
import os

from textwrap import wrap


class chat_client():
    """  """

    def __init__(self):
        """  """
        self.screen = curses.initscr()
        self.screen.keypad(True)
        curses.noecho()

        self.screenHeightMin = 13
        self.screenWidthMin = 30

        self.screenHeight, self.screenWidth = self.screen.getmaxyx()
        self.textboxHeight = self.screenHeight - 2
        self.lineWidth = self.screenWidth - 3

        self.lineQueue = []
        self.lineQueueDisplay = []
        self.scrollIndex = 0

        self.inputString = ""
        self.displayStringPos = 0

        self.cursorPos = 0
        self.visualCursorPos = 0

        self.visualLeftPos = 0
        self.visualRightPos = 0


    def update_screen_size(self):
        """  """
        self.screenHeight, self.screenWidth = self.screen.getmaxyx()
        self.textboxHeight = self.screenHeight - 2
        self.lineWidth = self.screenWidth - 3


    def update_input_string_display(self):
        """  """
        displayString = ""
        if len(self.inputString) >= self.lineWidth:
            displayString = self.inputString[self.visualLeftPos:self.visualRightPos]
        else:
            displayString = self.inputString
        self.screen.addstr(self.screenHeight-1, 0, "> " + displayString)


    def update_textbox(self):
        """  """
        displayText = []
        if len(self.lineQueue) >= self.textboxHeight:
            displayText = self.lineQueue[-self.textboxHeight + self.scrollIndex:][:self.textboxHeight]
        else:
            displayText = self.lineQueue

        for index, line in enumerate(displayText):
            self.screen.addstr(index, 0, line)


    def update_visual_cursor(self):
        """  """
        self.screen.move(self.screenHeight-1, self.visualCursorPos+2)


    def update_refresh(self):
        """  """
        self.screen.refresh()


    def update(self):
        """  """
        self.screen.clear()
        self.update_screen_size()
        self.update_textbox()
        self.update_input_string_display()
        self.update_visual_cursor()
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
        self.visualLeftPos = self.cursorPos - self.visualCursorPos
        self.visualRightPos = (self.lineWidth - self.visualCursorPos) + self.cursorPos
        self.update()

        while self.screenWidth > self.screenWidthMin and self.screenHeight > self.screenHeightMin:

            char = self.screen.get_wch()

            if char == "\x1b":                  # ESC KEY
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
                self.screenHeight, self.screenWidth = self.screen.getmaxyx()
            elif char == 262:                   # HOME KEY
                self.visualCursorPos = 0
                self.cursorPos = 0
            elif char == 358:                   # END KEY
                if len(self.inputString) >= self.lineWidth:
                    self.visualCursorPos = self.lineWidth
                else:
                    self.visualCursorPos = len(self.inputString)
                self.cursorPos = len(self.inputString)
            elif char == "\n":                  # ENTER KEY
                self.append_to_line_queue()
                self.scrollIndex = 0
                self.visualCursorPos = 0
                self.cursorPos = 0
            elif char == 330:                   # DELETE KEY
                self.inputString = self.inputString[:self.cursorPos] + self.inputString[self.cursorPos:][1:]

                if len(self.inputString) >= self.lineWidth:
                    if len(self.inputString) == (self.visualRightPos - 1) and self.visualCursorPos != self.lineWidth:
                        self.visualCursorPos += 1
            elif char == "\x08":                # BACKSPACE KEY
                self.inputString = self.inputString[:self.cursorPos][:-1] + self.inputString[self.cursorPos:]

                if self.visualCursorPos != 0 and len(self.inputString) <= self.lineWidth and self.visualLeftPos == 0:
                    self.visualCursorPos -= 1
                elif self.visualCursorPos != 0 and len(self.inputString) >= self.lineWidth and self.visualLeftPos == 0:
                    self.visualCursorPos -= 1
                if self.cursorPos != 0:
                    self.cursorPos -= 1
            else:                               # Append characters to self.inputString
                self.inputString = self.inputString[:self.cursorPos] + str(char) + self.inputString[self.cursorPos:]
                if self.visualCursorPos != self.lineWidth:
                    self.visualCursorPos += 1
                self.cursorPos += 1

            self.visualLeftPos = self.cursorPos - self.visualCursorPos
            self.visualRightPos = self.visualLeftPos + self.lineWidth

            self.update()

        curses.endwin()



if __name__ == "__main__":
    client = chat_client()
    client.run()
