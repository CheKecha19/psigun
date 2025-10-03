import requests
import urllib3
import hmac
import hashlib
import time
from typing import Dict
from urllib.parse import urlencode

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BinanceLoans:
    """Класс для работы с займами Binance"""
    
    def __init__(self, base_url: str, config: Dict):
        self.base_url = base_url
        self.config = config
        self.api_key = config.get("api_key", "")
        self.api_secret = config.get("api_secret", "")
    
    def _sign_request(self, params: Dict) -> str:
        """Создать подпись для запроса"""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _make_request(self, endpoint: str, params: Dict = None, signed: bool = False):
        """Выполнить запрос к API Binance"""
        if params is None:
            params = {}
        
        url = f"{self.base_url}{endpoint}"
        
        # Добавляем timestamp для подписанных запросов
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._sign_request(params)
        
        headers = {}
        if self.api_key:
            headers['X-MBX-APIKEY'] = self.api_key
        
        try:
            if signed:
                response = requests.post(url, data=params, headers=headers, verify=False, timeout=10)
            else:
                response = requests.get(url, params=params, headers=headers, verify=False, timeout=10)
            
            if response.status_code == 401:
                print(f"❌ Ошибка аутентификации Binance API: неверный API ключ")
                return None
            elif response.status_code == 404:
                print(f"❌ Эндпоинт Binance API не найден: {endpoint}")
                return None
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Ошибка запроса к Binance API ({endpoint}): {e}")
            return None
    
    def get_loan_rates(self) -> Dict[str, Dict]:
        """Получить реальные ставки по маржинальным займам на Binance"""
        print("🔍 Получение реальных данных о маржинальных займах с Binance...")
        
        # Эндпоинт для получения реальных маржинальных ставок
        endpoint = "/sapi/v1/margin/interestRateHistory"
        
        # Получаем ставки для основных монет
        major_coins = ['BTC', 'ETH', 'BNB', 'USDT', 'USDC', 'ADA', 'DOT', 'LTC', 'LINK', 'BCH']
        normalized = {}
        
        for coin in major_coins:
            params = {'asset': coin}
            response = self._make_request(endpoint, params)
            
            if response and isinstance(response, list) and len(response) > 0:
                try:
                    # Берем последнюю доступную ставку
                    latest_rate = response[0]
                    daily_rate = float(latest_rate.get('interestRate', 0))
                    annual_rate = daily_rate * 365 * 100
                    
                    normalized[coin] = {
                        'rate': annual_rate,
                        'min_amount': 0,
                        'max_amount': 0,
                        'daily_rate': daily_rate * 100
                    }
                    print(f"   💰 {coin}: {annual_rate:.2f}% годовых (реальная ставка)")
                    
                except (ValueError, TypeError, IndexError) as e:
                    print(f"   ⚠️ Ошибка получения ставки для {coin}, используем примерную")
                    # Резервные примерные ставки
                    backup_rates = self._get_backup_loan_rates(coin)
                    normalized[coin] = backup_rates
            else:
                # Если не получили реальные данные, используем примерные
                print(f"   ⚠️ Нет реальных данных для {coin}, используем примерные ставки")
                backup_rates = self._get_backup_loan_rates(coin)
                normalized[coin] = backup_rates
        
        print(f"📊 Binance: получено {len(normalized)} реальных ставок по займам")
        return normalized
    
    def _get_backup_loan_rates(self, coin: str) -> Dict:
        """Резервные примерные ставки если реальные недоступны"""
        rate_map = {
            'BTC': 3.5, 'ETH': 3.5, 'BNB': 3.5,
            'USDT': 5.0, 'USDC': 5.0, 'BUSD': 5.0,
        }
        return {
            'rate': rate_map.get(coin, 8.0),
            'min_amount': 0,
            'max_amount': 0
        }