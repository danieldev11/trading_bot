# nlp/sentiment_model.py
import logging
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger('aimbot')

class SentimentAnalyzer:
    def __init__(self, model_name="vader"):
        self.model_name = model_name
        logger.info(f"Initializing Sentiment Analyzer with {model_name}")
        self.model = SentimentIntensityAnalyzer()

    def analyze_text(self, text):
        scores = self.model.polarity_scores(text)
        compound = scores['compound']
        return {"score": compound, "confidence": abs(compound)}

    def extract_entities(self, text):
        tickers = re.findall(r'\$[A-Z]{1,5}', text)
        return [{"ticker": t[1:]} for t in tickers]
