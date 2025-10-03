# bot_runner.py
import sys
import os

# Добавляем пути для импорта модулей
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def test_imports():
    """Тестирование импортов"""
    print("🧪 Тестирование импортов...")
    
    try:
        from exchanges.bybit.bybit_exchange import BybitExchange
        print("✅ BybitExchange импортирован успешно")
    except Exception as e:
        print(f"❌ Ошибка импорта BybitExchange: {e}")
    
    try:
        from exchanges.okx.okx_exchange import OkxExchange
        print("✅ OkxExchange импортирован успешно")
    except Exception as e:
        print(f"❌ Ошибка импорта OkxExchange: {e}")
    
    try:
        from exchanges.binance.binance_exchange import BinanceExchange
        print("✅ BinanceExchange импортирован успешно")
    except Exception as e:
        print(f"❌ Ошибка импорта BinanceExchange: {e}")
    
    try:
        from telegram_bot import main as telegram_main
        print("✅ Telegram бот импортирован успешно")
    except Exception as e:
        print(f"❌ Ошибка импорта Telegram бота: {e}")

def main():
    """Главный файл для запуска бота"""
    print("🚀 ЗАПУСК АРБИТРАЖНОГО БОТА")
    print("=" * 50)
    
    # Сначала тестируем импорты
    test_imports()
    
    try:
        # Проверяем наличие необходимых библиотек
        try:
            from telegram import __version__
            print(f"✅ python-telegram-bot установлен (версия {__version__})")
        except ImportError:
            print("❌ python-telegram-bot не установлен")
            print("Установите зависимости: pip install -r requirements.txt")
            return
        
        # Запускаем Telegram бота
        print("\n🤖 Запуск Telegram бота...")
        from telegram_bot import main as telegram_main
        telegram_main()
        
    except Exception as e:
        print(f"❌ Критическая ошибка при запуске: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()