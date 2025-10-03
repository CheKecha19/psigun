# exchanges/okx/okx_exchange.py
import requests
import urllib3
import hashlib
import hmac
import base64
import json
from typing import Dict, List, Optional
from datetime import datetime
from ..base_exchange import BaseExchange  # Исправлен импорт
from .okx_loans import OkxLoans

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OkxExchange(BaseExchange):
    """Реализация API для OKX Exchange с использованием официальных эндпоинтов"""
    
    def __init__(self, config: Dict):
        super().__init__("OKX", config)
        self.base_url = "https://www.okx.com"
        self.api_key = config.get("api_key", "")
        self.api_secret = config.get("api_secret", "")
        self.passphrase = config.get("passphrase", "")
        
        # Инициализация модулей
        self.loans_module = OkxLoans(self.base_url, config)
        print("✅ OKX exchange initialized with modular structure")
    
    def get_loan_rates(self) -> Dict[str, Dict]:
        """Получить ставки по гибким займам с OKX"""
        return self.loans_module.get_loan_rates()
    
    def get_staking_rates(self) -> Dict[str, Dict]:
        """Получить ставки по стейкингу с OKX"""
        print("🔍 Получение данных о стейкинге с OKX...")
        
        endpoints = [
            "/api/v5/finance/savings/products",
            "/api/v5/finance/staking-defi/offers",
            "/api/v5/finance/savings/balance"
        ]
        
        for endpoint in endpoints:
            response = self._make_signed_request("GET", endpoint)
            if response and response.get("code") == "0":
                print(f"✅ OKX staking data received from {endpoint}")
                return self._normalize_staking_data(response)
        
        print("❌ Все эндпоинты стейкинга OKX вернули ошибку")
        return {}
    
    def _make_signed_request(self, method: str, endpoint: str, params: Dict = None):
        """Выполняет подписанный запрос к API OKX"""
        if params is None:
            params = {}
        
        timestamp = datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'
        
        # Подготовка тела запроса
        body = ""
        if method == "GET" and params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            request_path = f"{endpoint}?{query_string}"
        else:
            request_path = endpoint
            if method in ["POST", "PUT"] and params:
                body = json.dumps(params, separators=(',', ':'))
        
        # Создание подписи
        message = timestamp + method.upper() + request_path + body
        signature = base64.b64encode(
            hmac.new(
                self.api_secret.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode()
        
        headers = {
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": signature,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}{request_path}" if method == "GET" and params else f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, verify=False, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, data=body, verify=False, timeout=10)
            else:
                return None
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Ошибка запроса к OKX API ({endpoint}): {e}")
            return None
    
    def _normalize_staking_data(self, raw_data: Dict) -> Dict[str, Dict]:
        """Нормализовать данные о стейкинге"""
        normalized = {}
        
        try:
            data_list = raw_data.get("data", [])
            
            for item in data_list:
                currency = item.get("ccy", "").upper()
                apy = item.get("apy") or item.get("earningRate") or item.get("rate")
                
                if currency and apy is not None:
                    try:
                        apy_str = str(apy).replace('%', '')
                        rate = float(apy_str)
                        
                        normalized[currency] = {
                            'apy': rate,
                            'min_amount': float(item.get("minAmt", 0)),
                            'max_amount': float(item.get("maxAmt", 0))
                        }
                    except (ValueError, TypeError):
                        continue
            
            print(f"📊 OKX: нормализовано {len(normalized)} ставок по стейкингу")
            return normalized
            
        except Exception as e:
            print(f"❌ Ошибка нормализации данных о стейкинге OKX: {e}")
            return {}
    
    def get_available_coins(self) -> List[str]:
        """Получить список доступных монет на OKX"""
        loan_rates = self.get_loan_rates()
        staking_rates = self.get_staking_rates()
        return list(set(loan_rates.keys()) | set(staking_rates.keys()))
    
    def test_api_connection(self):
        """Тестирование подключения к OKX API"""
        print("🧪 Тестирование подключения к OKX API...")
        
        # Простой запрос для проверки баланса
        response = self._make_signed_request("GET", "/api/v5/account/balance")
        if response and response.get("code") == "0":
            print("✅ OKX API подключение успешно!")
            data = response.get("data", [])
            if data:
                print(f"✅ Баланс получен, {len(data)} счетов")
            return True
        else:
            error_msg = response.get('msg', 'Unknown error') if response else 'No response'
            print(f"❌ Ошибка подключения к OKX API: {error_msg}")
            return False