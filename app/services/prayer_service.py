from datetime import date, datetime
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repository import LocationRepository, PrayerTimeRepository
from app.database.models import PrayerTime, Location
from app.utils.api_client import api_client

PRAYER_DISPLAY_NAMES = {
    "bomdod": "Bomdod (Tong)",
    "quyosh": "Quyosh",
    "peshin": "Peshin",
    "asr": "Asr",
    "shom": "Shom",
    "xufton": "Xufton"
}

class PrayerService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.loc_repo = LocationRepository(session)
        self.pt_repo = PrayerTimeRepository(session)

    async def get_or_fetch_prayer_times(self, location: Location, target_date: Optional[date] = None) -> Optional[PrayerTime]:
        if not target_date:
            target_date = date.today()

        # Avval bazadan tekshiramiz
        pt = await self.pt_repo.get_prayer_time(location.id, target_date)
        if pt:
            return pt

        # Agar bugungi kun bo'lsa va bazada bo'lmasa, API dan olib saqlaymiz
        if target_date == date.today():
            api_data = await api_client.get_today_times(location.slug)
            if api_data:
                pt = await self.pt_repo.save_prayer_time(location.id, target_date, api_data)
                return pt

        return None

    def format_prayer_message(self, pt: PrayerTime, location_name: str) -> str:
        d_str = pt.prayer_date.strftime("%d.%m.%Y")
        return (
            f"🕌 <b>Namoz vaqtlari</b>\n"
            f"📍 <b>Hudud:</b> {location_name}\n"
            f"📅 <b>Sana:</b> {d_str}\n\n"
            f"🌅 <b>Bomdod:</b> {pt.bomdod}\n"
            f"☀️ <b>Quyosh:</b> {pt.quyosh}\n"
            f"☀️ <b>Peshin:</b> {pt.peshin}\n"
            f"⛅ <b>Asr:</b> {pt.asr}\n"
            f"🌇 <b>Shom:</b> {pt.shom}\n"
            f"🌌 <b>Xufton:</b> {pt.xufton}\n\n"
            f"<i>Manba: namoz-vaqti.uz (O'MI taqvimi asosida)</i>"
        )
