
import logging
import json
import requests
import redis


from app.database import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

redis_client = redis.Redis(
    host= settings.redis_host,
    port = settings.redis_port,
    db = 0,
    decode_responses=True
)

def fetch_rates() ->dict|None:
    try:
        # Проверка кэша
        cached_rates = redis_client.get("currency_rates")
        if cached_rates:
            logger.info("Курсы взяты из кэша")
            return json.loads(cached_rates)
        logger.info("Кэш пуст. Идем в API...")

        # запроса к API
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
        # сохранение в кэш
        redis_client.setex("currency_rates",3600,json.dumps(result))
        logger.info(f"Курсы сохранены в Redis на 1 час")

        return result
    except Exception:
        logger.exception("Не удалось получить курсы валют")
        return None

