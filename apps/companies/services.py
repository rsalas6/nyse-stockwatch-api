import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


# Excepción personalizada
class SymbolNotFoundException(Exception):
    pass


class QuotaExceededException(Exception):
    pass


def get_company_info_alpha(symbol):
    api_key = settings.ALPHA_VINTAGE_API_KEY
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        if not data or "Error Message" in data:
            raise SymbolNotFoundException(f"Symbol {symbol} not found.")

        return data

    except SymbolNotFoundException as e:
        logger.error(f"SymbolNotFoundException: {e}")
        raise
    except requests.RequestException as e:
        logger.error(
            f"RequestException: Error fetching data for symbol {symbol} from Alpha Vantage: {e}"
        )
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


def get_company_info_twelve(symbol):
    api_key = settings.TWELVE_DATA_API_KEY
    url = f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={api_key}"

    try:
        response = requests.get(url)
        data = response.json()

        if response.status_code == 429 or ("code" in data and data["code"] == 429):
            raise QuotaExceededException(data.get("message", "API quota exceeded."))

        if not data or "code" in data:
            raise SymbolNotFoundException(f"Symbol {symbol} not found on TwelveData.")

        return data

    except SymbolNotFoundException as e:
        logger.error(f"SymbolNotFoundException: {e}")
        raise
    except QuotaExceededException as e:
        logger.error(f"QuotaExceededException: {e}")
        raise
    except requests.RequestException as e:
        logger.error(
            f"RequestException: Error fetching data for symbol {symbol} from TwelveData: {e}"
        )
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


def get_market_data_twelve(symbol):
    api_key = settings.TWELVE_DATA_API_KEY
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1day&outputsize=7&apikey={api_key}"

    try:
        response = requests.get(url)
        data = response.json()

        if response.status_code == 429 or ("code" in data and data["code"] == 429):
            raise QuotaExceededException(data.get("message", "API quota exceeded."))

        if "code" in data or not data.get("values"):
            raise SymbolNotFoundException(
                f"Market data for symbol {symbol} not found on TwelveData."
            )

        return data["values"]  # This will return the market data for the last 7 days

    except SymbolNotFoundException as e:
        logger.error(f"SymbolNotFoundException: {e}")
        raise
    except QuotaExceededException as e:
        logger.error(f"QuotaExceededException: {e}")
        raise
    except requests.RequestException as e:
        logger.error(
            f"RequestException: Error fetching market data for symbol {symbol} from TwelveData: {e}"
        )
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
