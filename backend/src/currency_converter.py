# src/currency_converter.py

EXCHANGE_RATES = {
    "INR": 1.0,
    "USD": 83.50, # Example rate (1 USD = 83.50 INR)
    "EUR": 90.00, # Example rate
    "GBP": 105.00, # Example rate
    "JPY": 0.55,  # Example rate (1 JPY = 0.55 INR)
    "AED": 22.75, # UAE Dirham example rate
}

def convert_to_inr(amount, currency_code):
    """
    Converts an amount from a given currency to INR using predefined rates.
    Returns the converted amount and a boolean indicating success.
    """
    if amount is None or amount == "" : # Handle empty or None amounts
        return 0.0, False # Treat as zero, indicate failure

    currency_code = str(currency_code).upper().strip() # Ensure string and uppercase
    try:
        amount = float(amount) # Ensure amount is float
    except ValueError:
        print(f"Warning: Could not convert amount '{amount}' to float for currency conversion.")
        return 0.0, False # Return zero, indicate failure

    if currency_code not in EXCHANGE_RATES:
        print(f"Warning: Currency code '{currency_code}' not supported in EXCHANGE_RATES. Defaulting to original amount.")
        return amount, False # Return original amount, indicate failure

    if currency_code == "INR":
        return amount, True # No conversion needed if already INR

    inr_value = amount * EXCHANGE_RATES[currency_code]
    return inr_value, True