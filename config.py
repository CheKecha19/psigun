# Конфигурация приложения
TELEGRAM_CONFIG = {
    "token": "5861751467:AAGX4sHWp4Gd99jZCFa9SJR-nhAKpQ0qQFM",
    "chat_id": "983521024",
    "bot_enabled": True
}

# Настройки анализа
ARBITRAGE_CONFIG = {
    "min_profit_threshold": 0.1,
    "enable_telegram": True,
    "cross_exchange_analysis": True,
    "max_opportunities_per_message": 10  # Ограничение для бота
}

# Настройки бирж
EXCHANGES_CONFIG = {
    "bybit": {
        "enabled": True,
        "timeout": 10,
        "testnet": False
    },
    "okx": {
        "enabled": True,
        "timeout": 10,
        "testnet": False,
        "api_key": "8ae59fa3-37e7-4b14-b43a-c36e77aea020",
        "api_secret": "9767D8BD83B9A12C2A7F243EFD5BBF8B",
        "passphrase": "Cherokee19!"
    },
    "binance": {
        "enabled": True,
        "timeout": 10,
        "api_key": "yy1U0kHPSX5g9nuuckD5cgGvf6GYOXBF4yIGW9gv7H3gBoOOMVFPWV3c8Iq3wJVW",
        "api_secret": "auGTt8QcuiD2DlP8MOJe1voBlKbIaulMHVj2uCg8A8QAhrUP42Vq6CzdNg48Zeju"
    }
}