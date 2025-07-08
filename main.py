import os
from InquirerPy import inquirer
from src import voice, listen
from src.constants import QUESTION_1, OPTIONS_1

# clear the console screen
os.system("cls" if os.name == "nt" else "clear")

while True:
    # Prompt the user to select an operation
    op = inquirer.select(
        message = QUESTION_1,
        choices = OPTIONS_1
    ).execute()
    os.system("cls" if os.name == "nt" else "clear")    # clear the console screen

    if op == OPTIONS_1[0]:
        voice.start_voicing()
    elif op == OPTIONS_1[1]:
        pass
    elif op == OPTIONS_1[2]:
        break