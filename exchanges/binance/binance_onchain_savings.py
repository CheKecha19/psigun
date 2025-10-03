import requests
import urllib3
import hmac
import hashlib
import time
from typing import Dict
from urllib.parse import urlencode

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BinanceOnchainSavings:
    """Класс для работы с ончейн сбережениями Binance"""
    
    def __init__(self, base_url: str, config: Dict):
        self.base_url = base_url
        self.config = config
        self.api_key = config.get("api_key", "")
        self.api_secret = config.get("api_secret", "")
    
    def get_rates(self) -> Dict[str, Dict]:
        """Получить ставки по ончейн сбережениям на Binance"""
        print("🔍 Получение данных о ончейн сбережениях с Binance...")
        
        # Для Binance пока используем те же данные, что и для гибких сбережений
        # В будущем можно добавить специфичные ончейн продукты
        return {}
    
    def _get_alternative_staking_rates(self) -> Dict[str, Dict]:
        """Альтернативный метод получения ставок стейкинга"""
        print("🔍 Попытка альтернативного получения данных о стейкинге...")
        
        # Эндпоинт для позиций стейкинга (требует signed запрос)
        endpoint = "/sapi/v1/staking/position"
        params = {'product': 'STAKING'}
        
        response = self._make_request(endpoint, params, signed=True)
        
        if response and isinstance(response, list):
            return self._normalize_staking_positions(response)
        else:
            print("⚠️ Используем примерные данные о стейкинге")
            return self._get_sample_staking_rates()
    
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
    
    def _sign_request(self, params: Dict) -> str:
        """Создать подпись для запроса"""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _normalize_staking_positions(self, positions: list) -> Dict[str, Dict]:
        """Нормализовать данные из позиций стейкинга"""
        normalized = {}
        
        try:
            for position in positions:
                asset = position.get('asset', '').upper()
                apr = position.get('apr')
                
                if asset and apr:
                    try:
                        apy = float(apr)
                        
                        normalized[asset] = {
                            'apy': apy,
                            'min_amount': 0,
                            'max_amount': 0
                        }
                        print(f"   🏦 {asset}: {apy:.2f}% APY (из позиций)")
                    except (ValueError, TypeError):
                        continue
            
            return normalized
            
        except Exception as e:
            print(f"❌ Ошибка нормализации позиций стейкинга: {e}")
            return {}
    
    def _get_sample_staking_rates(self) -> Dict[str, Dict]:
        """Примерные ставки стейкинга для основных монет"""
        sample_rates = {
            'ADA': {'apy': 4.5, 'min_amount': 0, 'max_amount': 0},
            'DOT': {'apy': 12.0, 'min_amount': 0, 'max_amount': 0},
            'ATOM': {'apy': 15.0, 'min_amount': 0, 'max_amount': 0},
        }
        
        print("📊 Binance: используются примерные ставки ончейн стейкинга")
        return sample_rates