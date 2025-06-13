# main.py
from core.aimbot import AimBot

if __name__ == "__main__":
    bot = AimBot()
    news_item = {
        "text": "Tesla ($TSLA) reports record profits and surging demand!"
    }
    result = bot.process_news_item(news_item)
    print(result)
