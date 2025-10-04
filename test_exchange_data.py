# test_exchange_data.py
import sys
import os
from typing import Dict, List

# Добавляем пути для импорта модулей
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from config import EXCHANGES_CONFIG
from exchanges.bybit.bybit_exchange import BybitExchange
from exchanges.okx.okx_exchange import OkxExchange
from exchanges.binance.binance_exchange import BinanceExchange

def print_exchange_data(exchange_name: str, exchange):
    """Выводит данные по конкретной бирже"""
    print(f"\n{'='*60}")
    print(f"📊 ДАННЫЕ С {exchange_name.upper()}")
    print(f"{'='*60}")
    
    try:
        # Получаем данные о займах
        print(f"\n💰 ЗАЙМЫ:")
        loan_rates = exchange.get_loan_rates()
        print(f"   Получено {len(loan_rates)} монет для займов")
        
        # Выводим топ-10 монет по займам
        sorted_loans = sorted(loan_rates.items(), key=lambda x: x[1].get('rate', 0))
        for i, (coin, data) in enumerate(sorted_loans[:10]):
            rate = data.get('rate', 0)
            min_amount = data.get('min_amount', 0)
            max_amount = data.get('max_amount', 0)
            print(f"   {i+1:2d}. {coin:<8} Ставка: {rate:>6.2f}%  Мин: {min_amount:>8.2f}  Макс: {max_amount:>8.2f}")
        
        # Получаем данные о стейкинге
        print(f"\n🏦 СТЕЙКИНГ:")
        staking_rates = exchange.get_staking_rates()
        print(f"   Получено {len(staking_rates)} монет для стейкинга")
        
        # Выводим топ-10 монет по стейкингу
        sorted_staking = sorted(staking_rates.items(), key=lambda x: x[1].get('apy', 0), reverse=True)
        for i, (coin, data) in enumerate(sorted_staking[:10]):
            apy = data.get('apy', 0)
            min_amount = data.get('min_amount', 0)
            max_amount = data.get('max_amount', 0)
            print(f"   {i+1:2d}. {coin:<8} APY: {apy:>6.2f}%  Мин: {min_amount:>8.2f}  Макс: {max_amount:>8.2f}")
        
        # Находим общие монеты
        loan_coins = set(loan_rates.keys())
        staking_coins = set(staking_rates.keys())
        common_coins = loan_coins & staking_coins
        
        print(f"\n🎯 ОБЩИЕ МОНЕТЫ (для арбитража):")
        print(f"   Займы: {len(loan_coins)}, Стейкинг: {len(staking_coins)}, Общие: {len(common_coins)}")
        
        if common_coins:
            print(f"   Список общих монет: {', '.join(sorted(common_coins))}")
        else:
            print(f"   ❌ Нет общих монет для арбитража")
            
        # Анализ лучших возможностей
        print(f"\n🔍 АНАЛИЗ ЛУЧШИХ ВОЗМОЖНОСТЕЙ:")
        opportunities = []
        for coin in common_coins:
            loan_rate = loan_rates[coin]['rate']
            staking_apy = staking_rates[coin]['apy']
            net_profit = staking_apy - loan_rate
            opportunities.append({
                'coin': coin,
                'loan_rate': loan_rate,
                'staking_apy': staking_apy,
                'net_profit': net_profit
            })
        
        # Сортируем по убыванию прибыли
        opportunities.sort(key=lambda x: x['net_profit'], reverse=True)
        
        for i, opp in enumerate(opportunities[:5]):
            profit_label = "🟢 ВЫСОКАЯ" if opp['net_profit'] > 10 else "🟡 СРЕДНЯЯ" if opp['net_profit'] > 5 else "🔴 НИЗКАЯ"
            print(f"   {i+1:2d}. {opp['coin']:<8} Чистая прибыль: {opp['net_profit']:>6.2f}% ({profit_label})")
            print(f"        Займ: {opp['loan_rate']:>6.2f}% | Стейкинг: {opp['staking_apy']:>6.2f}%")
        
    except Exception as e:
        print(f"   ❌ Ошибка при получении данных: {e}")
        import traceback
        traceback.print_exc()

def test_all_exchanges():
    """Тестирует все биржи"""
    print("🚀 ТЕСТИРОВАНИЕ ДАННЫХ С БИРЖ")
    print("=" * 60)
    
    exchanges = []
    
    # Инициализируем биржи
    if EXCHANGES_CONFIG["bybit"]["enabled"]:
        exchanges.append(("Bybit", BybitExchange(EXCHANGES_CONFIG["bybit"])))
    
    if EXCHANGES_CONFIG["okx"]["enabled"]:
        exchanges.append(("OKX", OkxExchange(EXCHANGES_CONFIG["okx"])))
    
    if EXCHANGES_CONFIG["binance"]["enabled"]:
        exchanges.append(("Binance", BinanceExchange(EXCHANGES_CONFIG["binance"])))
    
    if not exchanges:
        print("❌ Нет активных бирж в конфигурации")
        return
    
    # Тестируем каждую биржу
    for exchange_name, exchange in exchanges:
        print_exchange_data(exchange_name, exchange)
    
    # Сводная статистика по всем биржам
    print(f"\n{'='*60}")
    print(f"📈 СВОДНАЯ СТАТИСТИКА ПО ВСЕМ БИРЖАМ")
    print(f"{'='*60}")
    
    all_loan_coins = set()
    all_staking_coins = set()
    
    for exchange_name, exchange in exchanges:
        try:
            loan_rates = exchange.get_loan_rates()
            staking_rates = exchange.get_staking_rates()
            
            all_loan_coins.update(loan_rates.keys())
            all_staking_coins.update(staking_rates.keys())
            
            common = set(loan_rates.keys()) & set(staking_rates.keys())
            print(f"\n{exchange_name}:")
            print(f"   Займы: {len(loan_rates)} монет")
            print(f"   Стейкинг: {len(staking_rates)} монет") 
            print(f"   Внутрибиржевые возможности: {len(common)}")
            
        except Exception as e:
            print(f"\n{exchange_name}: ❌ Ошибка - {e}")
    
    print(f"\n📊 ОБЩАЯ СТАТИСТИКА:")
    print(f"   Всего уникальных монет для займов: {len(all_loan_coins)}")
    print(f"   Всего уникальных монет для стейкинга: {len(all_staking_coins)}")
    print(f"   Всего уникальных монет: {len(all_loan_coins | all_staking_coins)}")
    
    # Топ монет по частоте встречаемости
    from collections import Counter
    
    print(f"\n🏆 ТОП-10 САМЫХ РАСПРОСТРАНЕННЫХ МОНЕТ:")
    # Здесь можно добавить анализ частоты монет, если нужно

def test_specific_coin(coin: str):
    """Тестирует конкретную монету на всех биржах"""
    print(f"\n🔍 ДЕТАЛЬНЫЙ АНАЛИЗ МОНЕТЫ {coin}")
    print(f"{'='*50}")
    
    exchanges = []
    
    if EXCHANGES_CONFIG["bybit"]["enabled"]:
        exchanges.append(("Bybit", BybitExchange(EXCHANGES_CONFIG["bybit"])))
    if EXCHANGES_CONFIG["okx"]["enabled"]:
        exchanges.append(("OKX", OkxExchange(EXCHANGES_CONFIG["okx"])))
    if EXCHANGES_CONFIG["binance"]["enabled"]:
        exchanges.append(("Binance", BinanceExchange(EXCHANGES_CONFIG["binance"])))
    
    for exchange_name, exchange in exchanges:
        print(f"\n{exchange_name}:")
        try:
            loan_rates = exchange.get_loan_rates()
            staking_rates = exchange.get_staking_rates()
            
            if coin in loan_rates:
                loan_data = loan_rates[coin]
                print(f"   💰 Займ: {loan_data.get('rate', 0):.2f}% (мин: {loan_data.get('min_amount', 0)})")
            else:
                print(f"   💰 Займ: ❌ не доступен")
            
            if coin in staking_rates:
                staking_data = staking_rates[coin]
                print(f"   🏦 Стейкинг: {staking_data.get('apy', 0):.2f}% (мин: {staking_data.get('min_amount', 0)})")
            else:
                print(f"   🏦 Стейкинг: ❌ не доступен")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

if __name__ == "__main__":
    # Запуск полного теста всех бирж
    test_all_exchanges()
    
    # Можно также протестировать конкретные монеты
    # test_specific_coin("BTC")
    # test_specific_coin("ETH")
    # test_specific_coin("USDT")
    
    print(f"\n✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")