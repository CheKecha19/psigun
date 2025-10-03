# utils/data_normalizer.py
class DataNormalizer:
    """Класс для нормализации данных и меток прибыльности"""
    
    @staticmethod
    def get_profitability_label(net_profit: float) -> str:
        """Получить метку прибыльности с новыми индикаторами"""
        if net_profit > 100:
            return "🚀 СУПЕР ПРИБЫЛЬ"
        elif net_profit > 50:
            return "👑 ОЧЕНЬ ВЫСОКАЯ"
        elif net_profit > 20:
            return "👑 ОТЛИЧНАЯ"
        elif net_profit > 15:
            return "🟢 ХОРОШАЯ"
        elif net_profit > 10:
            return "🟡 НИЗКАЯ"
        elif net_profit > 2:
            return "🔵 БЕЗУБЫТОК"
        else:
            return "🔴 УБЫТОЧНАЯ"
    
    @staticmethod
    def normalize_percentage(value) -> float:
        """Нормализовать процентное значение"""
        try:
            if isinstance(value, str):
                # Удаляем символы % и пробелы
                value = value.replace('%', '').strip()
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    @staticmethod
    def normalize_amount(value) -> float:
        """Нормализовать денежное значение"""
        try:
            if isinstance(value, str):
                # Удаляем пробелы и нечисловые символы (кроме точки)
                value = ''.join(c for c in value if c.isdigit() or c == '.')
            return float(value) if value else 0.0
        except (ValueError, TypeError):
            return 0.0