import curses
import time

screen = curses.initscr()
curses.noecho()
screenSize = screen.getmaxyx()

screenHeight = screenSize[0]
screenWidth = screenSize[1]

textbox = []
inputString = ""

char = None
while True:
    screen.clear()
    for index, line in enumerate(textbox):
        screen.addstr(index, 0, line)
    screen.addstr(screenHeight-1, 0, "> " + inputString)
    screen.refresh()
    char = screen.getch()
    if char == 27: # ESC
        break
    elif char == 10: # ENTER
        if inputString != "":
            if len(textbox) == screenHeight-2:
                textbox.pop(0)
            textbox.append(inputString)
            inputString = ""
    elif char == 8: # BACKSPACE
        if inputString != "":
            inputString = inputString[:-1]
    else:
        if len(inputString) == screenWidth-6:
            pass
        else:
            inputString += str(chr(char))

curses.endwin()
