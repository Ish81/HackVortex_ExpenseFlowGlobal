
# src/orchestrator.py

import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont # For custom fonts

from src.ocr_paddle import perform_ocr, active_font_for_pdf # Import OCR function and global font
from src.llm_parser import LLMParser
from src.tax_validator import TaxValidator
from src.currency_converter import convert_to_inr
from src.outlier_detector import OutlierDetector


class Orchestrator:
    def _init_(self):
        # Initialize sub-services
        self.llm_parser = LLMParser()
        self.tax_validator = TaxValidator()
        self.outlier_detector = OutlierDetector()
        print("Orchestrator initialized. All services ready.")

    def process_single_receipt(self, file_path, bill_idx):
        """
        Coordinates the processing of a single receipt (image or PDF).
        Returns structured data for the receipt.
        """
        print(f"  Orchestrating processing for: {file_path}")
        file_name = os.path.basename(file_path)
        extracted_data = {
            "file_name": file_name,
            "extracted_company": "N/A",
            "extracted_date": "N/A",
            "original_total": None,
            "original_currency": "N/A",
            "total_inr": None,
            "is_outlier": False,
            "tax_pct_valid": False,
            "vat_reg_valid": False,
            "country_determined": "N/A",
            "pipeline_errors": []
        }

        try:
            # Step 1: OCR
            # Your OCR module now handles both image and PDF (if pdf2image is used internally by pytesseract/PIL,
            # which it is for PDFs by default if installed with Poppler).
            bill_details_from_ocr = perform_ocr(file_path, bill_idx)

            if not bill_details_from_ocr:
                extracted_data["pipeline_errors"].append("OCR or initial parsing failed.")
                return extracted_data

            # Update extracted_data with initial OCR results
            extracted_data["extracted_company"] = bill_details_from_ocr.get("customer_name", "N/A")
            extracted_data["extracted_date"] = bill_details_from_ocr.get("bill_date", "N/A")

            # Calculate totals for the current bill
            sub_total_orig = 0.0
            sub_total_inr = 0.0
            currency_for_original_total = "N/A"
            items_processed = 0

            for item in bill_details_from_ocr.get("items", []):
                # We need to sum up original totals for each item
                item_original_total = item["quantity"] * item["unit_price_orig"]
                sub_total_orig += item_original_total
                currency_for_original_total = item["currency"] # Assuming one currency per bill for simplicity

                # Convert to INR
                inr_value, success = convert_to_inr(item["unit_price_orig"], item["currency"])
                if success:
                    item_total_inr = item["quantity"] * inr_value
                    sub_total_inr += item_total_inr
                    items_processed += 1
                else:
                    extracted_data["pipeline_errors"].append(f"Currency conversion failed for item '{item['description']}' from {item['currency']}")

            # Update extracted_data with calculated totals
            extracted_data["original_total"] = sub_total_orig if items_processed > 0 else None
            extracted_data["original_currency"] = currency_for_original_total if items_processed > 0 else "N/A"
            extracted_data["total_inr"] = sub_total_inr

            # Step 2: LLM Parsing (Mocked for now)
            # You could pass the full OCR text here if you wanted LLM to extract everything
            # llm_results = self.llm_parser.parse_document(ocr_text_from_step1)
            # If LLM significantly improves extraction, update extracted_data here.

            # Step 3: Tax Validation (Mocked for now)
            # Assuming you get estimated tax amount from OCR or LLM
            mock_extracted_tax = extracted_data["total_inr"] * 0.18 if extracted_data["total_inr"] else 0 # Mock 18% tax
            tax_valid = self.tax_validator.validate_tax_percentage(extracted_data["total_inr"], mock_extracted_tax)
            extracted_data["tax_pct_valid"] = tax_valid["tax_pct_valid"]
            if not extracted_data["tax_pct_valid"]:
                 extracted_data["pipeline_errors"].append(tax_valid["details"])

            # Mock VAT number and country determination
            mock_vat_number = "IN1234567890" # Replace with actual extracted VAT
            mock_address_text = "Some address, India" # Replace with actual extracted address
            vat_valid = self.tax_validator.validate_vat_registration(mock_vat_number)
            extracted_data["vat_reg_valid"] = vat_valid["vat_reg_valid"]
            if not extracted_data["vat_reg_valid"]:
                 extracted_data["pipeline_errors"].append(vat_valid["details"])

            extracted_data["country_determined"] = self.tax_validator.determine_country(mock_address_text)

            # Step 4: Outlier Detection (Mocked for now)
            outlier_check = self.outlier_detector.detect_outlier(extracted_data["total_inr"])
            extracted_data["is_outlier"] = outlier_check["is_outlier"]
            if extracted_data["is_outlier"]:
                extracted_data["pipeline_errors"].append(outlier_check["reason"])


            # Final check on parsing success for this bill
            if not bill_details_from_ocr.get("parsed_successfully") and not extracted_data["pipeline_errors"]:
                 extracted_data["pipeline_errors"].append("Initial OCR parsing was partial/ambiguous.")
            elif not bill_details_from_ocr.get("parsed_successfully") and extracted_data["pipeline_errors"]:
                 # Already has errors, so no need to add another "partial" message
                 pass
            elif not extracted_data["items"] and extracted_data["total_inr"] is None:
                extracted_data["pipeline_errors"].append("No items or total could be extracted.")


            return extracted_data

        except Exception as e:
            error_message = f"Critical error during pipeline execution for {file_name}: {e}"
            extracted_data["pipeline_errors"].append(error_message)
            print(error_message)
            return extracted_data

    def consolidate_bills(self, sub_bills_for_consolidation, consolidated_bill_id, customer_name, consolidated_date):
        """
        Consolidates multiple sub-bills for a specific customer.
        This function now accepts the processed dictionaries directly.
        """
        if not sub_bills_for_consolidation:
            return None

        consolidated_items_summary = []
        grand_total_inr = 0.0

        for sub_bill in sub_bills_for_consolidation:
            # Ensure 'total_inr' is a number; skip if not valid
            current_bill_total_inr = sub_bill.get('total_inr')
            if current_bill_total_inr is None or not isinstance(current_bill_total_inr, (int, float)):
                print(f"Warning: Skipping sub-bill {sub_bill.get('file_name', 'Unknown')} due to invalid total_inr: {current_bill_total_inr}")
                continue

            # We list each sub-bill as a line item on the consolidated bill summary
            consolidated_items_summary.append({
                "description": f"Bill: {sub_bill.get('file_name', 'N/A')} (ID: {sub_bill.get('bill_id', 'N/A')}, Date: {sub_bill.get('extracted_date', 'N/A')})",
                "quantity": 1,
                "unit_price_inr": current_bill_total_inr,
                "total_inr": current_bill_total_inr,
                "currency": "INR"
            })
            grand_total_inr += current_bill_total_inr

        if not consolidated_items_summary:
            print("No valid bills found for consolidation after filtering.")
            return None

        return {
            "consolidated_bill_id": consolidated_bill_id,
            "customer_name": customer_name,
            "consolidated_date": consolidated_date,
            "sub_bills_included": [sb.get('file_name', 'N/A') for sb in sub_bills_for_consolidation if sb.get('total_inr') is not None], # List original filenames
            "items_summary": consolidated_items_summary,
            "grand_total_inr": grand_total_inr
        }

    def print_receipt(self, bill_data, type="consolidated"):
        """
        Prints a bill or consolidated bill in a receipt-like format to the console.
        """
        if not bill_data:
            print("No bill data to print.")
            return

        width = 80

        print("\n" + "=" * width)
        if type == "consolidated":
            print(f"{'CONSOLIDATED EXPENSE REPORT':^{width}}")
            print(f"{'ID: ' + bill_data['consolidated_bill_id']:^{width}}")
        else:
            print(f"{'INDIVIDUAL RECEIPT SUMMARY':^{width}}")
            print(f"{'File: ' + bill_data['file_name']:^{width}}")

        print(f"{'Date: ' + bill_data['consolidated_date'] if type=='consolidated' else bill_data['extracted_date']:^{width}}")
        print(f"{'Time: ' + datetime.now().strftime('%H:%M:%S'):^{width}}")
        print(f"{'Customer/Source: ' + bill_data['customer_name'] if type=='consolidated' else bill_data['extracted_company']:^{width}}")
        print("=" * width)

        print(f"{'Description':<40} {'Qty':>5} {'Unit Price':>12} {'Total INR':>12}")
        print("-" * width)

        if type == "consolidated":
            for item in bill_data['items_summary']:
                unit_price_formatted = f"{item['unit_price_inr']:.2f} INR"
                total_formatted = f"{item['total_inr']:.2f} INR"
                description_for_console = (item['description'][:37] + '...') if len(item['description']) > 40 else item['description']
                print(f"{description_for_console:<40} {item['quantity']:>5} {unit_price_formatted:>12} {total_formatted:>12}")
        else: # Individual receipt summary
            # This part will be a bit different as process_single_receipt returns a flat dict,
            # not nested items like the original parse_ocr_text_to_bill.
            # For now, let's just print the high-level summary fields
            print(f"{'Original Total:':<40} {bill_data.get('original_total', 'N/A'):>5} {bill_data.get('original_currency', 'N/A'):>12} {'':>12}")
            print(f"{'Total (INR):':<40} {'':>5} {'':>12} {bill_data.get('total_inr', 'N/A'):>12.2f} INR")
            print(f"{'Outlier:':<40} {str(bill_data.get('is_outlier', 'N/A')):<17} {'':>12} {'':>12}")
            print(f"{'Tax Valid:':<40} {str(bill_data.get('tax_pct_valid', 'N/A')):<17} {'':>12} {'':>12}")
            print(f"{'VAT Valid:':<40} {str(bill_data.get('vat_reg_valid', 'N/A')):<17} {'':>12} {'':>12}")
            print(f"{'Country:':<40} {bill_data.get('country_determined', 'N/A'):<17} {'':>12} {'':>12}")
            if bill_data.get('pipeline_errors'):
                print(f"{'Errors:':<40} {'; '.join(bill_data['pipeline_errors']):<37}")


        print("-" * width)
        if type == "consolidated":
            grand_total_formatted = f"Rs.{bill_data['grand_total_inr']:.2f}"
            print(f"{'GRAND TOTAL (INR)':<60} {grand_total_formatted:>15}")
            print("-" * width)
            print("\n--- Sub-Bills Included ---")
            for sb_file in bill_data['sub_bills_included']:
                print(f"- {sb_file}")
            print("-" * width)
        else:
             # Already printed above for individual receipts
             pass

        print("=" * width)
        print(f"{'THANK YOU FOR YOUR BUSINESS!':^{width}}")
        print("=" * width)


    def generate_pdf_report(self, bill_data, filename="report.pdf", type="consolidated"):
        """
        Generates a PDF report using ReportLab.
        This now includes the consolidated grand total directly.
        """
        if not bill_data:
            print("No bill data to generate PDF.")
            return

        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter # 8.5 * 11 inches

        # Ensure the global active_font_for_pdf is used
        font_name = active_font_for_pdf

        # Margins
        left_margin = 0.75 * inch
        right_margin = width - 0.75 * inch
        line_height = 0.2 * inch
        header_line_height = 0.25 * inch

        y_position = height - 0.75 * inch

        # --- Header Information ---
        c.setFont(font_name, 18)
        if type == "consolidated":
            c.drawString(left_margin, y_position, "CONSOLIDATED EXPENSE REPORT")
            y_position -= header_line_height
            c.setFont(font_name, 12)
            c.drawString(left_margin, y_position, f"Report ID: {bill_data['consolidated_bill_id']}")
            report_date = bill_data['consolidated_date']
            report_customer = bill_data['customer_name']
        else: # Individual receipt summary (less likely to be called directly but good to have)
            c.drawString(left_margin, y_position, "INDIVIDUAL RECEIPT SUMMARY")
            y_position -= header_line_height
            c.setFont(font_name, 12)
            c.drawString(left_margin, y_position, f"File: {bill_data.get('file_name', 'N/A')}")
            report_date = bill_data.get('extracted_date', 'N/A')
            report_customer = bill_data.get('extracted_company', 'N/A')


        y_position -= header_line_height
        c.drawString(left_margin, y_position, f"Date: {report_date}")
        y_position -= header_line_height
        c.drawString(left_margin, y_position, f"Time: {datetime.now().strftime('%H:%M:%S')}")
        y_position -= header_line_height
        c.drawString(left_margin, y_position, f"Customer/Source: {report_customer}")
        y_position -= header_line_height * 1.5

        c.line(left_margin, y_position, right_margin, y_position)
        y_position -= header_line_height

        # --- Column Headers ---
        c.setFont(font_name, 10)
        col_widths = {
            "description": 4.0 * inch,
            "qty": 0.7 * inch,
            "unit_price": 1.2 * inch,
            "total": 1.2 * inch
        }

        x_desc = left_margin
        x_qty = x_desc + col_widths["description"] + 0.1 * inch
        x_unit_price = x_qty + col_widths["qty"] + 0.1 * inch
        x_total = x_unit_price + col_widths["unit_price"] + 0.1 * inch

        c.drawString(x_desc, y_position, "Description")
        c.drawString(x_qty, y_position, "Qty")
        c.drawRightString(x_unit_price + col_widths["unit_price"], y_position, "Unit Price")
        c.drawRightString(x_total + col_widths["total"], y_position, "Total (INR)") # Label now says "Total (INR)"

        y_position -= 0.15 * inch
        c.line(left_margin, y_position, right_margin, y_position)
        y_position -= 0.15 * inch

        # --- Bill Items (from consolidated_items_summary) ---
        c.setFont(font_name, 9)

        items_to_draw = bill_data['items_summary']

        for item in items_to_draw:
            if y_position < 1.5 * inch:
                c.showPage()
                y_position = height - 0.75 * inch
                c.setFont(font_name, 10)
                c.drawString(x_desc, y_position, "Description")
                c.drawString(x_qty, y_position, "Qty")
                c.drawRightString(x_unit_price + col_widths["unit_price"], y_position, "Unit Price")
                c.drawRightString(x_total + col_widths["total"], y_position, "Total (INR)")
                y_position -= 0.15 * inch
                c.line(left_margin, y_position, right_margin, y_position)
                y_position -= 0.15 * inch
                c.setFont(font_name, 9)

            description = item['description']
            if c.stringWidth(description, font_name, 9) > col_widths["description"]:
                while c.stringWidth(description + "...", font_name, 9) > col_widths["description"] and len(description) > 3:
                    description = description[:-1]
                description += "..."

            c.drawString(x_desc, y_position, description)
            c.drawString(x_qty, y_position, str(item['quantity']))

            # For consolidated report, Unit Price is already in INR
            unit_price_formatted = f"Rs. {item['unit_price_inr']:.2f}"
            total_formatted = f"Rs. {item['total_inr']:.2f}" # Total is also in INR

            c.drawRightString(x_unit_price + col_widths["unit_price"], y_position, unit_price_formatted)
            c.drawRightString(x_total + col_widths["total"], y_position, total_formatted)

            y_position -= line_height

        y_position -= 0.15 * inch
        c.line(left_margin, y_position, right_margin, y_position)

        y_position -= header_line_height
        c.setFont(font_name, 12)

        # Grand Total Section
        grand_total_formatted = f"Rs. {bill_data['grand_total_inr']:.2f}"
        c.drawString(left_margin, y_position, "GRAND TOTAL (INR):")
        c.drawRightString(right_margin, y_position, grand_total_formatted)
        y_position -= header_line_height
        c.line(left_margin, y_position, right_margin, y_position)

        y_position -= header_line_height # Space
        c.setFont(font_name, 10)
        c.drawString(left_margin, y_position, "Individual Bills Included:")
        y_position -= 0.15 * inch
        for sb_file in bill_data['sub_bills_included']:
            if y_position < 1 * inch:
                c.showPage()
                y_position = height - 0.75 * inch
                c.setFont(font_name, 10)
                c.drawString(left_margin, y_position, "Individual Bills Included (Cont.):")
                y_position -= 0.15 * inch
            c.drawString(left_margin + 0.25 * inch, y_position, f"- {sb_file}")
            y_position -= 0.15 * inch
        c.line(left_margin, y_position, right_margin, y_position)

        y_position -= 0.5 * inch
        c.setFont(font_name, 14)
        c.drawCentredString(width / 2.0, y_position, "THANK YOU FOR YOUR BUSINESS!")

        c.save()
        print(f"\nPDF report saved as: {filename}")