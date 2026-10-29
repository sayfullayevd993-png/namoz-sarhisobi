from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repository import QazaRepository
from app.database.models import QazaAccount

QAZA_NAMES = {
    "bomdod": "Bomdod",
    "peshin": "Peshin",
    "asr": "Asr",
    "shom": "Shom",
    "xufton": "Xufton",
    "vitr": "Vitr vojib"
}

class QazaService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = QazaRepository(session)

    async def get_qaza_summary(self, user_id: int) -> Dict[str, QazaAccount]:
        return await self.repo.get_accounts(user_id)

    async def complete_qaza(self, user_id: int, prayer_type: str, qty: int = 1) -> bool:
        return await self.repo.complete_prayer_qaza(user_id, prayer_type, qty)

    async def add_qaza(self, user_id: int, prayer_type: str, qty: int = 1, source: str = "manual"):
        return await self.repo.add_missed_prayer(user_id, prayer_type, qty, source)

    async def set_initial(self, user_id: int, prayer_type: str, count: int):
        return await self.repo.set_initial_count(user_id, prayer_type, count)

    def format_qaza_message(self, accounts: Dict[str, QazaAccount]) -> str:
        lines = [
            "📿 <b>Qazo namozlari sarhisobi</b>\n",
            "<i>Har bir namoz bo'yicha qolgan qazolar:</i>\n"
        ]

        total_remaining = 0
        for p_key, p_name in QAZA_NAMES.items():
            acc = accounts.get(p_key)
            rem = acc.remaining if acc else 0
            total_remaining += rem
            lines.append(f"• <b>{p_name}:</b> {rem} ta (Ado etilgan: {acc.completed_count if acc else 0})")

        lines.append(f"\n📊 <b>Jami qolgan qazo:</b> {total_remaining} ta")
        lines.append("\n<i>Qazo o'qiganingizda tegishli tugmani bosib sonni kamaytirib boring. Alloh taolo qabul qilsin!</i>")
        return "\n".join(lines)
