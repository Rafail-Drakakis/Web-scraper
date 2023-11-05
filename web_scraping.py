import sys
import os
import re
import urllib
import urllib3
import shutil 
import requests
import bs4 
import docx 
import zipfile 
import tarfile 
import gzip
import tkinter as tk
import customtkinter
from tkinter import filedialog
from CTkMessagebox import CTkMessagebox

# Disable InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#site_downloader.py
def fetch_and_store_files(url, folder_name):
    """
    The function `fetch_and_store_files` fetches files from a given URL and stores them in a specified
    folder.
    
    :param url: The `url` parameter is the URL of the webpage from which you want to fetch and store
    files. It can be a webpage URL or a file URL
    :param folder_name: The `folder_name` parameter is the name of the folder where the fetched files
    will be stored
    """
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url

    response = requests.get(url, verify=False)
    soup = bs4.BeautifulSoup(response.content, 'html.parser')
    a_tags = soup.find_all('a')
    save_dir = os.path.join(os.getcwd(), folder_name)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    for tag in a_tags:
        if 'href' in tag.attrs:
            file_url = urllib.parse.urljoin(url, tag['href'])
            file_name = os.path.join(save_dir, file_url.split('/')[-1])
            if '.' in file_name and file_url != url and file_url.startswith(("http://", "https://")):
                file_response = requests.get(file_url, allow_redirects=True, verify=False)
                successful_response = 200
                if file_response.status_code == successful_response:
                    with open(file_name, 'wb') as file:
                        file.write(file_response.content)

#clean_folder.py
def clean_up_folder(folder_path):
    """
    The `clean_up_folder` function deletes files with .html and .php extensions and unzips files with
    supported extensions (.zip, .tgz, .gz) in a given folder path.
    
    :param folder_path: The `folder_path` parameter is a string that represents the path to the folder
    that needs to be cleaned up
    """
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)

            # Delete files with .html and .php extensions
            if file.endswith((".html", ".php")):
                os.remove(file_path)

            # Unzip files with supported extensions
            elif file.endswith((".zip", ".tgz", ".gz")):
                if file.endswith(".zip"):
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(root)
                elif file.endswith((".tgz", ".tar.gz")):
                    try:
                        with tarfile.open(file_path, 'r:gz') as tar_ref:
                            tar_ref.extractall(root)
                    except tarfile.ReadError:
                        print(f"Skipping file: {file_path} (Not a valid tar file)")
                        continue
                elif file.endswith(".gz"):
                    new_file_path = file_path[:-3]  # Remove .gz extension
                    try:
                        with gzip.open(file_path, 'rb') as gzip_ref:
                            with open(new_file_path, 'wb') as output_file:
                                output_file.write(gzip_ref.read())
                    except (gzip.BadGzipFile, OSError):
                        print(f"Skipping file: {file_path} (Not a valid gzip file)")
                        continue

                os.remove(file_path)

def organize_files(directory):
    """
    The `organize_files` function organizes files in a given directory by moving them into folders based
    on their file extensions.
    
    :param directory: The `directory` parameter is the path to the directory where the files are located
    """
    # Get all files in the directory
    files = os.listdir(directory)

    # Create a dictionary to hold the file extensions and their corresponding folders
    file_types = {}

    # Loop through each file and organize them by extension
    for file in files:
        # Exclude the target file from being moved
        if file == "merged.pdf":
            continue
        
        # Get the file extension
        file_extension = os.path.splitext(file)[1]

        # If the file extension doesn't exist in the dictionary, create a new folder for it
        if file_extension not in file_types:
            folder_name = file_extension.replace(".", "")
            folder_path = os.path.join(directory, folder_name)
            
            # Check if the folder already exists
            if not os.path.exists(folder_path):
                os.mkdir(folder_path)
            
            file_types[file_extension] = folder_name

        # Move the file to the corresponding folder
        src_path = os.path.join(directory, file)
        dst_path = os.path.join(directory, file_types[file_extension], file)
        shutil.move(src_path, dst_path)
    
#scrape_data.py  
def scrape_text(url, folder_name, folder_path):
    """
    The function `scrape_text` takes a URL and a folder name as input, scrapes the main text from the
    webpage at the given URL, and saves the cleaned text in a text file within the specified folder.

    :param url: The `url` parameter is the URL of the webpage you want to scrape the text from
    :param folder_name: The `folder_name` parameter is the name of the folder where you want to save the
    extracted text file
    """
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.content, 'html.parser')
    main_text = soup.get_text(separator='\n')
    if not main_text:
        print('Error: Failed to extract the main text')
        sys.exit(1)
    main_text = replace_chars(main_text)
    os.makedirs(folder_name, exist_ok=True)
    txt_filename = f"{folder_name}/{folder_path}.txt"
    with open(txt_filename, 'w', encoding='utf-8') as f:
        f.write(main_text)
    clean_text_file(txt_filename)

def scrape_images(url, folder_name):
    """
    The function `scrape_images` takes a URL and a folder name as input, scrapes all the images from the
    webpage at the given URL, and saves them in the specified folder.
    
    :param url: The `url` parameter is the URL of the webpage from which you want to scrape images. It
    should be a string
    :param folder_name: The `folder_name` parameter is the name of the folder where the scraped images
    will be saved
    """
    soup = get_page(url)
    os.makedirs(folder_name, exist_ok=True)
    for img in soup.find_all('img'):
        img_url = img.get('src')
        if not img_url:
            continue
        try:
            img_name = img_url.split('/')[-1]
            img_name = img_name.split('.')[0] + '.jpg'
            img_path = os.path.join(folder_name, img_name)
            urllib.request.urlretrieve(img_url, img_path)
        except Exception as e:
            print(f'Error downloading {img_url}: {str(e)}')

#clean_text.py
def replace_chars(text):
    """
    The function `replace_chars` takes a text as input and replaces all characters from 1 to 99 with a
    space, and replaces tabs with three spaces.

    :param text: The `text` parameter is a string that represents the text you want to modify
    :return: the modified text after replacing certain characters.
    """
    chars_to_replace = [f"[{i}]" for i in range(1, 100)]
    for char in chars_to_replace:
        text = text.replace(char, ' ')
    text = text.replace('\t', '   ')  # Replace tab with three spaces
    return text

def clean_text_file(filename):
    """
    The function `clean_text_file` reads a text file, replaces multiple consecutive new lines with a
    single new line and adds three spaces instead of a new line, replaces three or more spaces with two
    spaces, saves the modified text as a DOCX file, and finally deletes the original text file.

    :param filename: The `filename` parameter is the name of the text file that you want to clean
    """
    if not os.path.isfile(filename):
        print(f'Error: {filename} does not exist')
        sys.exit(1)
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()
    # Replace multiple consecutive new lines with a single new line and add three spaces instead of new line
    text = re.sub(r'\n+', '   ', text.strip())
    # Replace 3 or more spaces with 2 spaces
    text = re.sub(r' {3,}', '  ', text)
    save_text_as_docx(text, filename)
    os.remove(filename)

def save_text_as_docx(text, filename):
    """
    The function `save_text_as_docx` takes in a string of text and a filename, and saves the text as a
    .docx file with the specified filename.

    :param text: The `text` parameter is the content that you want to save as a .docx file. It can be a
    string containing any text you want to include in the document
    :param filename: The `filename` parameter is the name of the file you want to save the text as. It
    should include the file extension, such as ".txt" or ".docx"
    """
    doc = docx.Document()
    doc.add_paragraph(text, style='Normal')
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = docx.shared.Pt(12)
    doc_file_name = os.path.splitext(filename)[0] + '.docx'
    doc.save(doc_file_name)

def get_page(url):
    """
    The function `get_page` takes a URL as input, sends a GET request to that URL, and returns the
    parsed HTML content of the web page.
    
    :param url: The `url` parameter is the URL of the web page that you want to retrieve
    :return: a BeautifulSoup object, which is created from the content of the web page obtained from the
    given URL.
    """
    response = requests.get(url)
    successful_response = 200
    if response.status_code != successful_response:
        print('Error: Failed to get the web page')
        sys.exit(1)
    soup = bs4.BeautifulSoup(response.content, 'html.parser')
    return soup

def show_message(output, sucess):
    if sucess:
        CTkMessagebox(title="Success", message=output, icon="check", option_1="Thanks")
    else:
        CTkMessagebox(title="Error", message=output, icon="cancel")

def create_directory(url_entry, folder_name_entry):
    download_path = filedialog.askdirectory()
    folder_name = os.path.splitext(os.path.basename(download_path))[0]
    url = url_entry.get()
    folder_name = folder_name_entry.get()
    directory = os.path.join(download_path, folder_name)
    output = f'The {folder_name} folder has been successfully created.'
    return directory, output, url, folder_name

def scrape_text_and_images(url_entry, folder_name_entry):
    try:
        directory, output, url, folder_name = create_directory(url_entry, folder_name_entry)
        scrape_text(url, directory, folder_name) 
        scrape_images(url, directory)
        show_message(output, 1)
    except Exception as e:
        show_message(str(e), 0)

def download_files_from_website(url_entry, folder_name_entry):
    try: 
        directory, output, url, _ = create_directory(url_entry, folder_name_entry)  
        fetch_and_store_files(url, directory)
        clean_up_folder(directory)
        organize_files(directory)
        show_message(output, 1)
    except Exception as e:
        show_message(str(e), 0)

def main():
    app = customtkinter.CTk()
    app.title("Media downloader")

    # Set the window size
    window_width = 700
    window_height = 620

    # Get the screen width and height
    screen_width = app.winfo_screenwidth()
    screen_height = app.winfo_screenheight()

    # Calculate the x and y coordinates for the window to be centered
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2

    # Set the geometry of the window to center it on the screen
    app.geometry(f"{window_width}x{window_height}+{x}+{y}")

    get_text_title = customtkinter.CTkLabel(app, text="Enter the URL of the web page you want to scrape text and images from")
    get_text_title.pack()
    
    # Create Entry widgets to get URL and folder name
    url_entry = tk.Entry(app, width=50)
    url_entry.pack(pady=10, padx=10)

    scrape_text_and_images_button = customtkinter.CTkButton(app, text="Scrape Text and Images", command=lambda: scrape_text_and_images(url_entry, folder_name_entry))
    scrape_text_and_images_button.pack(pady=10, padx=10)

    get_files_title = customtkinter.CTkLabel(app, text="Enter the name of the folder where you want to store the files")
    get_files_title.pack()
    
    folder_name_entry = tk.Entry(app, width=50)
    folder_name_entry.pack(pady=10, padx=10)
    
    download_files_button = customtkinter.CTkButton(app, text="Download Files from Website", command=lambda: download_files_from_website(url_entry, folder_name_entry))
    download_files_button.pack(pady=10, padx=10)
    # Start the GUI main loop
    app.mainloop()

main()