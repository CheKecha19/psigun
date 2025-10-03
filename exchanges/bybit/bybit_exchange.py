# exchanges/bybit/bybit_exchange.py
import requests
import urllib3
from typing import Dict, List, Optional
from ..base_exchange import BaseExchange  # Исправлен импорт
from .bybit_loans import BybitLoans
from .bybit_flexible_savings import BybitFlexibleSavings
from .bybit_onchain_savings import BybitOnchainSavings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BybitExchange(BaseExchange):
    """Объединенная реализация API для Bybit (все продукты)"""
    
    def __init__(self, config: Dict):
        super().__init__("Bybit", config)
        self.base_url = "https://api.bybit.com"
        
        # Инициализация модулей
        self.loans_module = BybitLoans(self.base_url, config)
        self.flexible_savings_module = BybitFlexibleSavings(self.base_url, config)
        self.onchain_savings_module = BybitOnchainSavings(self.base_url, config)
    
    def get_loan_rates(self) -> Dict[str, Dict]:
        """Получить ставки по займам с Bybit"""
        return self.loans_module.get_loan_rates()
    
    def get_staking_rates(self) -> Dict[str, Dict]:
        """Получить ставки по всем типам стейкинга с Bybit"""
        print("🔍 Получение данных о всех типах стейкинга с Bybit...")
        
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
        
        print(f"📊 Bybit: объединено {len(flexible_rates)} гибких + {len(onchain_rates)} ончейн = {len(combined_rates)} ставок")
        return combined_rates
    
    def get_available_coins(self) -> List[str]:
        """Получить список доступных монет на Bybit"""
        loan_rates = self.get_loan_rates()
        staking_rates = self.get_staking_rates()
        return list(set(loan_rates.keys()) | set(staking_rates.keys()))