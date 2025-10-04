# main.py
import sys
import os
from typing import Dict, List

# Добавляем пути для импорта модулей
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from config import TELEGRAM_CONFIG, ARBITRAGE_CONFIG, EXCHANGES_CONFIG
from exchanges.bybit.bybit_exchange import BybitExchange
from exchanges.okx.okx_exchange import OkxExchange
from exchanges.binance.binance_exchange import BinanceExchange
from core.arbitrage_analyzer import ArbitrageAnalyzer
from core.telegram_notifier import TelegramNotifier
from core.cross_exchange_analyzer import CrossExchangeAnalyzer
from utils.data_normalizer import DataNormalizer  # Исправлен импорт

class ArbitrageBot:
    """Основной бот для арбитражного анализа"""
    
    def __init__(self):
        self.telegram_notifier = TelegramNotifier(TELEGRAM_CONFIG)
        self.exchanges = self._initialize_exchanges()
        self.analyzer = ArbitrageAnalyzer(min_profit_threshold=ARBITRAGE_CONFIG["min_profit_threshold"])
        self.cross_analyzer = CrossExchangeAnalyzer(min_profit_threshold=ARBITRAGE_CONFIG["min_profit_threshold"])
    
    def _initialize_exchanges(self):
        """Инициализировать все биржи"""
        exchanges = []
        
        if EXCHANGES_CONFIG["bybit"]["enabled"]:
            exchanges.append(BybitExchange(EXCHANGES_CONFIG["bybit"]))
            print("✅ Bybit exchange initialized")
        
        if EXCHANGES_CONFIG["okx"]["enabled"]:
            exchanges.append(OkxExchange(EXCHANGES_CONFIG["okx"]))
            print("✅ OKX exchange initialized")
        
        if EXCHANGES_CONFIG["binance"]["enabled"]:
            exchanges.append(BinanceExchange(EXCHANGES_CONFIG["binance"]))
            print("✅ Binance exchange initialized")
        
        return exchanges
    
    def collect_all_data(self):
        """Собрать все данные с бирж"""
        print("\n📊 СБОР ДАННЫХ С БИРЖ...")
        all_data = {}
        
        for exchange in self.exchanges:
            print(f"\n🔍 Сбор данных с {exchange.name}...")
            try:
                loan_rates = exchange.get_loan_rates()
                staking_rates = exchange.get_staking_rates()
                
                all_data[exchange.name] = {
                    'loan_rates': loan_rates,
                    'staking_rates': staking_rates,
                    'exchange': exchange
                }
                
                print(f"✅ {exchange.name}: {len(loan_rates)} займов, {len(staking_rates)} стейкингов")
                
            except Exception as e:
                print(f"❌ Ошибка сбора данных с {exchange.name}: {e}")
                all_data[exchange.name] = {'loan_rates': {}, 'staking_rates': {}, 'exchange': exchange}
        
        return all_data
    
    def find_best_staking_opportunities(self, all_data: Dict) -> List[Dict]:
        """Найти лучшие стейкинги на всех биржах"""
        best_staking = []
        
        for exchange_name, data in all_data.items():
            staking_rates = data['staking_rates']
            
            for coin, staking_info in staking_rates.items():
                apy = staking_info.get('apy', 0)
                
                if apy > 5:  # Фильтр для хороших стейкингов
                    best_staking.append({
                        'coin': coin,
                        'apy': apy,
                        'exchange': exchange_name,
                        'min_amount': staking_info.get('min_amount', 0),
                        'max_amount': staking_info.get('max_amount', 0)
                    })
        
        # Сортируем по убыванию APY
        return sorted(best_staking, key=lambda x: x['apy'], reverse=True)
    
    def find_hot_loan_opportunities(self, all_data: Dict) -> List[Dict]:
        """Найти дорогие займы (суета в монете)"""
        hot_loans = []
        
        for exchange_name, data in all_data.items():
            loan_rates = data['loan_rates']
            
            for coin, loan_info in loan_rates.items():
                rate = loan_info.get('rate', 0)
                
                if rate > 15:  # Высокие ставки по займам
                    reason = self._get_loan_reason(rate)
                    hot_loans.append({
                        'coin': coin,
                        'rate': rate,
                        'exchange': exchange_name,
                        'min_amount': loan_info.get('min_amount', 0),
                        'max_amount': loan_info.get('max_amount', 0),
                        'reason': reason
                    })
        
        # Сортируем по убыванию ставки
        return sorted(hot_loans, key=lambda x: x['rate'], reverse=True)
    
    def _get_loan_reason(self, rate: float) -> str:
        """Получить причину высокой ставки"""
        if rate > 50:
            return "🚀 ОЧЕНЬ ВЫСОКАЯ ДОХОДНОСТЬ"
        elif rate > 30:
            return "🔥 ВЫСОКИЙ СПРОС"
        elif rate > 20:
            return "⚡ ПОВЫШЕННЫЙ СПРОС"
        elif rate > 15:
            return "📈 АКТИВНАЯ ТОРГОВЛЯ"
        else:
            return "📊 СТАНДАРТНАЯ СТАВКА"

    def find_intra_exchange_opportunities(self, all_data: Dict):
        """Найти внутрибиржевые возможности"""
        print("\n🎯 ПОИСК ВНУТРИБИРЖЕВЫХ ВОЗМОЖНОСТЕЙ...")
        intra_opportunities = []
    
        for exchange_name, data in all_data.items():
            exchange = data['exchange']
            loan_rates = data['loan_rates']
            staking_rates = data['staking_rates']
        
            print(f"\n🔍 Анализ {exchange_name}...")
        
            # Находим общие монеты
            common_coins = set(loan_rates.keys()) & set(staking_rates.keys())
            print(f"   📊 Общих монет: {len(common_coins)}")
        
            for coin in common_coins:
                lending_info = loan_rates[coin]
                staking_info = staking_rates[coin]
                lending_rate = lending_info['rate']
                staking_apy = staking_info['apy']
                net_profit = staking_apy - lending_rate
            
                if net_profit >= self.analyzer.min_profit_threshold:
                    intra_opportunities.append({
                        "coin": coin,
                        "borrow_rate": lending_rate,
                        "borrow_exchange": exchange_name,
                        "staking_apy": staking_apy,
                        "staking_exchange": exchange_name,  # Всегда одинаковая биржа
                        "net_profit": net_profit,
                        "profitability": exchange.get_profitability_label(net_profit),
                        "type": "intra"
                    })
    
        # СОРТИРОВКА ПО УБЫВАНИЮ ПРИБЫЛИ
        return sorted(intra_opportunities, key=lambda x: x["net_profit"], reverse=True)
    
    def find_cross_exchange_opportunities(self, all_data: Dict):
        """Найти межбиржевые возможности"""
        print("\n🌐 ПОИСК МЕЖБИРЖЕВЫХ ВОЗМОЖНОСТЕЙ...")
        cross_opportunities = []
    
        # Собираем все стейкинги и займы в общие пулы
        all_staking_rates = {}
        all_loan_rates = {}
    
        for exchange_name, data in all_data.items():
            all_staking_rates[exchange_name] = data['staking_rates']
            all_loan_rates[exchange_name] = data['loan_rates']
    
        # Ищем лучшие комбинации
        for coin in self._get_all_coins(all_data):
            best_staking = self._find_best_staking(coin, all_staking_rates)
            best_loan = self._find_best_loan(coin, all_loan_rates)
        
            if best_staking and best_loan:
                staking_exchange, staking_apy = best_staking
                loan_exchange, loan_rate = best_loan
            
                # УБЕДИМСЯ, ЧТО БИРЖИ РАЗНЫЕ
                if staking_exchange != loan_exchange:
                    net_profit = staking_apy - loan_rate
                
                    if net_profit >= self.cross_analyzer.min_profit_threshold:
                        cross_opportunities.append({
                            "coin": coin,
                            "borrow_rate": loan_rate,
                            "borrow_exchange": loan_exchange,
                            "staking_apy": staking_apy,
                            "staking_exchange": staking_exchange,
                            "net_profit": net_profit,
                            "profitability": self._get_profitability_label(net_profit),
                            "type": "cross"
                        })
    
        # СОРТИРОВКА ПО УБЫВАНИЮ ПРИБЫЛИ
        return sorted(cross_opportunities, key=lambda x: x["net_profit"], reverse=True)
    
    def _get_all_coins(self, all_data: Dict):
        """Получить все уникальные монеты"""
        all_coins = set()
        for data in all_data.values():
            all_coins.update(data['loan_rates'].keys())
            all_coins.update(data['staking_rates'].keys())
        return all_coins
    
    def _find_best_staking(self, coin: str, all_staking_rates: Dict):
        """Найти лучший стейкинг для монеты"""
        best_apy = 0
        best_exchange = None
        
        for exchange_name, staking_rates in all_staking_rates.items():
            if coin in staking_rates:
                apy = staking_rates[coin]['apy']
                if apy > best_apy:
                    best_apy = apy
                    best_exchange = exchange_name
        
        return (best_exchange, best_apy) if best_exchange else None
    
    def _find_best_loan(self, coin: str, all_loan_rates: Dict):
        """Найти лучший займ для монеты"""
        best_rate = float('inf')
        best_exchange = None
        
        for exchange_name, loan_rates in all_loan_rates.items():
            if coin in loan_rates:
                rate = loan_rates[coin]['rate']
                if rate < best_rate:
                    best_rate = rate
                    best_exchange = exchange_name
        
        return (best_exchange, best_rate) if best_exchange else None
    
    def _get_profitability_label(self, net_profit: float) -> str:
        """Получить метку прибыльности"""
        return DataNormalizer.get_profitability_label(net_profit)
    
    def create_summary_table(self, intra_opportunities: List, cross_opportunities: List):
        """Создать сводную таблицу всех возможностей БЕЗ ДУБЛИКАТОВ"""
        print("\n📈 СОЗДАНИЕ СВОДНОЙ ТАБЛИЦЫ...")
    
        # Создаем словарь для уникальных возможностей
        # Ключ: (coin, borrow_exchange, staking_exchange)
        unique_opportunities = {}
    
        # Добавляем внутрибиржевые возможности
        for opp in intra_opportunities:
            key = (opp["coin"], opp["borrow_exchange"], opp["staking_exchange"])
            if key not in unique_opportunities:
                unique_opportunities[key] = opp
    
        # Добавляем межбиржевые возможности
        for opp in cross_opportunities:
            key = (opp["coin"], opp["borrow_exchange"], opp["staking_exchange"])
            if key not in unique_opportunities:
                unique_opportunities[key] = opp
    
        # Преобразуем обратно в список и сортируем по убыванию прибыли
        all_opportunities = list(unique_opportunities.values())
        return sorted(all_opportunities, key=lambda x: x["net_profit"], reverse=True)
    
    def display_results(self, intra_opportunities: List, cross_opportunities: List, summary_opportunities: List):
        """Показать результаты в консоли"""
    
        # Внутрибиржевые возможности (уже отсортированы)
        print(f"\n🎯 ВНУТРИБИРЖЕВЫЕ ВОЗМОЖНОСТИ (топ-20):")
        self._display_opportunities_table(intra_opportunities[:20], "intra")
    
        # Межбиржевые возможности (уже отсортированы)
        print(f"\n🌐 МЕЖБИРЖЕВЫЕ ВОЗМОЖНОСТИ (топ-20):")
        self._display_opportunities_table(cross_opportunities[:20], "cross")
    
        # Сводная таблица (уже отсортирована и без дубликатов)
        print(f"\n📊 СВОДНАЯ ТАБЛИЦА ВСЕХ ВОЗМОЖНОСТЕЙ (топ-20):")
        self._display_opportunities_table(summary_opportunities[:20], "summary")
    
    def _display_opportunities_table(self, opportunities: List, opp_type: str):
        """Показать таблицу возможностей"""
        if not opportunities:
            print("❌ Возможности не найдены")
            return
        
        print(f"{'Монета':<10} {'Займ на':<12} {'Стейкинг на':<12} {'Ставка займа':<14} {'Доходность':<12} {'Чистая прибыль':<15} {'Прибыльность':<12}")
        print("=" * 95)
        
        for i, opp in enumerate(opportunities, 1):
            # Цвета для консоли с новыми индикаторами
            if opp["net_profit"] > 100:
                color = "\033[95m"  # Фиолетовый
            elif opp["net_profit"] > 50:
                color = "\033[91m"  # Красный
            elif opp["net_profit"] > 20:
                color = "\033[95m"  # Фиолетовый
            elif opp["net_profit"] > 15:
                color = "\033[92m"  # Зеленый
            elif opp["net_profit"] > 10:
                color = "\033[93m"  # Желтый
            elif opp["net_profit"] > 2:
                color = "\033[94m"  # Синий
            else:
                color = "\033[91m"  # Красный
            reset = "\033[0m"
            
            print(f"{i:2d}. {opp['coin']:<8} {opp['borrow_exchange'][:10]:<10} {opp['staking_exchange'][:10]:<10} "
                  f"{opp['borrow_rate']:<13.4f} {opp['staking_apy']:<11.2f} "
                  f"{color}{opp['net_profit']:<14.2f}{reset} {opp['profitability']:<12}")
    
    def send_telegram_reports(self, intra_opportunities: List, cross_opportunities: List, summary_opportunities: List):
        """Отправить отчеты в Telegram"""
        print("\n📨 ОТПРАВКА ОТЧЕТОВ В TELEGRAM...")
        
        # Внутрибиржевые возможности
        if intra_opportunities:
            self.telegram_notifier.send_opportunities(
                intra_opportunities[:20], 
                "🎯 ВНУТРИБИРЖЕВЫЕ АРБИТРАЖНЫЕ ВОЗМОЖНОСТИ"
            )
        
        # Межбиржевые возможности
        if cross_opportunities:
            self.telegram_notifier.send_opportunities(
                cross_opportunities[:20],
                "🌐 МЕЖБИРЖЕВЫЕ АРБИТРАЖНЫЕ ВОЗМОЖНОСТИ"
            )
        
        # Сводная таблица
        if summary_opportunities:
            self.telegram_notifier.send_opportunities(
                summary_opportunities[:20],
                "📊 СВОДНАЯ ТАБЛИЦА ЛУЧШИХ ВОЗМОЖНОСТЕЙ"
            )

def main():
    """Главная функция приложения"""
    print("🚀 ЗАПУСК АРБИТРАЖНОГО АНАЛИЗАТОРА")
    print("=" * 60)
    
    # Инициализация бота
    bot = ArbitrageBot()
    
    if not bot.exchanges:
        print("❌ Нет активных бирж в конфигурации")
        return
    
    # Отправляем уведомление о начале анализа
    bot.telegram_notifier.send_message("🔄 <b>Начинаю анализ арбитражных возможностей...</b>", silent=True)
    
    try:
        # 1. Сбор данных со всех бирж
        all_data = bot.collect_all_data()
        
        # 2. Поиск внутрибиржевых возможностей
        intra_opportunities = bot.find_intra_exchange_opportunities(all_data)
        
        # 3. Поиск межбиржевых возможностей
        cross_opportunities = bot.find_cross_exchange_opportunities(all_data)
        
        # 4. Создание сводной таблицы
        summary_opportunities = bot.create_summary_table(intra_opportunities, cross_opportunities)
        
        # 5. Показать результаты в консоли
        bot.display_results(intra_opportunities, cross_opportunities, summary_opportunities)
        
        # 6. Отправить отчеты в Telegram
        bot.send_telegram_reports(intra_opportunities, cross_opportunities, summary_opportunities)
        
        # Статистика
        print(f"\n📊 ФИНАЛЬНАЯ СТАТИСТИКА:")
        print(f"   • Внутрибиржевых возможностей: {len(intra_opportunities)}")
        print(f"   • Межбиржевых возможностей: {len(cross_opportunities)}")
        print(f"   • Всего возможностей: {len(summary_opportunities)}")
        
        if summary_opportunities:
            best_profit = summary_opportunities[0]["net_profit"]
            print(f"   • Лучшая возможность: {best_profit:.2f}%")
        
        print("\n✅ АНАЛИЗ ЗАВЕРШЕН!")
        
    except Exception as e:
        error_msg = f"❌ Критическая ошибка: {str(e)}"
        print(error_msg)
        bot.telegram_notifier.send_message(f"❌ <b>Ошибка при анализе:</b>\n<code>{str(e)}</code>")

if __name__ == "__main__":
    main()