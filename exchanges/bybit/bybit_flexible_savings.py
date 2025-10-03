# exchanges/bybit_flexible_savings.py
import requests
import urllib3
from typing import Dict

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BybitFlexibleSavings:
    """Класс для работы с гибкими сбережениями Bybit"""
    
    def __init__(self, base_url: str, config: Dict):
        self.base_url = base_url
        self.config = config
    
    def get_rates(self) -> Dict[str, Dict]:
        """Получить данные о гибких сбережениях"""
        endpoint = "/v5/earn/product"
        url = f"{self.base_url}{endpoint}"
        params = {"category": "FlexibleSaving"}
        
        try:
            response = self._make_request(url, params)
            
            if response and response.get("retCode") == 0:
                rates = self._normalize_flexible_savings_data(response)
                print(f"📊 Bybit: найдено {len(rates)} гибких сбережений")
                return rates
            else:
                print(f"❌ Bybit flexible savings API error: {response.get('retMsg') if response else 'No response'}")
                return {}
        except Exception as e:
            print(f"❌ Bybit flexible savings error: {e}")
            return {}
    
    def _make_request(self, url: str, params: Dict = None):
        """Вспомогательный метод для выполнения запросов"""
        try:
            response = requests.get(url, params=params, verify=False, timeout=self.config.get("timeout", 10))
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Bybit request error: {e}")
            return None
    
    def _normalize_flexible_savings_data(self, raw_data: Dict) -> Dict[str, Dict]:
        """Нормализовать данные о гибких сбережениях"""
        normalized = {}
        
        for product in raw_data["result"].get("list", []):
            if product.get("status") == "Available":
                coin = product.get("coin", "").upper()
                estimate_apr = product.get("estimateApr")
                min_stake = product.get("minStakeAmount", 0)
                max_stake = product.get("maxStakeAmount", 0)
                
                if coin and estimate_apr and estimate_apr != "":
                    try:
                        apr_str = str(estimate_apr).replace('%', '')
                        normalized[coin] = {
                            'apy': float(apr_str),
                            'min_amount': float(min_stake) if min_stake else 0,
                            'max_amount': float(max_stake) if max_stake else 0
                        }
                    except (ValueError, TypeError):
                        continue
        
        return normalized