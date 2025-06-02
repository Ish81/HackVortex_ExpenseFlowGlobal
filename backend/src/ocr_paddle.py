
import os
import re
from PIL import Image
import pytesseract
from datetime import datetime
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- Global Font Registration for PDF (moved here from all-in-one) ---
custom_font_name = 'NotoSans'
custom_font_path = 'NotoSans-Regular.ttf' # Assuming this file is in the project root

active_font_for_pdf = 'Helvetica' # Default fallback

def setup_tesseract_and_font():
    """
    Sets up Tesseract OCR and registers a custom font for ReportLab PDFs.
    This function should be called once at the start of the application.
    """
    global active_font_for_pdf

    # Check for Tesseract executable
    # On Windows, you might need to set the tesseract_cmd path:
    # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    # For Colab/Linux, sudo apt-get install tesseract-ocr usually makes it available.
    try:
        pytesseract.get_tesseract_version()
        print("Tesseract OCR engine is found.")
    except pytesseract.TesseractNotFoundError:
        print("Error: Tesseract OCR engine not found.")
        print("Please ensure it's installed (e.g., 'sudo apt-get install tesseract-ocr' on Linux, or via installer on Windows) and its path is set if needed.")
        print("OCR functionality will be limited or unavailable.")

    # Try to register a custom font for better Unicode support (like Rupee symbol)
    try:
        if os.path.exists(custom_font_path):
            pdfmetrics.registerFont(TTFont(custom_font_name, custom_font_path))
            print(f"Custom font '{custom_font_name}' registered for PDF: {custom_font_path}")
            active_font_for_pdf = custom_font_name
        else:
            print(f"Warning: Custom font file '{custom_font_path}' not found.")
            print("Upload it to your project root (e.g., ExpenseReconciliation/) for full Rupee symbol support in PDFs.")
            print("Using ReportLab's built-in 'Helvetica' font as fallback. Rupee symbol might not display.")
            active_font_for_pdf = 'Helvetica' # Fallback to standard built-in font
    except Exception as e:
        print(f"Error registering custom font: {e}")
        print("Using ReportLab's built-in 'Helvetica' font as fallback. Rupee symbol might not display.")
        active_font_for_pdf = 'Helvetica' # Fallback if any error occurs

# --- Parsing Logic (from your all-in-one app) ---

def parse_ocr_text_to_bill(ocr_text, bill_idx):
    """
    Parses raw OCR text to extract structured bill details.
    This function makes strong assumptions about the bill's format and keywords.
    It's the most fragile part and may need tuning for your specific bill layouts.
    Now includes a fallback for direct total extraction if items are not found.
    """
    bill_data = {
        "bill_id": f"OCR_BILL_{bill_idx:03d}", # Default ID
        "customer_name": "Unknown Customer",
        "bill_date": datetime.now().strftime("%Y-%m-%d"), # Default date
        "items": [],
        "parsed_successfully": False # Flag to indicate if parsing was somewhat successful
    }

    lines = ocr_text.split('\n')

    # 1. Extract Bill ID, Customer Name, Date (using regex and keywords)
    for line in lines:
        line = line.strip()
        if not line: # Skip empty lines
            continue

        # Bill ID - more flexible regex for Invoice No, Invoice #, Ref No, etc.
        id_match = re.search(r'(?:Bill ID|Invoice #|Invoice No|Ref No|Order ID|Inv No)[:\s]*([A-Za-z0-9\-\_]+)', line, re.IGNORECASE)
        if id_match and bill_data["bill_id"].startswith("OCR_BILL_"): # Only update if default or not found yet
            bill_data["bill_id"] = id_match.group(1).strip()
            bill_data["parsed_successfully"] = True

        # Customer Name - improved to handle "Bill To" or "Customer"
        cust_match = re.search(r'(?:Customer|Client|Name|Bill To)[:\s]*(.+)', line, re.IGNORECASE)
        if cust_match and bill_data["customer_name"] == "Unknown Customer":
            customer_name_raw = cust_match.group(1).strip()
            # Clean up potential trailing dates or other info
            customer_name_clean = re.sub(r'\b(?:Date|Inv|Invoice|No|ID|Ref)\b.*', '', customer_name_raw, flags=re.IGNORECASE).strip()
            if customer_name_clean: # Ensure it's not empty after cleaning
                bill_data["customer_name"] = customer_name_clean
                bill_data["parsed_successfully"] = True

        # Bill Date (look for common date formats) - improved to handle "Date 2" or similar noise
        date_match = re.search(r'(?:Date|Bill Date)[:\s]*(\d{1,4}[-/]\d{1,2}[-/]\d{1,4})', line, re.IGNORECASE)
        if date_match and bill_data["bill_date"] == datetime.now().strftime("%Y-%m-%d"):
            bill_data["bill_date"] = date_match.group(1).strip()
            bill_data["parsed_successfully"] = True

    # 2. Extract Items
    item_section_potential = False
    for i, line in enumerate(lines):
        line = line.strip()
        if not line: continue

        if re.search(r'(?:Description|Desc)\s+(?:Qty|Quantity)\s+(?:Price|Amount|Rate|Total)', line, re.IGNORECASE) or \
           re.search(r'^-+\s*(?:Description|Desc)\s.*?-+$', line, re.IGNORECASE):
            item_section_potential = True
            continue

        if item_section_potential and not re.search(r'(Total|Subtotal|Tax|VAT|Discount|GST|Exclude GST)', line, re.IGNORECASE):
            item_match = re.search(r'(.+?)\s+(\d+)\s+(\d+\.?\d*)\s*([A-Za-z]{3}|\$|€|₹)?', line)

            if item_match:
                description = item_match.group(1).strip()
                try:
                    quantity = int(item_match.group(2))
                    unit_price = float(item_match.group(3))
                    currency = item_match.group(4) if item_match.group(4) else "INR"

                    description = re.sub(r'\d+\.?\d*|\$|€|₹|USD|EUR|GBP|JPY|INR|AED', '', description, flags=re.IGNORECASE).strip()

                    if description and quantity > 0 and unit_price >= 0:
                        bill_data["items"].append({
                            "description": description,
                            "quantity": quantity,
                            "unit_price_orig": unit_price,
                            "currency": currency.upper()
                        })
                        bill_data["parsed_successfully"] = True
                except ValueError:
                    pass

    # --- New Logic: Fallback for extracting a 'Grand Total' from OCR text ---
    ocr_extracted_final_total = 0.0
    ocr_extracted_final_currency = "INR"

    for line in lines:
        line = line.strip()
        total_match = re.search(r'(?:total|grand total|net amount|amount due|inclusive gst|exclude gst|tal|grandtal)[:\s]([\d.,]+)\s([A-Za-z]{3}|\$|€|₹)?', line, re.IGNORECASE)

        if total_match:
            amount_str = total_match.group(1).replace(',', '')
            try:
                current_total_value = float(amount_str)
                current_currency_code = total_match.group(2) if total_match.group(2) else "INR"

                if re.search(r'(inclusive gst|grand total)', line, re.IGNORECASE):
                    ocr_extracted_final_total = current_total_value
                    ocr_extracted_final_currency = current_currency_code.upper()
                    bill_data["parsed_successfully"] = True
                    break
                elif current_total_value > ocr_extracted_final_total:
                    ocr_extracted_final_total = current_total_value
                    ocr_extracted_final_currency = current_currency_code.upper()
                    bill_data["parsed_successfully"] = True

            except ValueError:
                pass

    if not bill_data["items"] and ocr_extracted_final_total > 0:
        print(f"DEBUG: No individual items parsed. Using OCR extracted total: {ocr_extracted_final_total} {ocr_extracted_final_currency} as a fallback.")
        bill_data["items"].append({
            "description": f"Consolidated amount (from OCR total)",
            "quantity": 1,
            "unit_price_orig": ocr_extracted_final_total,
            "currency": ocr_extracted_final_currency
        })
        bill_data["parsed_successfully"] = True
    elif not bill_data["items"]:
        print("DEBUG: No items and no significant total found via OCR for this bill.")

    if not bill_data["items"] and bill_data["parsed_successfully"]:
            print(f"OCR Bill {bill_data['bill_id']} had some info but no valid items could be processed. Consider using direct total if available.")
    elif not bill_data["parsed_successfully"]:
            print(f"OCR Bill {bill_data['bill_id']} was difficult to parse. Data might be incomplete.")

    return bill_data


def perform_ocr(image_path, bill_idx):
    """
    Performs OCR on an image and returns parsed bill details.
    """
    print(f"  Performing OCR on: {image_path}")
    try:
        img = Image.open(image_path)
        img = img.convert("L") # Convert to grayscale for better OCR performance
        ocr_text = pytesseract.image_to_string(img)

        # print("\n--- Raw OCR Text ---")
        # print(ocr_text)
        # print("--------------------")

        bill_details = parse_ocr_text_to_bill(ocr_text, bill_idx)
        return bill_details

    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}. Please check the path.")
        return None
    except pytesseract.TesseractNotFoundError:
        print("Error: Tesseract is not installed or not in your PATH. Please ensure Tesseract is installed.")
        return None
    except Exception as e:
        print(f"An error occurred during OCR or parsing of {image_path}: {e}")
        return None