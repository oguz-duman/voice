"""
Prompt Tree:

└── QUESTION_1 Choose an option:
    ├── OPTIONS_1 Voice a book
        ├── QUESTION_2 Start a new process or continue with an existing one?:
            ├── OPTIONS_2 Start Over
                ├── QUESTION_3 Choose the language of the book:
                    ├── OPTIONS_3 English
                    ├── OPTIONS_3 Turkish
            ├── OPTIONS_2 Continue
                ├── QUESTION_4 Select the book:
                    
    ├── OPTIONS_1 Listen to an audio book

"""

QUESTION_1 = "Choose an option:"
OPTIONS_1 = ["Voice a book", "Listen to an audio book", "Exit"]

QUESTION_2 = "Start a new process or continue with an existing one:"
OPTIONS_2 = ["Start Over", "Continue"]

QUESTION_3 = "Choose the language of the book:"
OPTIONS_3 = ["English", "Turkish"]

QUESTION_4 = "Select the book:"
