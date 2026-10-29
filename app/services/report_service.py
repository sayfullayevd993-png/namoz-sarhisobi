from datetime import date, datetime, timedelta
from typing import Dict, Any
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import PrayerRecord, QazaEvent

class ReportService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_period_stats(self, user_id: int, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Berilgan vaqt oralig'i bo'yicha hisobot tayyorlash.
        """
        # Jurnal yozuvlari
        stmt = select(PrayerRecord.status, func.count(PrayerRecord.id)).where(
            and_(
                PrayerRecord.user_id == user_id,
                PrayerRecord.prayer_date >= start_date,
                PrayerRecord.prayer_date <= end_date
            )
        ).group_by(PrayerRecord.status)
        result = await self.session.execute(stmt)
        record_counts = dict(result.all())

        prayed_on_time = record_counts.get("prayed_on_time", 0)
        qaza_recorded = record_counts.get("qaza_recorded", 0)
        pending = record_counts.get("pending", 0)

        # Shu davr oralig'idagi umumiy farz namozlar soni (kunlar soni * 5)
        total_days = (end_date - start_date).days + 1
        expected_total = total_days * 5
        unrecorded = max(0, expected_total - (prayed_on_time + qaza_recorded + pending))

        # Shu davrda ado etilgan qazolar
        event_stmt = select(func.coalesce(func.sum(QazaEvent.quantity), 0)).where(
            and_(
                QazaEvent.user_id == user_id,
                QazaEvent.event_type == "completed",
                QazaEvent.event_date >= start_date,
                QazaEvent.event_date <= end_date
            )
        )
        completed_qaza = await self.session.scalar(event_stmt) or 0

        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_days": total_days,
            "prayed_on_time": prayed_on_time,
            "qaza_recorded": qaza_recorded,
            "unanswered": pending + unrecorded,
            "completed_qaza": completed_qaza,
            "expected_total": expected_total
        }

    def format_report_message(self, stats: Dict[str, Any], title: str = "Haftalik sarhisob") -> str:
        s_str = stats["start_date"].strftime("%d.%m.%Y")
        e_str = stats["end_date"].strftime("%d.%m.%Y")
        
        prayed = stats["prayed_on_time"]
        expected = stats["expected_total"]
        pct = (prayed / expected * 100) if expected > 0 else 0

        lines = [
            f"📊 <b>{title}</b>",
            f"🗓 <b>Davr:</b> {s_str} — {e_str} ({stats['total_days']} kun)\n",
            f"✅ <b>Vaqtida o'qilgan namozlar:</b> {prayed} ta ({pct:.1f}%)",
            f"❌ <b>Qazo qilingan namozlar:</b> {stats['qaza_recorded']} ta",
            f"⏳ <b>Javobsiz / Belgilanmagan:</b> {stats['unanswered']} ta",
            f"📿 <b>Ado etilgan qazo namozlar:</b> {stats['completed_qaza']} ta\n",
            "<i>«Albatta, namoz mo'minlarga vaqtida tayinlangan farzdir» (Niso surasi, 103-oyat)</i>"
        ]
        return "\n".join(lines)
