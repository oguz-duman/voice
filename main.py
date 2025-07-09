import os
from InquirerPy import inquirer
from src.voice import VoicingApp


class MenuNavigator:
    def __init__(self):
        self.state = "main_menu"
        self.running = True

        self.states = {
            "main_menu": self.main_menu,
            "voicing_options": self.voicing_options,
            "choose_language": self.choose_language,
            "choose_book": self.choose_book,
            "exit": self.exit_program
        }


    def run(self):
        while self.running:
            self.clear_console()
            self.states[self.state]()  # Call the method associated with the current state


    def main_menu(self):
        choice = inquirer.select(
            message="Choose an option:",
            choices=["Voice a book", "Listen to an audio book", "--Exit--"]
        ).execute()

        if choice == "Voice a book":
            self.state = "voicing_options"
        elif choice == "Listen to an audio book":
            pass
        else:
            self.state = "exit"


    def voicing_options(self):
        choice = inquirer.select(
            message="Start a new process or continue with an existing one?",
            choices=["Start Over", "Continue", "--Go Back--", "--Exit--"]
        ).execute()

        if choice == "Start Over":
            self.state = "choose_language"
        elif choice == "Continue":
            self.state = "choose_book"
        elif choice == "--Go Back--":
            self.state = "main_menu"
        elif choice == "--Exit--":
            self.state = "exit"


    def choose_language(self):
        choice = inquirer.select(
            message="Choose the language of the book:",
            choices=["English", "Turkish", "--Go Back--", "--Exit--"]
        ).execute()

        if choice == "--Go Back--":
            self.state = "voicing_options"
            return
        elif choice == "--Exit--":
            self.state = "exit"
            return
        
        if voicing_app.open_file():
            print("No PDF file selected. Exiting the voicing process.")
            self.state = "main_menu"
            return

        voicing_app.create_data_directories()
        voicing_app.choose_language_model(choice)
        voicing_app.extract_book_data()
        voicing_app.text_to_speech()    

        self.state = "main_menu"


    def choose_book(self):
        books = voicing_app.get_book_list() 
        books += ["--Go Back--", "--Exit--"]
        choice = inquirer.select(
            message="Select a book:",
            choices=books
        ).execute()

        if choice == "--Go Back--":
            self.state = "voicing_options"
            return
        elif choice == "--Exit--":
            self.state = "exit"
            return

        voicing_app.get_stored_progress(choice)
        voicing_app.text_to_speech()     

        self.state = "main_menu"


    def exit_program(self):
        self.running = False
    

    def clear_console(self):    
        os.system("cls" if os.name == "nt" else "clear")


# create class objects
menu_navigator = MenuNavigator()
voicing_app = VoicingApp()

# run the menu navigator
menu_navigator.run()
