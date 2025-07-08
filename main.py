from InquirerPy import inquirer
from src import voice, listen

options = [
    "Voice a new book",
    "Listen to a voiced book"
]

# Prompt the user to select an operation
op = inquirer.select(
    message="What do you want to do?",
    choices=options
).execute()

if op == options[0]:
    voice.start_voice()
elif op == options[1]:
    pass
