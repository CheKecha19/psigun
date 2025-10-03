# exchanges/bybit_onchain_savings.py
import requests
import urllib3
from typing import Dict

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BybitOnchainSavings:
    """Класс для работы с ончейн сбережениями Bybit"""
    
    def __init__(self, base_url: str, config: Dict):
        self.base_url = base_url
        self.config = config
    
    def get_rates(self) -> Dict[str, Dict]:
        """Получить данные о OnChain продуктах"""
        endpoint = "/v5/earn/product"
        url = f"{self.base_url}{endpoint}"
        params = {"category": "OnChain"}
        
        try:
            response = self._make_request(url, params)
            
            if response and response.get("retCode") == 0:
                rates = self._normalize_onchain_data(response)
                print(f"📊 Bybit: найдено {len(rates)} ончейн продуктов")
                return rates
            else:
                print(f"❌ Bybit OnChain API error: {response.get('retMsg') if response else 'No response'}")
                return {}
        except Exception as e:
            print(f"❌ Bybit OnChain error: {e}")
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
    
    def _normalize_onchain_data(self, raw_data: Dict) -> Dict[str, Dict]:
        """Нормализовать данные о OnChain продуктах"""
        normalized = {}
        
        products = raw_data["result"].get("list", [])
        print(f"📊 Bybit OnChain: получено {len(products)} продуктов")
        
        for product in products:
            coin = product.get("coin", "").upper()
            estimate_apr = product.get("estimateApr")
            min_stake = product.get("minStakeAmount", 0)
            max_stake = product.get("maxStakeAmount", 0)
            
            if coin and estimate_apr is not None:
                try:
                    apr_str = str(estimate_apr).replace('%', '')
                    rate = float(apr_str)
                    
                    # Если монета уже есть, берем максимальную ставку
                    if coin in normalized:
                        if rate > normalized[coin]['apy']:
                            normalized[coin] = {
                                'apy': rate,
                                'min_amount': float(min_stake) if min_stake else 0,
                                'max_amount': float(max_stake) if max_stake else 0
                            }
                    else:
                        normalized[coin] = {
                            'apy': rate,
                            'min_amount': float(min_stake) if min_stake else 0,
                            'max_amount': float(max_stake) if max_stake else 0
                        }
                        
                except (ValueError, TypeError) as e:
                    print(f"   ❌ Ошибка конвертации для {coin}: {estimate_apr} - {e}")
                    continue
        
        return normalized