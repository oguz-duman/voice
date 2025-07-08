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
from InquirerPy import inquirer
from rich.progress import Progress

from src.constants import QUESTION_2, OPTIONS_2, QUESTION_3, OPTIONS_3, QUESTION_4


paragraphs_per_page = []        # To store the number of paragraphs in each page
paragraph_coordinates = []      # To store the coordinates of the paragraphs
interrupt_process = False       # To stop the voice synthesis process
last_flag = 0                   # To store the position of last stopped process
lan = ""                        # To store the book language   
model = ""                      # To store the modal path
book_dir = ""                   # To store active book directory


def start_voicing():
    """ Starts the voicing process by making the necessary preparations. """
    global model, lan
    
    # Ask the user if they want to continue or start a new process
    process_type = inquirer.select(
        message = QUESTION_2,
        choices = OPTIONS_2
    ).execute()
    clear_console()

    if process_type == OPTIONS_2[0]:
        # Ask the user to choose the language of the book
        lan = inquirer.select(
            message = QUESTION_3,
            choices = OPTIONS_3
        ).execute()
        clear_console()
        new_voicing()                   

    elif process_type == OPTIONS_2[1]:
        continue_voicing()


def choose_language_model(lan):
    """ Chooses the appropriate language model based on the provided language. """
    global model

    if lan == OPTIONS_3[0]:
        model = ".\\src\\piper\\en_US-hfc_female-medium.onnx" 
    elif lan == OPTIONS_3[1]:
        model = ".\\src\\piper\\tr_TR-dfki-medium.onnx"
        command = f'cmd /c chcp 65001'          # console encoding for Turkish
        subprocess.call(command, shell=True)


def new_voicing():
    """ Starts a fresh voicing process. """
    global book_dir, lan
    choose_language_model(lan)      # choose the appropriate language model based on the selected language  

    # open the pdf file and extract the text and images
    pdf_file, book_dir = open_file()
    if not pdf_file:
        return
    extract_data(pdf_file)

    # start the text to speech process
    text_to_speech()


def continue_voicing():
    """
    Continues the voicing process from where it was left off.
    It loads the necessary data from the previous process and starts the text to speech process with the loaded data.
    """
    global book_dir, paragraphs_per_page, paragraph_coordinates, last_flag, lan    

    # get the list of books in the data directory
    books = [d for d in os.listdir("src/data") if os.path.isdir(os.path.join("src/data", d))]
    if not books:
        print("No books found in the data directory. Please start a new voicing process.")
        return
    # Ask the user to select a book to continue voicing
    book_name = inquirer.select(
        message = QUESTION_4,
        choices = books
    ).execute()   
    clear_console()
    book_dir = f"src/data/{book_name}"  # set the book directory      

    # Load the paragraphs_per_page, paragraph_coordinates, last_flag and language data
    with open(f'{book_dir}/paragraphs_per_page.pickle', 'rb') as f:
        paragraphs_per_page = pickle.load(f)

    with open(f'{book_dir}/paragraph_coordinates.pickle', 'rb') as f:
        paragraph_coordinates = pickle.load(f)

    with open(f'{book_dir}/last_flag.pickle', 'rb') as f:
        last_flag = pickle.load(f)
    
    with open(f'{book_dir}/language.pickle', 'rb') as f:
        lan = pickle.load(f)

    # start the text to speech process
    text_to_speech()


def open_file():
    """
    Opens a PDF file using a file dialog and prepares the data directory for the new book.
    The directory structure is created with subdirectories for images, texts, and audios.
    The name of the data directory is derived from the PDF file name.
    Uses the PyMuPDF library to handle PDF files and the tkinter library for the file dialog.
    Returns:
        pdf_file (fitz.Document): The opened PDF file.
        dir_path (str): The path to the data directory for the new book.
    """
    Tk().withdraw()
    file_path = askopenfilename(
        title="Select a PDF file",
        filetypes=[("PDF files", "*.pdf")]
    )
    if not file_path:
        print("No PDF file selected. Exiting the voicing process.")
        return None, None
    pdf_file = fitz.open(file_path)

    # Prepare the data directory for the new book
    file_name = file_path.split("/")[-1].strip(".pdf").replace(" ", "_").lower()
    dir_path = f"src/data/{file_name}"

    # If the directory already exists, delete it for a fresh start
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        shutil.rmtree(dir_path)

    # Create the directory structure for the new book
    os.makedirs(f"{dir_path}/images")
    os.makedirs(f"{dir_path}/texts")
    os.makedirs(f"{dir_path}/audios")

    return pdf_file, dir_path


def extract_data(pdf_file):
    """
    Extracts text and images from the PDF file and saves them in the appropriate directories.
    The text is saved as paragraph blocks in separate txt files, and the images are saved as PNG files.
    The number of pages and paragraphs per page are also stored in .pickle files for later use.
    """
    global book_dir, lan, paragraphs_per_page, paragraph_coordinates

    with Progress(transient=True) as progress:
        task = progress.add_task("[green]Extracting text...", total=pdf_file.page_count)
        
        for page_num in range(pdf_file.page_count):
            
            page = pdf_file.load_page(page_num)            # Get the page
            paragraphs = page.get_text("blocks")           # Get the page text as paragraph blocks
            
            # Save each paragraph to a txt file
            par_count = 0
            par_coords = []
            for para_num, par in enumerate(paragraphs):
                if par == "":  # skip empty paragraphs
                    continue
                par_count += 1
                par_coords.append(par[0:4])
                with open(f"{book_dir}/texts/page_{page_num + 1}_para_{para_num + 1}.txt", "w", encoding="utf-8") as txt_file:
                    text = par[4].replace('\n', ' ')            
                    text = text.replace('- ', '')            
                    text = unicodedata.normalize("NFKC", text) if lan == "en" else text
                    txt_file.write(text) 
            
            # store the number of paragraphs in the page
            if par_count > 0:
                paragraphs_per_page.append(par_count)  
                paragraph_coordinates.append(par_coords)
            else:
                paragraphs_per_page.append(None)
                paragraph_coordinates.append(None)

            # Save the page as an image file
            dpi = 300/72    # 72 DPI is default, adjust for higher quality
            pix = page.get_pixmap(matrix=fitz.Matrix(dpi, dpi))  
            img_filename = f"{book_dir}/images/page_{page_num + 1}.png"
            pix.save(img_filename)
            
            # Update progress
            progress.update(task, advance=1, description=f"[green]Extracting text from page {page_num + 1}/{pdf_file.page_count}...")
        
        # Store the number of paragraphs per page
        with open(f"{book_dir}/paragraphs_per_page.pickle", "wb") as f:
            pickle.dump(paragraphs_per_page, f)

        # Store the paragraph coordinates
        with open(f"{book_dir}/paragraph_coordinates.pickle", "wb") as f:
            pickle.dump(paragraph_coordinates, f)

        # Store the language og the book
        with open(f"{book_dir}/language.pickle", "wb") as f:
            pickle.dump(lan, f)
        

def text_to_speech():
    """
    Converts the extracted text to speech using the Piper TTS model.
    The audio files are saved in the audios directory with the same naming convention as the text files.
    The process can be interrupted by pressing the 'q' key, and the current progress is saved to a pickle file.
    The last processed page number is saved to resume the process later.
    """
    global book_dir, last_flag, interrupt_process, model, paragraphs_per_page


    with Progress(transient=True) as progress:
        threading.Thread(target=interrupt_listenner, args=(progress,), daemon=True).start()           # start the interrupt listener thread to listen for the 'q' key press
        page_count = len(paragraphs_per_page)
        task = progress.add_task("[green]Voicing...", total=page_count)

        for page_num in range(1, page_count+1):
            # check if the process is resuming from a previous interruption and if the page has paragraphs to voice
            if (not last_flag or page_num > last_flag) and paragraphs_per_page[page_num-1]:
                # voice each paragraph in the page
                for para_num in range(1, paragraphs_per_page[page_num-1]+1):
                    book_dir_ = book_dir.replace("/", "\\")     # replace forward slashes with backslashes for Windows compatibility
                    command = f'cmd /c type .\\{book_dir_}\\texts\\page_{page_num}_para_{para_num}.txt | .\\src\\piper\\piper.exe -m {model} -f .\\{book_dir_}\\audios\\page_{page_num}_para_{para_num}.wav'
                    subprocess.call(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Update progress
            progress.update(task, advance=1, description=f'[green]Voicing page {page_num}/{page_count}...')        

            # If the process is interrupted, save the current page number and break the loop
            if interrupt_process:
                clear_console()
                print("Voicing process interrupted. You can continue later from where you left off.")
                input("Press Enter to continue...")
                clear_console()
                break

        # save the current page number
        with open(f"{book_dir}/last_flag.pickle", "wb") as f:
            pickle.dump(page_num+1, f)


def interrupt_listenner(progress):
    """ Listens for the 'q' key press to interrupt the voicing process. """
    global interrupt_process
    print("Press 'q' to stop the voicing process and continue later from where you left off.")
    keyboard.wait('q')
    progress.stop()
    clear_console()
    print("Interrupting the voicing process. Please wait...")
    interrupt_process = True


def clear_console():
    os.system("cls" if os.name == "nt" else "clear")

