# HackVortex_ExpenseFlowGlobal
1. Ishaan Chepurwar (Team Leader)
2. Chinmay Inamdar
3. Raman Gandewar

# Cross-Border Expense Reconciliation System

🔗 Live Demo
Website: https://expenseflowglobal.vercel.app/

The ExpenseFlow Global website is a professional fintech SaaS platform for multinational corporations, streamlining cross-border expense reconciliation. It emphasizes real-time processing and AI-powered compliance. The site features a modern, clean design with a focus on clarity and user experience. All “Start Free Trial” buttons direct users to a comprehensive demo payment page, ensuring a smooth and professional conversion experience.

A production-grade Python system for automated processing and reconciliation of cross-border expense receipts using OCR, LLM parsing, tax validation, currency conversion, and anomaly detection.

## Features

- **OCR Processing**: PaddleOCR-based text extraction from receipts/invoices (PDF, JPG, PNG)
- **LLM Parsing**: TinyLlama-based structured data extraction
- **Tax Validation**: Multi-country VAT/GST validation with JSON schema
- **Currency Conversion**: Real-time and historical exchange rates
- **Anomaly Detection**: Isolation Forest-based outlier detection
- **File Watching**: Automated processing of new files
- **Batch Processing**: Process multiple files at once

<p align="center">
  <img src="https://github.com/Ish81/HackVortex_ExpenseFlowGlobal/blob/main/gif.mp4" alt="ExpenseFlow Global Demo" width="700"/>
</p>


## Architecture Overview

The following diagram illustrates the high-level architecture of **ExpenseFlow Global**, showcasing how different components such as OCR, LLM parsing, tax validation, currency conversion, and anomaly detection are orchestrated in the pipeline.

<p align="center">
  <img src="Add ExpenseFlow Global architecture image.jpg" alt="ExpenseFlow Global Architecture" width="700"/>
</p>

## Installation

### Google Colab
```python
# Run this in a Colab cell
!git clone <your-repo-url>
%cd ExpenseReconciliation
exec(open('colab_setup.py').read())
```

### Linux/Local
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install poppler-utils tesseract-ocr

# Install Python dependencies
pip install -r requirements.txt

# Setup environment
python run_pipeline.py --mode setup --install-deps --create-samples
```

## Quick Start

### 1. Generate Mock Data
```python
from data.mock_services.generate_mock_data import main as generate_mock_data
generate_mock_data()
```

### 2. Batch Processing
```bash
python run_pipeline.py --mode batch --input-dir data/incoming_receipts --output-dir data/reconciled_results
```

### 3. Watch Mode (Continuous)
```bash
python run_pipeline.py --mode watch --input-dir data/incoming_receipts --output-dir data/reconciled_results
```

### 4. Programmatic Usage
```python
from src.orchestrator import ExpenseOrchestrator

# Initialize orchestrator
orchestrator = ExpenseOrchestrator()

# Process single file
result = orchestrator.process_single_file("receipt.jpg")

# Process directory
results = orchestrator.process_directory("input/", "output/")
```

## Directory Structure
```
ExpenseReconciliation/
├── src/
│   ├── ocr_paddle.py          # OCR service
│   ├── llm_parser.py          # LLM parsing
│   ├── tax_validator.py       # Tax validation
│   ├── currency_converter.py  # Currency conversion
│   ├── outlier_detector.py    # Anomaly detection
│   ├── orchestrator.py        # Main coordinator
│   └── watcher.py            # File watching
├── data/
│   ├── incoming_receipts/     # Input files
│   ├── reconciled_results/    # Output JSON
│   └── mock_services/         # Mock data
├── models/                    # ML models
├── requirements.txt
├── run_pipeline.py           # Main entry point
├── colab_setup.py           # Colab setup
└── README.md
```

## Configuration

### Tax Rules (`data/mock_services/tax_rules.json`)
```json
{
  "vat_rates": {
    "IN": [0, 5, 12, 18, 28],
    "US": [0, 6, 7, 8, 10]
  },
  "currency_countries": {
    "INR": "IN",
    "USD": "US"
  }
}
```

### Currency Rates (`data/mock_services/rates.json`)
```json
{
  "base_currency": "USD",
  "rates": {
    "USD": 1.0,
    "EUR": 0.85,
    "INR": 83.25
  }
}
```

## Output Format

Each processed receipt generates a JSON file with:

```json
{
  "file_path": "receipt.jpg",
  "processed_at": "2024-01-15T10:30:00",
  "status": "completed",
  "ocr_data": [...],
  "parsed_data": {
    "merchant": "Tech Store",
    "date": "2024-01-15",
    "total": 1453.65,
    "currency": "USD",
    "vat_pct": 8.0
  },
  "validation_results": {
    "schema_valid": true,
    "vat_valid": true
  },
  "converted_amounts": {
    "original_amount": 1453.65,
    "converted_amount": 121000.0,
    "target_currency": "INR"
  },
  "outlier_results": {
    "is_outlier": false,
    "anomaly_score": 0.1
  }
}
```

## Supported Countries & Currencies

- **India**: INR, GST validation
- **United States**: USD, Sales tax
- **United Kingdom**: GBP, VAT 
- **Germany**: EUR, VAT
- **Singapore**: SGD, GST
- **Australia**: AUD, GST
- **Canada**: CAD, GST/HST
- **Japan**: JPY, Consumption tax

## Error Handling

The system includes comprehensive error handling:
- Fallback regex parsing if LLM fails
- Default tax rules if validation files missing
- Dummy models for offline operation
- Graceful degradation for missing services

## Performance

- **OCR**: ~2-5 seconds per image
- **LLM**: ~3-10 seconds per document  
- **Validation**: <1 second
- **Throughput**: ~10-20 documents per minute

## Monitoring & Logging

All components include structured logging:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

Logs include:
- Processing progress
- Error messages
- Performance metrics
- Validation results

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
1. Check the logs for error messages
2. Verify file permissions and paths
3. Ensure all dependencies are installed
4. Test with sample data first
