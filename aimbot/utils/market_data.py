import yfinance as yf
import logging

logger = logging.getLogger('aimbot')

def get_market_data(ticker):
    """
    Fetch recent market data for the given ticker using yfinance.
    Returns a dictionary with price, volume, MA20, and average volume.
    """
    try:
        data = yf.Ticker(ticker).history(period="5d")
        if data.empty:
            logger.warning(f"No data found for ticker: {ticker}")
            return {}

        latest = data.iloc[-1]
        ma20 = data['Close'].rolling(window=20).mean().iloc[-1]

        return {
            "price": latest['Close'],
            "volume": latest['Volume'],
            "ma20": ma20,
            "avg_volume": data['Volume'].mean()
        }

    except Exception as e:
        logger.error(f"Error fetching market data for {ticker}: {e}")
        return {}
