import requests
import urllib3
import hashlib
import hmac
import base64
import json
from typing import Dict
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OkxFlexibleSavings:
    """Класс для работы с гибкими сбережениями OKX"""
    
    def __init__(self, base_url: str, config: Dict):
        self.base_url = base_url
        self.config = config
        self.api_key = config.get("api_key", "")
        self.api_secret = config.get("api_secret", "")
        self.passphrase = config.get("passphrase", "")
    
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
    
    def get_rates(self) -> Dict[str, Dict]:
        """Получить данные о гибких сбережениях"""
        print("🔍 Получение данных о гибких сбережениях OKX...")
        
        endpoint = "/api/v5/finance/savings/products"
        params = {"productType": "simple", "protocolType": "flexible"}
        
        response = self._make_signed_request("GET", endpoint, params)
        if not response or response.get("code") != "0":
            print("❌ Ошибка получения гибких сбережений OKX")
            return {}
        
        return self._normalize_flexible_data(response)
    
    def _normalize_flexible_data(self, raw_data: Dict) -> Dict[str, Dict]:
        """Нормализовать данные о гибких сбережениях"""
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
                        print(f"   🏦 {currency}: {rate:.2f}% APY (гибкий)")
                    except (ValueError, TypeError):
                        continue
            
            print(f"📊 OKX: нормализовано {len(normalized)} гибких сбережений")
            return normalized
            
        except Exception as e:
            print(f"❌ Ошибка нормализации гибких сбережений OKX: {e}")
            return {}