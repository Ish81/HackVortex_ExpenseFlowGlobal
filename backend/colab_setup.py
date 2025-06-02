
# colab_setup.py

import os
import subprocess

def run_command(command):
    try:
        subprocess.run(command, check=True, shell=True, capture_output=True, text=True)
        print(f"Successfully executed: {command}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing '{command}':")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        raise e
    except FileNotFoundError:
        print(f"Command not found: {command.split()[0]}. Make sure it's in your PATH.")
        raise

def setup_colab_environment():
    print("--- Setting up Colab environment ---")

    print("Installing Tesseract OCR engine...")
    run_command("sudo apt-get update -qq")
    run_command("sudo apt-get install tesseract-ocr -qq")

    print("Installing Python libraries: pytesseract, Pillow, reportlab, pandas, numpy...")
    run_command("pip install pytesseract Pillow reportlab pandas numpy -qq")

    # Download NotoSans-Regular.ttf for Rupee symbol support in PDFs
    print("Downloading NotoSans-Regular.ttf for PDF font support...")
    font_url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf"
    font_path = "NotoSans-Regular.ttf"
    if not os.path.exists(font_path):
        try:
            run_command(f"wget -q {font_url} -O {font_path}")
            print(f"Downloaded {font_path}")
        except Exception as e:
            print(f"Could not download NotoSans-Regular.ttf: {e}")
            print("PDFs might not display the Rupee symbol correctly.")
    else:
        print(f"{font_path} already exists.")


    print("Environment setup complete.")

if _name_ == "_main_":
    setup_colab_environment()