import requests
import logging

logger = logging.getLogger(__name__)

# CoinGecko API for Dogecoin prices
COINGECKO_API = "https://api.coingecko.com/api/v3/simple/price"

# Supported currencies
SUPPORTED_CURRENCIES = [
    "usd", "eur", "gbp", "jpy", "cad", "aud", "cny", "chf", "sek", "nzd", 
    "krw", "btc", "eth", "ltc", "bch", "bnb", "ada", "dot", "link", "xlm"
]


def get_rate(currency="usd"):
    """
    Get the current Dogecoin price in the specified currency.
    
    Args:
        currency (str): The currency code (default: "usd")
        
    Returns:
        float: The current price of Dogecoin in the specified currency
        None: If the request fails or currency is not supported
    """
    currency = currency.lower()
    
    if currency not in SUPPORTED_CURRENCIES:
        logger.warning(f"Currency {currency} not supported. Using USD instead.")
        currency = "usd"
    
    try:
        params = {
            "ids": "dogecoin",
            "vs_currencies": currency
        }
        
        response = requests.get(COINGECKO_API, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        price = data.get("dogecoin", {}).get(currency)
        
        if price is None:
            logger.error(f"Price not found for currency: {currency}")
            return None
            
        return float(price)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Dogecoin price: {e}")
        return None
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Error parsing price data: {e}")
        return None


def get_multiple_rates(currencies=None):
    """
    Get Dogecoin prices in multiple currencies.
    
    Args:
        currencies (list): List of currency codes. If None, gets major currencies.
        
    Returns:
        dict: Dictionary with currency codes as keys and prices as values
    """
    if currencies is None:
        currencies = ["usd", "eur", "gbp", "btc", "eth"]
    
    # Filter out unsupported currencies
    currencies = [c.lower() for c in currencies if c.lower() in SUPPORTED_CURRENCIES]
    
    if not currencies:
        logger.warning("No supported currencies provided. Using USD.")
        currencies = ["usd"]
    
    try:
        params = {
            "ids": "dogecoin",
            "vs_currencies": ",".join(currencies)
        }
        
        response = requests.get(COINGECKO_API, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        prices = data.get("dogecoin", {})
        
        # Convert to float values
        result = {}
        for currency in currencies:
            price = prices.get(currency)
            if price is not None:
                result[currency.upper()] = float(price)
        
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Dogecoin prices: {e}")
        return {}
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Error parsing price data: {e}")
        return {}


def format_price(price, currency="USD"):
    """
    Format price for display.
    
    Args:
        price (float): The price value
        currency (str): The currency code
        
    Returns:
        str: Formatted price string
    """
    if price is None:
        return "Price unavailable"
    
    currency = currency.upper()
    
    # Special formatting for different currency types
    if currency in ["BTC", "ETH", "LTC", "BCH"]:
        # Crypto currencies - show more decimal places
        return f"{price:.8f} {currency}"
    elif currency in ["JPY", "KRW"]:
        # Currencies that don't use decimal places
        return f"{price:.0f} {currency}"
    else:
        # Fiat currencies - show 2-4 decimal places depending on value
        if price < 0.01:
            return f"{price:.6f} {currency}"
        elif price < 1:
            return f"{price:.4f} {currency}"
        else:
            return f"{price:.2f} {currency}"


def convert_doge_to_currency(doge_amount, currency="usd"):
    """
    Convert Dogecoin amount to specified currency.
    
    Args:
        doge_amount (float): Amount of Dogecoin
        currency (str): Target currency
        
    Returns:
        float: Converted amount, or None if conversion fails
    """
    rate = get_rate(currency)
    if rate is None:
        return None
    
    return float(doge_amount) * rate


def convert_currency_to_doge(amount, currency="usd"):
    """
    Convert currency amount to Dogecoin.
    
    Args:
        amount (float): Amount in the specified currency
        currency (str): Source currency
        
    Returns:
        float: Amount in Dogecoin, or None if conversion fails
    """
    rate = get_rate(currency)
    if rate is None or rate == 0:
        return None
    
    return float(amount) / rate


def is_currency_supported(currency):
    """
    Check if a currency is supported.
    
    Args:
        currency (str): Currency code to check
        
    Returns:
        bool: True if supported, False otherwise
    """
    return currency.lower() in SUPPORTED_CURRENCIES


def get_supported_currencies():
    """
    Get list of supported currencies.
    
    Returns:
        list: List of supported currency codes
    """
    return SUPPORTED_CURRENCIES.copy()
