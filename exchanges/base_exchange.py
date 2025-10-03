# exchanges/base_exchange.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from utils.data_normalizer import DataNormalizer  # Исправлен импорт

class BaseExchange(ABC):
    """Абстрактный базовый класс для всех бирж"""
    
    def __init__(self, name: str, config: Dict):
        self.name = name
        self.config = config
        self.base_url = ""
    
    @abstractmethod
    def get_loan_rates(self) -> Dict[str, Dict]:
        """Получить ставки по займам для всех монет с минимальными и максимальными суммами"""
        pass
    
    @abstractmethod
    def get_staking_rates(self) -> Dict[str, Dict]:
        """Получить ставки по стейкингу для всех монет с минимальными и максимальными суммами"""
        pass
    
    @abstractmethod
    def get_available_coins(self) -> List[str]:
        """Получить список доступных монет"""
        pass
    
    def get_profitability_label(self, net_profit: float) -> str:
        """Получить метку прибыльности с новыми индикаторами"""
        return DataNormalizer.get_profitability_label(net_profit)