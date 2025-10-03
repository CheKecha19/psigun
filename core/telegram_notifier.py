# core/telegram_notifier.py
import requests
from typing import List, Dict
from utils.data_normalizer import DataNormalizer  # Исправлен импорт

class TelegramNotifier:
    def __init__(self, config: Dict):
        self.token = config["token"]
        self.chat_id = config["chat_id"]
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.enabled = config.get("enabled", True)
    
    def send_message(self, text: str, silent: bool = False) -> bool:
        """Отправить сообщение в Telegram"""
        if not self.enabled:
            return True
            
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_notification": silent
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"❌ Telegram error: {e}")
            return False
    
    def send_opportunities(self, opportunities: List[Dict], title: str):
        """Отправить список возможностей в Telegram с новыми индикаторами"""
        if not opportunities:
            message = f"❌ <b>{title}</b>\n\nНе найдено прибыльных возможностей"
            self.send_message(message)
            return
        
        message = f"<b>{title} (ТОП-{len(opportunities)})</b>\n\n"
        
        for i, opp in enumerate(opportunities, 1):
            # Используем новые индикаторы прибыльности
            profit_label = DataNormalizer.get_profitability_label(opp["net_profit"])
            
            # Определяем тип операции
            if opp.get('type') == 'intra' or opp['borrow_exchange'] == opp['staking_exchange']:
                op_type = "📊 ВНУТРИ"
            else:
                op_type = "🌐 МЕЖБИРЖА"
                
            message += f"<b>{i}. {opp['coin']}</b> {profit_label} {op_type}\n"
            message += f"   💰 Займ: <code>{opp['borrow_rate']:.4f}%</code> на <b>{opp['borrow_exchange']}</b>\n"
            message += f"   📈 Стейкинг: <code>{opp['staking_apy']:.2f}%</code> на <b>{opp['staking_exchange']}</b>\n"
            message += f"   🎯 Чистая прибыль: <code>{opp['net_profit']:.2f}%</code>\n\n"
        
        # Статистика
        total_opps = len(opportunities)
        best_profit = opportunities[0]["net_profit"]
        avg_profit = sum(opp["net_profit"] for opp in opportunities) / len(opportunities)
        
        message += "<b>📊 СТАТИСТИКА:</b>\n"
        message += f"   • Всего возможностей: <b>{total_opps}</b>\n"
        message += f"   • Лучшая прибыль: <b>{best_profit:.2f}%</b>\n"
        message += f"   • Средняя прибыль: <b>{avg_profit:.2f}%</b>"
        
        self.send_message(message)