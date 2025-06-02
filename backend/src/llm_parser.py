# src/llm_parser.py

class LLMParser:
    def _init_(self, model_name="mock_llm"):
        self.model_name = model_name
        print(f"LLMParser initialized with model: {self.model_name} (Currently a mock service)")

    def parse_document(self, ocr_text):
        """
        Mocks LLM-based parsing. In a real scenario, this would send OCR text
        to an LLM (e.g., OpenAI, Gemini, Hugging Face) for structured extraction.
        For now, it returns a very basic structure.
        """
        print("  (LLM Parsing: Mocking response for now)")
        # In a real scenario, LLM would extract this
        extracted_data = {
            "company_name": "Extracted Co. (LLM)",
            "invoice_date": "2023-01-15",
            "total_amount": 123.45,
            "currency": "USD",
            "items": [
                {"description": "LLM Item 1", "quantity": 1, "unit_price": 50.0},
                {"description": "LLM Item 2", "quantity": 2, "unit_price": 36.72}
            ],
            "extracted_by_llm": True
        }
        return extracted_data

    def validate_extracted_data(self, extracted_data):
        """
        Mocks LLM-based validation.
        """
        print("  (LLM Validation: Mocking response for now)")
        return {"is_valid": True, "reason": "Mock validation passed"}