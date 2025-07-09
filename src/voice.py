import os
import subprocess
import pickle
import unicodedata
import threading
import shutil
from tkinter import Tk
from tkinter.filedialog import askopenfilename

import fitz # PyMuPDF  
import keyboard
from rich.progress import Progress


class VoicingApp():
    """
    """
    def __init__(self):
        self.paragraphs_per_page = []           # To store the page count and number of paragraphs in each page
        self.paragraph_coordinates = []         # To store the coordinates of the paragraphs
        self.interrupt_process = False          # To stop the voice synthesis process
        self.last_position = 0                  # To store the position of last stopped process
        self.language = None                    # To store the book language
        self.model = None                       # To store the modal path
        self.pdf_file = None                    # To store the PDF file
        self.data_dir = None                    # To store the active active book data directory

    def choose_language_model(self):
        """ Chooses the appropriate language model based on the provided language. """
        if self.language == "English":
            self.model = ".\\src\\piper\\en_US-hfc_female-medium.onnx" 
        elif self.language == "Turkish":
            self.model = ".\\src\\piper\\tr_TR-dfki-medium.onnx"
            command = f'cmd /c chcp 65001'          # console encoding for Turkish
            subprocess.call(command, shell=True)


    def open_file(self):
        Tk().withdraw()
        file_path = askopenfilename(
            title="Select a PDF file",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not file_path:
            return False
        
        # read the pdf
        self.pdf_file = fitz.open(file_path)

        # set the book data directory
        file_name = file_path.split("/")[-1].strip(".pdf").replace(" ", "_").lower()
        self.data_dir = f"src/data/{file_name}"

        return True


    def create_data_directories(self):
        # If the directory already exists, delete its content for a fresh start
        if os.path.exists(self.data_dir) and os.path.isdir(self.data_dir):
            shutil.rmtree(self.data_dir)

        # Create the directory structure for the new book
        os.makedirs(f"{self.data_dir}/images")
        os.makedirs(f"{self.data_dir}/texts")
        os.makedirs(f"{self.data_dir}/audios")


    def extract_book_data(self):
        """
        """
        with Progress(transient=True) as progress:
            task = progress.add_task("[green]Extracting text...", total=self.pdf_file.page_count)
            
            for page_num in range(self.pdf_file.page_count):
                
                page = self.pdf_file.load_page(page_num)       # Get the page
                paragraphs = page.get_text("blocks")           # Get the page text as paragraph blocks
                
                # Save each paragraph to a txt file
                par_count = 0
                par_coords = []
                for para_num, par in enumerate(paragraphs):
                    if par == "":  # skip empty paragraphs
                        continue
                    par_count += 1
                    par_coords.append(par[0:4])
                    with open(f"{self.data_dir}/texts/page_{page_num + 1}_para_{para_num + 1}.txt", "w", encoding="utf-8") as txt_file:
                        text = par[4].replace('\n', ' ')            
                        text = text.replace('- ', '')            
                        text = unicodedata.normalize("NFKC", text) if self.language == "en" else text
                        txt_file.write(text) 
                
                # store the number of paragraphs in the page
                if par_count > 0:
                    self.paragraphs_per_page.append(par_count)  
                    self.paragraph_coordinates.append(par_coords)
                else:
                    self.paragraphs_per_page.append(None)
                    self.paragraph_coordinates.append(None)

                # Save the page as an image file
                dpi = 300/72    # 72 DPI is default, adjust for higher quality
                pix = page.get_pixmap(matrix=fitz.Matrix(dpi, dpi))  
                img_filename = f"{self.data_dir}/images/page_{page_num + 1}.png"
                pix.save(img_filename)
                
                # Update progress
                progress.update(task, advance=1, description=f"[green]Extracting text from page {page_num + 1}/{self.pdf_file.page_count}...")
            
            # Store the number of paragraphs per page
            with open(f"{self.data_dir}/paragraphs_per_page.pickle", "wb") as f:
                pickle.dump(self.paragraphs_per_page, f)

            # Store the paragraph coordinates
            with open(f"{self.data_dir}/paragraph_coordinates.pickle", "wb") as f:
                pickle.dump(self.paragraph_coordinates, f)

            # Store the language og the book
            with open(f"{self.data_dir}/language.pickle", "wb") as f:
                pickle.dump(self.language, f)
         

    def text_to_speech(self):
        """
        """
        interrupted = False     # to check if the process is completed or interrupted

        with Progress(transient=True) as progress:
            threading.Thread(target=self.interrupt_listenner, args=(progress,), daemon=True).start()           # start the interrupt listener thread to listen for the 'q' key press
            page_count = len(self.paragraphs_per_page)
            task = progress.add_task("[green]Voicing page 1...", total=page_count)

            for page_num in range(1, page_count+1):
                # check if the process is resuming from a previous interruption and if the page has paragraphs to voice
                if (self.last_position == 0 or page_num > self.last_position) and self.paragraphs_per_page[page_num-1]:
                    # voice each paragraph in the page
                    for par_num in range(1, self.paragraphs_per_page[page_num-1]+1):
                        data_dir = self.data_dir.replace("/", "\\")     # replace forward slashes with backslashes for Windows compatibility
                        command = f'cmd /c type .\\{data_dir}\\texts\\page_{page_num}_para_{par_num}.txt | .\\src\\piper\\piper.exe -m {self.model} -f .\\{data_dir}\\audios\\page_{page_num}_para_{par_num}.wav'
                        subprocess.call(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                # Update progress
                progress.update(task, advance=1, description=f'[green]Voicing page {page_num+1}/{page_count}...')        

                # If the process is interrupted, save the current page number and break the loop
                if self.interrupt_process:
                    self.warning_message("Voicing process interrupted. You can continue later from where you left off.")
                    interrupted = True
                    self.interrupt_process = False
                    subprocess.call("taskkill /IM piper.exe /F", shell=True)
                    break
            
            # save the current page number
            with open(f"{self.data_dir}/self.last_position.pickle", "wb") as f:
                pickle.dump(page_num, f)
            self.last_position = page_num
            progress.stop()
            self.clear_console()
            if not interrupted:
                self.warning_message("Voicing process is completed.") 
   

    def interrupt_listenner(self, progress):
        """ Listens for the 'q' key press to interrupt the voicing process. """
        print("Press 'q' to stop the voicing process and start listening. You can continue voicing later where you left off.")
        keyboard.wait('q')
        progress.stop()
        self.clear_console()
        print("Interrupting the voicing process. Please wait...")
        self.interrupt_process = True


    def get_book_list(self):
        # get the list of books in the src/data directory
        books = [d for d in os.listdir("src/data") if os.path.isdir(os.path.join("src/data", d))]
        if not books:
            print("No books found in the data directory. Please start a new voicing process.")
            return None
        return books


    def get_stored_progress(self, book_name):
        """
        """
        self.data_dir = f"src/data/{book_name}"     

        with open(f'{self.data_dir}/paragraphs_per_page.pickle', 'rb') as f:
            self.paragraphs_per_page = pickle.load(f)

        with open(f'{self.data_dir}/paragraph_coordinates.pickle', 'rb') as f:
            self.paragraph_coordinates = pickle.load(f)

        with open(f'{self.data_dir}/self.last_position.pickle', 'rb') as f:
            self.last_position = pickle.load(f)
        
        with open(f'{self.data_dir}/language.pickle', 'rb') as f:
            self.language = pickle.load(f)
            
        self.choose_language_model()


    def clear_console(self):    
        os.system("cls" if os.name == "nt" else "clear")


    def warning_message(self, message):
        self.clear_console()
        print(message, "\n")
        input("Press Enter to continue...")
        self.clear_console()


