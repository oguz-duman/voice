import os
import fitz  
import subprocess
import pickle
import unicodedata
from InquirerPy import inquirer
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from rich.progress import Progress
import threading
import keyboard
import time
import shutil

paragraphs_per_page = [None]    # To store the number of paragraphs in each page
paragraph_coordinates = [None]  # To store the coordinates of the paragraphs
interrupt_process = False       # To stop the voice synthesis process
last_flag = False               # To store the position of last stopped process
lan = ""                        # To store the book language   
model = ""                      # To store the modal path
book_dir = ""                   # To store active book directory

def start_voice():
    global model

    language_options = ["English", "Turkish"]
    # Ask the user to choose the language of the book
    lan = inquirer.select(
        message="Choose the language of the book:",
        choices=language_options
    ).execute()

    # choose the appropriate language model
    if lan == language_options[0]:
        model = ".\\src\\piper\\en_US-hfc_female-medium.onnx" 
    elif lan == language_options[1]:
        model = ".\\src\\piper\\tr_TR-dfki-medium.onnx"

    # Set the console encoding to UTF-8 if the language is Turkish
    if lan == "tr":
        command = f'cmd /c chcp 65001'
        subprocess.call(command, shell=True)

    # Ask the user if they want to continue or start a new process
    process_type = inquirer.select(
        message="Do you want to start a new process or continue with an existing one?:",
        choices=["Start Over", "Continue"]
    ).execute()

    if process_type == "Continue":
        continue_voicing()
    elif process_type == "Start Over":
        new_voicing()


def new_voicing():
    """
    
    """
    global book_dir
    # open the pdf file and extract the text and images
    pdf_file, book_dir = open_file()
    extract_text_and_imgs(pdf_file)
    voice()


def voice():
    """

    """
    global book_dir, model
    tot = len(paragraphs_per_page)
    
    threading.Thread(target=interrupt_listenner, daemon=True).start()

    with Progress() as progress:
        task = progress.add_task("[green]Voicing...", total=tot)

        for page_num in range(1, tot):

            if last_flag and page_num < last_flag:
                continue

            if not paragraphs_per_page[page_num]:
                continue
            
            for para_num in range(1, paragraphs_per_page[page_num]+1):
                book_dir_ = book_dir.replace("/", "\\")
                
                command = f'cmd /c type .\\{book_dir_}\\texts\\page_{page_num}_para_{para_num}.txt | .\\src\\piper\\piper.exe -m {model} -f .\\{book_dir_}\\audios\\page_{page_num}_para_{para_num}.wav'
                subprocess.call(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            if interrupt_process:
                # save the current page number
                with open(f"{book_dir}/last_flag.pickle", "wb") as f:
                    pickle.dump(page_num+1, f)
                is_ended = True
                break

            # Update progress
            progress.update(task, advance=1)

        # save the current page number
        dir = "src/data/" + book_dir
        with open(f"{book_dir}/last_flag.pickle", "wb") as f:
            pickle.dump(len(paragraphs_per_page), f)


def continue_voicing():
    return
    # Load the number of paragraphs per page from the pickle file
    with open("data/paragraphs_per_page.pickle", "rb") as f:
        paragraphs_per_page = pickle.load(f)
    
    # Load the paragraph coordinates from the pickle file
    with open("data/paragraph_coordinates.pickle", "rb") as f:
        paragraph_coordinates = pickle.load(f)
    
    # Load the last page number from the pickle file
    with open("data/stop_page.pickle", "rb") as f:
        stop_page = pickle.load(f)
    
    # Run the voice synthesis in a new thread with the last page number passed
    synthesis_thread = threading.Thread(target=voice_senthesis, args=(stop_page,))
    synthesis_thread.start()
    
    # Listen to the user's commands to end the process when needed
    while synthesis_thread.is_alive():
        # to reduce the CPU usage
        time.sleep(0.05)   

        # listen to the user's commands
        command = input("")
        if command.lower() == "end":
            print("Ending the process. Please wait!")
            stop_thread = True
            while not is_ended:
                pass
            break

    print("Program has been ended.")


def extract_text_and_imgs(pdf_file):
    global book_dir

    tot_pages = pdf_file.page_count

    with Progress() as progress:
        task = progress.add_task("[green]Extracting text...", total=tot_pages)
        
        for page_num in range(tot_pages):
            # Get the page
            page = pdf_file.load_page(page_num)
            
            # Get the page text as paragraph blocks
            paragraphs = page.get_text("blocks")
            
            # Save each paragraph to a txt file
            para_count = 0
            par_coords = []
            for para_num, para in enumerate(paragraphs):
                if para == "":  # skip empty paragraphs
                    continue
                para_count += 1
                par_coords.append(para[0:4])
                with open(f"{book_dir}/texts/page_{page_num + 1}_para_{para_num + 1}.txt", "w", encoding="utf-8") as txt_file:
                    text = para[4].replace('\n', ' ')            
                    text = text.replace('- ', '')            
                    text = unicodedata.normalize("NFKC", text) if lan == "en" else text
                    txt_file.write(text) 
            
            # store the number of paragraphs in the page
            if para_count > 0:
                paragraphs_per_page.append(para_count)  
                paragraph_coordinates.append(par_coords)
            else:
                paragraphs_per_page.append(None)
                paragraph_coordinates.append(None)

            # Save the page to an image file
            dpi = 300       # Adjust DPI for higher quality
            pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72))  # 72 DPI is default, adjust for higher quality
            img_filename = f"{book_dir}/images/page_{page_num + 1}.png"
            pix.save(img_filename)
            
            # Update progress
            progress.update(task, advance=1)

        print("All pages have been converted.")


def interrupt_listenner():
    global interrupt_process
    keyboard.wait('q')
    interrupt_process = True


def open_file():
    """

    """
    Tk().withdraw()
    file_path = askopenfilename(
        title="Select a PDF file",
        filetypes=[("PDF files", "*.pdf")]
    )
    pdf_file = fitz.open(file_path)

    # name of the data directory will be reserved for the new book
    file_name = file_path.split("/")[-1].strip(".pdf").replace(" ", "_").lower()
    dir_path = f"src/data/{file_name}"

    # Remove the directory if it already exists
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        shutil.rmtree(dir_path)

    # Create the new data directory
    os.makedirs(f"{dir_path}/images")
    os.makedirs(f"{dir_path}/texts")
    os.makedirs(f"{dir_path}/audios")

    return pdf_file, dir_path


def clean_console():
    os.system("cls" if os.name == "nt" else "clear")


def clean_dir(folder_path):
    """ Deletes all files in the given folder. Except .gitkeep """
    for filename in os.listdir(folder_path):
        if filename[0] == ".":
            continue
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

