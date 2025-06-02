
import os
import json
from datetime import datetime
from src.orchestrator import Orchestrator
from src.ocr_paddle import setup_tesseract_and_font # Renamed to reflect the content

def main():
    print("\n--- Expense Reconciliation Pipeline ---")
    print("Initializing services...")

    # Set up Tesseract and fonts (important for PDF generation)
    # This assumes NotoSans-Regular.ttf is placed in the project root or accessible path
    setup_tesseract_and_font()

    orchestrator = Orchestrator()

    print("\nProvide paths to your bill image/PDF files. Type 'end' when finished.")

    input_files = []
    bill_counter = 1
    while True:
        # Adjusted prompt to include PDF
        path = input(f"Enter path for Bill/Receipt {bill_counter} (e.g., 'data/incoming_receipts/bill1.png' or 'data/incoming_receipts/invoice.pdf') or 'end' to finish: ").strip()
        if path.lower() == 'end':
            break

        if os.path.exists(path):
            input_files.append(path)
            bill_counter += 1
        else:
            print(f"Warning: File '{path}' not found. Please check the path.")

    if not input_files:
        print("\nNo input files provided. Exiting application.")
        return

    print(f"\n--- Processing {len(input_files)} files ---")
    all_processed_sub_bills = []
    for idx, file_path in enumerate(input_files):
        print(f"\nProcessing file {idx+1}/{len(input_files)}: {file_path}")
        try:
            # The process_receipt_file in orchestrator will now return the parsed bill details
            processed_bill = orchestrator.process_single_receipt(file_path, idx + 1)
            if processed_bill:
                all_processed_sub_bills.append(processed_bill)
            else:
                print(f"Skipped {file_path} due to processing issues.")
        except Exception as e:
            print(f"An unexpected error occurred processing {file_path}: {e}")

    if not all_processed_sub_bills:
        print("\nNo valid bills were processed for consolidation. Exiting.")
        return

    print(f"\n--- Consolidating ALL processed bills into a single report ---")

    grand_consolidated_id = f"GRAND_CB_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    grand_consolidated_customer_name = "Overall Business Expenses" # Or prompt user
    consolidated_date = datetime.now().strftime('%Y-%m-%d')

    grand_consolidated_bill = orchestrator.consolidate_bills(
        all_processed_sub_bills,
        grand_consolidated_id,
        grand_consolidated_customer_name,
        consolidated_date
    )

    if grand_consolidated_bill:
        # Print to console (using orchestrator's print_receipt)
        orchestrator.print_receipt(grand_consolidated_bill, type="consolidated")

        # Generate PDF (using orchestrator's generate_pdf_receipt)
        output_dir = "data/reconciled_results"
        os.makedirs(output_dir, exist_ok=True)
        pdf_filename = os.path.join(output_dir, f"grand_consolidated_bill_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")
        orchestrator.generate_pdf_report(grand_consolidated_bill, filename=pdf_filename, type="consolidated")
    else:
        print("Could not generate a grand consolidated bill (no valid bills for consolidation).")

    print("\nPipeline finished.")

if _name_ == "_main_":
    main()