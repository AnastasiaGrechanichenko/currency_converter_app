import httpx
import logging

import requests

from app.database import settings

logger = logging.getLogger(__name__)

def fetch_rates() ->dict|None:
    try:
        response = requests.get(settings.exchange_api_url, timeout=10.0)
        response.raise_for_status()

        data = response.json()
        rates = data["rates"]

        result = {}
        for code, usd_rate in rates.items():
            if code =="RUB":
                continue
            result[code] = round(rates["RUB"]/usd_rate,2)
        if "USD" not in result:
            result["USD"] = round(rates["RUB"], 2)


        logger.info(f"Курсы получены: {result}")
        return result
    except Exception:
        logger.exception("Не удалось получить курсы валют")
        return None

