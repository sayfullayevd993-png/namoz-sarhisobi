from datetime import datetime, date
from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.database.session import async_session_maker
from app.database.repository import UserRepository, PrayerRecordRepository
from app.services.journal_service import JournalService

router = Router(name="reminders")

PRAYER_NAMES_UZ = {
    "bomdod": "Bomdod",
    "peshin": "Peshin",
    "asr": "Asr",
    "shom": "Shom",
    "xufton": "Xufton"
}

@router.callback_query(F.data.startswith("rem_act:"))
async def handle_reminder_action(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer("Noto'g'ri so'rov!", show_alert=True)
        return

    action = parts[1]        # "prayed" yoki "missed"
    prayer_type = parts[2]   # "bomdod", "peshin", va h.k.
    date_str = parts[3]      # "2026-10-25"

    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        target_date = date.today()

    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("Foydalanuvchi topilmadi!", show_alert=True)
            return

        rec_repo = PrayerRecordRepository(session)
        existing_record = await rec_repo.get_record(user.id, target_date, prayer_type)

        # Takroriy bosishdan himoya (agar allaqachon shu holatda bo'lsa)
        expected_status = "prayed_on_time" if action == "prayed" else "qaza_recorded"
        if existing_record and existing_record.status == expected_status:
            await callback.answer("Bu holat allaqachon belgilangan!", show_alert=False)
            return

        journal_service = JournalService(session)
        await journal_service.mark_prayer(
            user_id=user.id,
            target_date=target_date,
            prayer_type=prayer_type,
            status=expected_status,
            source="button_eslatma"
        )
        await session.commit()

    p_uz = PRAYER_NAMES_UZ.get(prayer_type, prayer_type.capitalize())
    
    if action == "prayed":
        resp_note = f"✅ <b>{p_uz} namozi:</b> Vaqtida o'qildi deb qayd qilindi. Alloh qabul qilsin!"
        alert_msg = "Alloh qabul qilsin!"
    else:
        extra_note = " (Xufton bilan birga Vitr vojib ham qazoga kiritildi)" if prayer_type == "xufton" else ""
        resp_note = f"❌ <b>{p_uz} namozi:</b> Qazo ro'yxatiga avtomatik qo'shildi{extra_note}. Fursat topib ado etishni unutmang."
        alert_msg = "Qazo hisobiga qo'shildi."

    # Xabarni yangilab, tugmalarni olib tashlaymiz yoki yangilangan status bilan almashtiramiz
    original_text = callback.message.html_text or callback.message.text or ""
    new_text = f"{original_text}\n\n{resp_note}"
    
    await callback.message.edit_text(new_text, reply_markup=None)
    await callback.answer(alert_msg)
