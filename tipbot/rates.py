import requests
import logging
from decimal import Decimal
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Price API endpoints for TRMP (these would need to be actual APIs once TRMP is listed)
PRICE_APIS = {
    'coingecko': 'https://api.coingecko.com/api/v3/simple/price?ids=trumpow&vs_currencies=usd,eur,btc,eth',
    'coinmarketcap': 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol=TRMP',
    # Add more APIs as TRMP gets listed
}

# Fallback mock prices for development/testing
MOCK_PRICES = {
    'usd': 0.000001,  # $0.000001
    'eur': 0.00000095,
    'btc': 0.00000000001,
    'eth': 0.000000000005,
}


def get_rate(currency: str = 'usd') -> Optional[Decimal]:
    """
    Get TRMP price in specified currency
    
    Args:
        currency: Currency code (usd, eur, btc, etc.)
        
    Returns:
        Price as Decimal or None if unavailable
    """
    currency = currency.lower()
    
    # Try to get real price from APIs
    price = _fetch_real_price(currency)
    if price is not None:
        return price
    
    # Fallback to mock prices for development
    logger.warning(f"Using mock price for TRMP/{currency.upper()}")
    mock_price = MOCK_PRICES.get(currency)
    if mock_price:
        return Decimal(str(mock_price))
    
    logger.error(f"No price available for TRMP/{currency.upper()}")
    return None


def _fetch_real_price(currency: str) -> Optional[Decimal]:
    """
    Fetch real TRMP price from APIs
    Note: This will work once TRMP is listed on exchanges
    """
    # Try CoinGecko (most reliable for new tokens)
    try:
        price = _fetch_coingecko_price(currency)
        if price:
            return price
    except Exception as e:
        logger.warning(f"CoinGecko API failed: {e}")
    
    # Try other APIs here as they become available
    
    return None


def _fetch_coingecko_price(currency: str) -> Optional[Decimal]:
    """
    Fetch price from CoinGecko API
    Note: This assumes TRMP will be listed as 'trumpow' on CoinGecko
    """
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids=trumpow&vs_currencies={currency}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'trumpow' in data and currency in data['trumpow']:
                price = data['trumpow'][currency]
                return Decimal(str(price))
        
        logger.warning(f"CoinGecko: TRMP not found or {currency} not available")
        return None
        
    except Exception as e:
        logger.error(f"Error fetching from CoinGecko: {e}")
        return None


def get_rate_formatted(currency: str = 'usd') -> str:
    """
    Get formatted price string for display
    
    Args:
        currency: Currency code
        
    Returns:
        Formatted price string
    """
    rate = get_rate(currency)
    if rate is None:
        return f"Price unavailable for TRMP/{currency.upper()}"
    
    currency_upper = currency.upper()
    
    # Format based on currency type
    if currency in ['usd', 'eur']:
        if rate < Decimal('0.01'):
            return f"${rate:.8f} {currency_upper}" if currency == 'usd' else f"€{rate:.8f} {currency_upper}"
        else:
            return f"${rate:.4f} {currency_upper}" if currency == 'usd' else f"€{rate:.4f} {currency_upper}"
    elif currency in ['btc', 'eth']:
        return f"{rate:.12f} {currency_upper}"
    else:
        return f"{rate:.8f} {currency_upper}"


def convert_trmp_to_currency(trmp_amount: Decimal, currency: str = 'usd') -> Optional[Decimal]:
    """
    Convert TRMP amount to specified currency
    
    Args:
        trmp_amount: Amount in TRMP
        currency: Target currency
        
    Returns:
        Converted amount or None if conversion fails
    """
    rate = get_rate(currency)
    if rate is None:
        return None
    
    return trmp_amount * rate


def convert_currency_to_trmp(amount: Decimal, currency: str = 'usd') -> Optional[Decimal]:
    """
    Convert currency amount to TRMP
    
    Args:
        amount: Amount in specified currency
        currency: Source currency
        
    Returns:
        TRMP amount or None if conversion fails
    """
    rate = get_rate(currency)
    if rate is None or rate == 0:
        return None
    
    return amount / rate


def get_supported_currencies() -> list:
    """Get list of supported currencies"""
    return ['usd', 'eur', 'btc', 'eth']


def is_currency_supported(currency: str) -> bool:
    """Check if currency is supported"""
    return currency.lower() in get_supported_currencies()


# For backward compatibility
def format_currency(amount: Decimal, currency: str = 'usd') -> str:
    """Format amount with currency symbol"""
    currency = currency.lower()
    
    if currency == 'usd':
        return f"${amount:.4f}"
    elif currency == 'eur':
        return f"€{amount:.4f}"
    elif currency in ['btc', 'eth']:
        return f"{amount:.8f} {currency.upper()}"
    else:
        return f"{amount:.4f} {currency.upper()}"
