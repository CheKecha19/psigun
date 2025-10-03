# exchanges/binance/binance_exchange.py
import requests
import urllib3
import hmac
import hashlib
import time
from typing import Dict, List, Optional
from urllib.parse import urlencode
from ..base_exchange import BaseExchange  # Исправлен импорт
from .binance_loans import BinanceLoans
from .binance_flexible_savings import BinanceFlexibleSavings
from .binance_onchain_savings import BinanceOnchainSavings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BinanceExchange(BaseExchange):
    """Реализация API для Binance с использованием модульной структуры"""
    
    def __init__(self, config: Dict):
        super().__init__("Binance", config)
        self.base_url = "https://api.binance.com"
        self.api_key = config.get("api_key", "")
        self.api_secret = config.get("api_secret", "")
        
        # Инициализация модулей
        self.loans_module = BinanceLoans(self.base_url, config)
        self.flexible_savings_module = BinanceFlexibleSavings(self.base_url, config)
        self.onchain_savings_module = BinanceOnchainSavings(self.base_url, config)
        print("✅ Binance exchange initialized with modular structure")
    
    def get_loan_rates(self) -> Dict[str, Dict]:
        """Получить ставки по займам с Binance"""
        return self.loans_module.get_loan_rates()
    
    def get_staking_rates(self) -> Dict[str, Dict]:
        """Получить ставки по стейкингу с Binance"""
        print("🔍 Получение данных о стейкинге с Binance...")
        
        # Получаем данные из всех доступных модулей
        flexible_rates = self.flexible_savings_module.get_rates()
        onchain_rates = self.onchain_savings_module.get_rates()
        
        # Объединяем результаты, предпочитая более высокие ставки
        combined_rates = {}
        
        # Добавляем все гибкие ставки
        for coin, data in flexible_rates.items():
            combined_rates[coin] = data
        
        # Для ончейн ставок: если монета уже есть, берем максимальную ставку
        for coin, data in onchain_rates.items():
            if coin in combined_rates:
                if data['apy'] > combined_rates[coin]['apy']:
                    combined_rates[coin] = data
            else:
                combined_rates[coin] = data
        
        print(f"📊 Binance: объединено {len(flexible_rates)} гибких + {len(onchain_rates)} ончейн = {len(combined_rates)} ставок")
        return combined_rates
    
    def get_available_coins(self) -> List[str]:
        """Получить список доступных монет на Binance"""
        loan_rates = self.get_loan_rates()
        staking_rates = self.get_staking_rates()
        return list(set(loan_rates.keys()) | set(staking_rates.keys()))