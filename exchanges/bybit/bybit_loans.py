# exchanges/bybit_loans.py
import requests
import urllib3
from typing import Dict

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BybitLoans:
    """Класс для работы с займами Bybit"""
    
    def __init__(self, base_url: str, config: Dict):
        self.base_url = base_url
        self.config = config
    
    def get_loan_rates(self) -> Dict[str, Dict]:
        """Получить ставки по займам с Bybit"""
        print("🔍 Получение данных о займах с Bybit...")
        
        endpoint = "/v5/crypto-loan-common/loanable-data"
        url = f"{self.base_url}{endpoint}"
        params = {"vipLevel": "VIP0"}
        
        try:
            response = self._make_request(url, params)
            
            if response and response.get("retCode") == 0:
                return self._normalize_loan_data(response)
            else:
                print(f"❌ Bybit API error: {response.get('retMsg') if response else 'No response'}")
                return {}
        except Exception as e:
            print(f"❌ Bybit loan data error: {e}")
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
    
    def _normalize_loan_data(self, raw_data: Dict) -> Dict[str, Dict]:
        """Нормализовать данные о займах"""
        normalized = {}
        
        for coin in raw_data["result"].get("list", []):
            currency = coin.get("currency", "").upper()
            flexible_rate = coin.get("flexibleAnnualizedInterestRate")
            min_loan = coin.get("minLoanAmount", 0)
            max_loan = coin.get("maxLoanAmount", 0)
            
            if currency and flexible_rate and flexible_rate != "":
                try:
                    normalized[currency] = {
                        'rate': float(flexible_rate),
                        'min_amount': float(min_loan) if min_loan else 0,
                        'max_amount': float(max_loan) if max_loan else 0
                    }
                except (ValueError, TypeError):
                    continue
        
        print(f"📊 Bybit: нормализовано {len(normalized)} ставок по займам")
        return normalized