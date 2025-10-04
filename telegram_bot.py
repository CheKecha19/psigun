# telegram_bot.py
import asyncio
import logging
from typing import List, Dict, Optional, Any
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import sys
import os

# Добавляем пути для импорта модулей
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from config import TELEGRAM_CONFIG
from main import ArbitrageBot

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ArbitrageTelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.application = Application.builder().token(token).build()
        self.arbitrage_bot = None
        self.setup_handlers()
    
    def setup_handlers(self):
        """Настройка обработчиков команд"""
        # Основные команды
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("analyze", self.analyze_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("best_staking", self.best_staking_command))
        self.application.add_handler(CommandHandler("hot_loans", self.hot_loans_command))
        self.application.add_handler(CommandHandler("debug", self.debug_command))
        
        # Обработчик для любых текстовых сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        welcome_text = f"""
🤖 Привет, {user.first_name}!

Я - бот для анализа арбитражных возможностей между биржами.

📊 <b>Доступные команды:</b>
/analyze - Запустить анализ арбитражных возможностей
/status - Статус бирж и доступных монет
/best_staking - Показать лучшие стейкинги
/hot_loans - В монете намечается суета (дорогие займы)
/help - Помощь по использованию бота

⚡ <b>Поддерживаемые биржи:</b>
• Bybit
• OKX  
• Binance

Бот анализирует разницу между ставками займов и стейкинга для поиска прибыльных возможностей.
        """
        await update.message.reply_html(welcome_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """
📖 <b>ПОМОЩЬ ПО ИСПОЛЬЗОВАНИЮ БОТА</b>

<b>Команды:</b>
/start - Начало работы с ботом
/analyze - Запустить полный анализ арбитражных возможностей
/status - Показать статус подключения к биржам
/best_staking - Показать лучшие предложения по стейкингу
/hot_loans - Монеты с высокими ставками займов
/help - Эта справка

<b>Как это работает:</b>
1. Бот собирает данные о ставках займов с бирж
2. Собирает данные о доходности стейкинга
3. Находит монеты, доступные для обеих операций
4. Рассчитывает чистую прибыль (стейкинг - займ)
5. Показывает лучшие возможности

<b>Типы арбитража:</b>
• 🎯 Внутрибиржевой - займ и стейкинг на одной бирже
• 🌐 Межбиржевой - займ на одной, стейкинг на другой бирже

<b>Метки прибыльности:</b>
👑 ОТЛИЧНАЯ (>20%) | 🟢 ХОРОШАЯ (>15%) | 🟡 НИЗКАЯ (>10%) | 🔵 БЕЗУБЫТОК (>2%) | 🔴 УБЫТОЧНАЯ

<b>Поддерживаемые биржи:</b>
• Bybit, OKX, Binance
        """
        await update.message.reply_html(help_text)
    
    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /analyze"""
        try:
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            
            # Отправляем сообщение о начале анализа
            status_message = await update.message.reply_text(
                "🔄 <b>Запускаю анализ арбитражных возможностей...</b>\n"
                "⏳ Это займет 1-2 минуты...",
                parse_mode='HTML'
            )
            
            # Запускаем анализ в отдельном потоке с обработкой ошибок
            asyncio.create_task(
                self.run_analysis_async_safe(chat_id, status_message.message_id)
            )
            
        except Exception as e:
            logger.error(f"Ошибка в analyze_command: {e}")
            await update.message.reply_text(
                f"❌ <b>Ошибка при запуске анализа:</b>\n<code>{str(e)}</code>",
                parse_mode='HTML'
            )
    
    async def run_analysis_async_safe(self, chat_id: int, message_id: int):
        """Безопасный асинхронный запуск анализа с обработкой всех исключений"""
        try:
            await self.run_analysis_async(chat_id, message_id)
        except Exception as e:
            logger.error(f"Критическая ошибка в run_analysis_async_safe: {e}")
            await self.send_error(chat_id, message_id, f"❌ <b>Критическая ошибка:</b>\n<code>{str(e)}</code>")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /status - показывает статус бирж"""
        try:
            if not self.arbitrage_bot:
                self.arbitrage_bot = ArbitrageBot()
            
            status_text = "📊 <b>СТАТУС БИРЖ</b>\n\n"
            
            # Проверяем доступность каждой биржи
            for exchange in self.arbitrage_bot.exchanges:
                status_text += f"<b>{exchange.name}</b>\n"
                
                try:
                    # Получаем доступные монеты
                    loan_coins = exchange.get_loan_rates()
                    staking_coins = exchange.get_staking_rates()
                    
                    status_text += f"✅ Займы: {len(loan_coins)} монет\n"
                    status_text += f"✅ Стейкинг: {len(staking_coins)} монет\n"
                    status_text += f"📈 Общие монеты: {len(set(loan_coins.keys()) & set(staking_coins.keys()))}\n"
                    
                except Exception as e:
                    status_text += f"❌ Ошибка: {str(e)}\n"
                
                status_text += "\n"
            
            await update.message.reply_html(status_text)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка при получении статуса: {str(e)}")
    
    async def best_staking_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать лучшие стейкинги"""
        try:
            if not self.arbitrage_bot:
                self.arbitrage_bot = ArbitrageBot()
            
            await update.message.reply_text("🔄 <b>Собираю данные о лучших стейкингах...</b>", parse_mode='HTML')
            
            all_data = self.arbitrage_bot.collect_all_data()
            best_staking = self.arbitrage_bot.find_best_staking_opportunities(all_data)
            
            if best_staking:
                message = self._format_best_staking_message(best_staking)
            else:
                message = "❌ <b>Не найдено хороших стейкингов</b>"
            
            await update.message.reply_html(message)
            
        except Exception as e:
            error_msg = f"❌ <b>Ошибка при поиске стейкингов:</b>\n<code>{str(e)}</code>"
            await update.message.reply_html(error_msg)
    
    async def hot_loans_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать дорогие займы (суета в монете)"""
        try:
            if not self.arbitrage_bot:
                self.arbitrage_bot = ArbitrageBot()
            
            await update.message.reply_text("🔄 <b>Ищу монеты с дорогими займами...</b>", parse_mode='HTML')
            
            all_data = self.arbitrage_bot.collect_all_data()
            hot_loans = self.arbitrage_bot.find_hot_loan_opportunities(all_data)
            
            if hot_loans:
                message = self._format_hot_loans_message(hot_loans)
            else:
                message = "❌ <b>Не найдено монет с дорогими займами</b>"
            
            await update.message.reply_html(message)
            
        except Exception as e:
            error_msg = f"❌ <b>Ошибка при поиске займов:</b>\n<code>{str(e)}</code>"
            await update.message.reply_html(error_msg)
    
    async def debug_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для отладки"""
        await update.message.reply_text(
            f"🤖 Бот работает!\n"
            f"Чат ID: {update.effective_chat.id}\n"
            f"Пользователь: {update.effective_user.first_name}\n"
            f"Bot enabled: {TELEGRAM_CONFIG.get('bot_enabled', True)}"
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик обычных сообщений"""
        await update.message.reply_text(
            "🤖 Используйте команды для работы с ботом:\n"
            "/start - начать работу\n"
            "/analyze - запустить анализ\n"
            "/best_staking - лучшие стейкинги\n"
            "/hot_loans - дорогие займы\n"
            "/status - статус бирж\n" 
            "/help - помощь"
        )
    
    def _format_best_staking_message(self, staking_opportunities: List[Dict]) -> str:
        """Форматировать сообщение о лучших стейкингах"""
        message = "🏆 <b>ЛУЧШИЕ СТЕЙКИНГИ НА ВСЕХ БИРЖАХ</b>\n\n"
        
        for i, opp in enumerate(staking_opportunities[:15], 1):
            message += f"<b>{i}. {opp['coin']}</b>\n"
            message += f"   📈 APY: <code>{opp['apy']:.2f}%</code>\n"
            message += f"   🏦 Биржа: <b>{opp['exchange']}</b>\n"
            message += f"   💰 Мин. сумма: <code>{opp['min_amount']}</code>\n\n"
        
        return message
    
    def _format_hot_loans_message(self, loan_opportunities: List[Dict]) -> str:
        """Форматировать сообщение о дорогих займах"""
        message = "🔥 <b>В МОНЕТЕ НАМЕКАЕТСЯ СУЕТА (ДОРОГИЕ ЗАЙМЫ)</b>\n\n"
        
        for i, opp in enumerate(loan_opportunities[:15], 1):
            message += f"<b>{i}. {opp['coin']}</b>\n"
            message += f"   💸 Ставка: <code>{opp['rate']:.2f}%</code>\n"
            message += f"   🏦 Биржа: <b>{opp['exchange']}</b>\n"
            message += f"   📊 Причина: {opp['reason']}\n\n"
        
        return message
    
    async def run_analysis_async(self, chat_id: int, message_id: int):
        """Асинхронный запуск анализа"""
        try:
            print(f"🔍 Начинаем анализ для чата {chat_id}")
            
            # Создаем бота анализа
            arbitrage_bot = ArbitrageBot()
            
            # Запускаем анализ
            print("📊 Собираем данные с бирж...")
            all_data = arbitrage_bot.collect_all_data()
            
            print("🎯 Ищем внутрибиржевые возможности...")
            intra_opportunities = arbitrage_bot.find_intra_exchange_opportunities(all_data)
            
            print("🌐 Ищем межбиржевые возможности...")
            cross_opportunities = arbitrage_bot.find_cross_exchange_opportunities(all_data)
            
            print("📈 Создаем сводную таблицу...")
            summary_opportunities = arbitrage_bot.create_summary_table(intra_opportunities, cross_opportunities)
            
            # Формируем отчет
            print("📨 Формируем отчет...")
            report = self.format_analysis_report(intra_opportunities, cross_opportunities, summary_opportunities)
            
            # Отправляем результаты
            await self.send_analysis_results(chat_id, message_id, report)
            
        except Exception as e:
            print(f"❌ Ошибка в run_analysis_async: {e}")
            import traceback
            traceback.print_exc()
            error_message = f"❌ <b>Ошибка при анализе:</b>\n<code>{str(e)}</code>"
            await self.send_error(chat_id, message_id, error_message)
    
    def format_analysis_report(self, intra_opportunities: List[Dict], cross_opportunities: List[Dict], summary_opportunities: List[Dict]) -> Dict[str, str]:
        """Форматирует результаты анализа для отправки"""
        report = {}
        
        # Внутрибиржевые возможности
        if intra_opportunities:
            report['intra'] = self._format_opportunities_message(
                intra_opportunities[:10],
                "🎯 ВНУТРИБИРЖЕВЫЕ АРБИТРАЖНЫЕ ВОЗМОЖНОСТИ"
            )
        else:
            report['intra'] = "❌ <b>ВНУТРИБИРЖЕВЫЕ ВОЗМОЖНОСТИ</b>\n\nНе найдено прибыльных возможностей"
        
        # Межбиржевые возможности
        if cross_opportunities:
            report['cross'] = self._format_opportunities_message(
                cross_opportunities[:10],
                "🌐 МЕЖБИРЖЕВЫЕ АРБИТРАЖНЫЕ ВОЗМОЖНОСТИ"
            )
        else:
            report['cross'] = "❌ <b>МЕЖБИРЖЕВЫЕ ВОЗМОЖНОСТИ</b>\n\nНе найдено прибыльных возможностей"
        
        # Сводная статистика
        report['summary'] = self._format_summary(intra_opportunities, cross_opportunities, summary_opportunities)
        
        return report
    
    def _format_opportunities_message(self, opportunities: List[Dict], title: str) -> str:
        """Форматирует список возможностей в сообщение"""
        if not opportunities:
            return f"❌ <b>{title}</b>\n\nНе найдено прибыльных возможностей"
        
        message = f"<b>{title} (ТОП-{len(opportunities)})</b>\n\n"
        
        for i, opp in enumerate(opportunities, 1):
            # Эмодзи для прибыльности
            if opp["net_profit"] > 20:
                profit_emoji = "👑"
            elif opp["net_profit"] > 15:
                profit_emoji = "🟢"
            elif opp["net_profit"] > 10:
                profit_emoji = "🟡"
            elif opp["net_profit"] > 2:
                profit_emoji = "🔵"
            else:
                profit_emoji = "🔴"
            
            # Определяем тип операции
            if opp.get('type') == 'intra' or opp['borrow_exchange'] == opp['staking_exchange']:
                op_type = "📊 ВНУТРИ"
            else:
                op_type = "🌐 МЕЖБИРЖА"
                
            message += f"<b>{i}. {opp['coin']}</b> {profit_emoji} {op_type}\n"
            message += f"   💰 Займ: <code>{opp['borrow_rate']:.4f}%</code> на <b>{opp['borrow_exchange']}</b>\n"
            message += f"   📈 Стейкинг: <code>{opp['staking_apy']:.2f}%</code> на <b>{opp['staking_exchange']}</b>\n"
            message += f"   🎯 Чистая прибыль: <code>{opp['net_profit']:.2f}%</code> - {opp['profitability']}\n\n"
        
        return message
    
    def _format_summary(self, intra_opportunities: List[Dict], cross_opportunities: List[Dict], summary_opportunities: List[Dict]) -> str:
        """Форматирует сводную статистику"""
        total_intra = len(intra_opportunities)
        total_cross = len(cross_opportunities)
        total_all = len(summary_opportunities)
        
        if summary_opportunities:
            best_profit = summary_opportunities[0]["net_profit"]
            avg_profit = sum(opp["net_profit"] for opp in summary_opportunities[:20]) / min(20, len(summary_opportunities))
        else:
            best_profit = 0
            avg_profit = 0
        
        summary = f"""
📊 <b>СВОДНАЯ СТАТИСТИКА АНАЛИЗА</b>

🎯 Внутрибиржевых возможностей: <b>{total_intra}</b>
🌐 Межбиржевых возможностей: <b>{total_cross}</b>
📈 Всего возможностей: <b>{total_all}</b>

🏆 Лучшая прибыль: <b>{best_profit:.2f}%</b>
📊 Средняя прибыль (топ-20): <b>{avg_profit:.2f}%</b>

⏰ Анализ завершен: <b>{len(summary_opportunities) > 0}</b>
        """
        
        return summary
    
    async def send_analysis_results(self, chat_id: int, message_id: int, report: Dict[str, str]):
        """Отправляет результаты анализа"""
        try:
            print(f"📨 Отправляем результаты в чат {chat_id}")
            
            # Удаляем сообщение "анализ запущен"
            try:
                await self.application.bot.delete_message(chat_id, message_id)
                print("✅ Сообщение о запуске удалено")
            except Exception as e:
                print(f"⚠️ Не удалось удалить сообщение: {e}")
            
            # Отправляем внутрибиржевые возможности
            if 'intra' in report:
                await self.application.bot.send_message(
                    chat_id=chat_id,
                    text=report['intra'],
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
                await asyncio.sleep(0.5)  # Небольшая задержка между сообщениями
            
            # Отправляем межбиржевые возможности
            if 'cross' in report:
                await self.application.bot.send_message(
                    chat_id=chat_id,
                    text=report['cross'],
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
                await asyncio.sleep(0.5)  # Небольшая задержка между сообщениями
            
            # Отправляем сводную статистику
            if 'summary' in report:
                await self.application.bot.send_message(
                    chat_id=chat_id,
                    text=report['summary'],
                    parse_mode='HTML'
                )
                
            print("✅ Все результаты отправлены")
            
        except Exception as e:
            print(f"❌ Ошибка при отправке результатов: {e}")
            import traceback
            traceback.print_exc()
            
            # Пытаемся отправить сообщение об ошибке
            try:
                await self.application.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ <b>Ошибка при отправке результатов:</b>\n<code>{str(e)}</code>",
                    parse_mode='HTML'
                )
            except Exception as send_error:
                print(f"❌ Не удалось отправить сообщение об ошибке: {send_error}")
    
    async def send_error(self, chat_id: int, message_id: int, error_message: str):
        """Отправляет сообщение об ошибке"""
        try:
            # Пытаемся отредактировать существующее сообщение
            await self.application.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=error_message,
                parse_mode='HTML'
            )
        except Exception as e:
            # Если не удалось отредактировать, отправляем новое сообщение
            logger.error(f"Ошибка при редактировании сообщения: {e}")
            try:
                await self.application.bot.send_message(
                    chat_id=chat_id,
                    text=error_message,
                    parse_mode='HTML'
                )
            except Exception as send_error:
                logger.error(f"Ошибка при отправке ошибки: {send_error}")
    
    def run(self):
        """Запускает бота"""
        print("🤖 Запуск Telegram бота...")
        try:
            self.application.run_polling()
        except Exception as e:
            logger.error(f"Критическая ошибка бота: {e}")
            print(f"❌ Бот упал с ошибкой: {e}")

def main():
    """Главная функция для запуска бота"""
    try:
        token = TELEGRAM_CONFIG["token"]
        
        if not token:
            print("❌ Токен бота не найден в конфигурации")
            return
        
        # Создаем и запускаем бота
        bot = ArbitrageTelegramBot(token)
        bot.run()
    except Exception as e:
        print(f"❌ Критическая ошибка при запуске бота: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()