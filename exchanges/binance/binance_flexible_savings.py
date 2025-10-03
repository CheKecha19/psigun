import requests
import urllib3
import hmac
import hashlib
import time
from typing import Dict
from urllib.parse import urlencode

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BinanceFlexibleSavings:
    """Класс для работы с гибкими сбережениями Binance"""
    
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
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Ошибка запроса к Binance API ({endpoint}): {e}")
            return None
    
    def get_rates(self) -> Dict[str, Dict]:
        """Получить ставки по гибким сбережениям на Binance"""
        print("🔍 Получение данных о гибких сбережениях с Binance...")
        
        # Основной эндпоинт для продуктов стейкинга
        endpoint = "/sapi/v1/staking/productList"
        params = {'product': 'STAKING'}
        
        response = self._make_request(endpoint, params, signed=True)
        
        if not response:
            print("❌ Не удалось получить данные о стейкинге с основного эндпоинта")
            return self._get_sample_staking_rates()
        
        return self._normalize_staking_data(response)
    
    def _normalize_staking_data(self, raw_data: list) -> Dict[str, Dict]:
        """Нормализовать данные о стейкинге"""
        normalized = {}
        
        try:
            print(f"📊 Binance staking data: получено {len(raw_data)} продуктов")
            
            for product in raw_data:
                asset = product.get('asset', '').upper()
                apr = product.get('apr')
                
                if asset and apr:
                    try:
                        apy = float(apr)
                        
                        normalized[asset] = {
                            'apy': apy,
                            'min_amount': float(product.get('minPurchaseAmount', 0)),
                            'max_amount': 0
                        }
                        print(f"   🏦 {asset}: {apy:.2f}% APY")
                    except (ValueError, TypeError) as e:
                        print(f"   ❌ Ошибка конвертации для {asset}: {apr} - {e}")
                        continue
            
            print(f"📊 Binance: нормализовано {len(normalized)} ставок по стейкингу")
            return normalized
            
        except Exception as e:
            print(f"❌ Ошибка нормализации данных о стейкинге Binance: {e}")
            return self._get_sample_staking_rates()
    
    def _get_sample_staking_rates(self) -> Dict[str, Dict]:
        """Примерные ставки стейкинга для основных монет"""
        sample_rates = {
            'ADA': {'apy': 4.5, 'min_amount': 0, 'max_amount': 0},
            'DOT': {'apy': 12.0, 'min_amount': 0, 'max_amount': 0},
            'ATOM': {'apy': 15.0, 'min_amount': 0, 'max_amount': 0},
            'SOL': {'apy': 7.5, 'min_amount': 0, 'max_amount': 0},
            'ETH': {'apy': 4.0, 'min_amount': 0, 'max_amount': 0},
            'MATIC': {'apy': 3.0, 'min_amount': 0, 'max_amount': 0},
            'BNB': {'apy': 2.0, 'min_amount': 0, 'max_amount': 0},
        }
        
        print("📊 Binance: используются примерные ставки стейкинга")
        for coin, data in sample_rates.items():
            print(f"   🏦 {coin}: {data['apy']:.2f}% APY (примерная)")
        
        return sample_rates