import logging
from datetime import date, datetime
from typing import Optional, Dict, Any
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

class NamozApiClient:
    def __init__(self, base_url: str = settings.NAMOZ_API_BASE_URL):
        self.base_url = base_url

    async def get_today_times(self, slug: str) -> Optional[Dict[str, str]]:
        """
        Berilgan hudud slug bo'yicha bugungi namoz vaqtlarini qaytaradi.
        Format:
        {
            "bomdod": "05:15",
            "quyosh": "06:32",
            "peshin": "12:10",
            "asr": "15:40",
            "shom": "17:45",
            "xufton": "19:05",
            "date": "2026-10-25"
        }
        """
        params = {
            "format": "json",
            "region": slug,
            "period": "today"
        }
        headers = {
            "Accept": "application/json",
            "User-Agent": "NamozSarhisobiBot/1.0"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.base_url, params=params, headers=headers)
                if response.status_code != 200:
                    logger.error(f"API xatosi: status {response.status_code} ({slug})")
                    return None

                data = response.json()
                times = None
                
                # Turli JSON strukturalarini qo'llab-quvvatlash
                if "today" in data and "times" in data["today"]:
                    times = data["today"]["times"]
                elif "times" in data:
                    times = data["times"]
                elif "items" in data and len(data["items"]) > 0:
                    times = data["items"][0]

                if not times:
                    logger.error(f"API javobida vaqtlar topilmadi: {data}")
                    return None

                # Standartlashtirish
                result = {
                    "bomdod": times.get("bomdod") or times.get("fajr") or times.get("tong_saharlik"),
                    "quyosh": times.get("quyosh") or times.get("sunrise"),
                    "peshin": times.get("peshin") or times.get("dhuhr"),
                    "asr": times.get("asr"),
                    "shom": times.get("shom") or times.get("maghrib"),
                    "xufton": times.get("xufton") or times.get("isha"),
                    "date": data.get("meta", {}).get("date") or str(date.today())
                }
                return result

        except Exception as e:
            logger.exception(f"Namoz vaqtlarini olishda xatolik yuz berdi ({slug}): {e}")
            return None

api_client = NamozApiClient()
