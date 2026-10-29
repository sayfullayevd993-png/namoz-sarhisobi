from datetime import date, datetime, timedelta
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repository import PrayerRecordRepository, QazaRepository
from app.database.models import PrayerRecord

PRAYER_TITLES = {
    "bomdod": "Bomdod",
    "peshin": "Peshin",
    "asr": "Asr",
    "shom": "Shom",
    "xufton": "Xufton"
}

STATUS_ICONS = {
    "prayed_on_time": "✅ O'qildi",
    "qaza_recorded": "❌ Qazo bo'ldi",
    "pending": "⏳ Kutilmoqda"
}

class JournalService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.rec_repo = PrayerRecordRepository(session)
        self.qaza_repo = QazaRepository(session)

    async def get_daily_journal(self, user_id: int, target_date: date) -> Dict[str, str]:
        return await self.rec_repo.get_daily_records(user_id, target_date)

    async def mark_prayer(self, user_id: int, target_date: date, prayer_type: str, status: str, source: str = "button") -> PrayerRecord:
        """
        Namoz holatini belgilash.
        Agar status 'qaza_recorded' bo'lsa, avtomatik qazo hisobiga qo'shiladi.
        Agar Xufton bo'lsa, qoidaga binoan Vitr ham qo'shiladi.
        """
        record = await self.rec_repo.set_record_status(user_id, target_date, prayer_type, status)
        
        if status == "qaza_recorded":
            await self.qaza_repo.add_missed_prayer(user_id, prayer_type, qty=1, source=source)
            
        return record

    def format_journal_message(self, records: Dict[str, str], target_date: date) -> str:
        d_str = target_date.strftime("%d.%m.%Y")
        lines = [
            f"📖 <b>Kundalik namoz jurnali</b>",
            f"📅 <b>Sana:</b> {d_str}\n"
        ]
        
        prayed_count = sum(1 for s in records.values() if s == "prayed_on_time")
        qaza_count = sum(1 for s in records.values() if s == "qaza_recorded")

        for p_key, p_title in PRAYER_TITLES.items():
            status = records.get(p_key, "pending")
            icon_text = STATUS_ICONS.get(status, "⏳ Kutilmoqda")
            lines.append(f"• <b>{p_title}:</b> {icon_text}")

        lines.append(f"\n📊 <b>Kunlik sarhisob:</b> O'qilgan: {prayed_count}/5 | Qazo: {qaza_count}/5")
        lines.append("<i>Quyidagi tugmalar orqali har bir namoz holatini o'zgartirishingiz mumkin:</i>")
        return "\n".join(lines)
