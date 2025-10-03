from typing import List, Dict, Optional
from exchanges.base_exchange import BaseExchange

class ArbitrageAnalyzer:
    """Анализатор арбитражных возможностей"""
    
    def __init__(self, min_profit_threshold: float = 0.1):
        self.min_profit_threshold = min_profit_threshold