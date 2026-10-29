from datetime import date, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from app.database.session import async_session_maker
from app.database.repository import UserRepository
from app.services.journal_service import JournalService
from app.bot.keyboards.inline import get_journal_keyboard

router = Router(name="journal")

@router.message(F.text == "📖 Kundalik jurnal")
async def handle_journal_menu(message: Message):
    today = date.today()
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("Avval /start buyrug'ini bosing.")
            return

        journal_service = JournalService(session)
        records = await journal_service.get_daily_journal(user.id, today)
        text = journal_service.format_journal_message(records, today)

    await message.answer(text, reply_markup=get_journal_keyboard(today, records))

@router.callback_query(F.data.startswith("jnl_date:"))
async def handle_journal_date(callback: CallbackQuery):
    date_str = callback.data.split(":")[1]
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

        journal_service = JournalService(session)
        records = await journal_service.get_daily_journal(user.id, target_date)
        text = journal_service.format_journal_message(records, target_date)

    await callback.message.edit_text(text, reply_markup=get_journal_keyboard(target_date, records))
    await callback.answer()

@router.callback_query(F.data.startswith("jnl_toggle:"))
async def handle_journal_toggle(callback: CallbackQuery):
    parts = callback.data.split(":")
    prayer_type = parts[1]
    target_date = date.fromisoformat(parts[2])

    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("Foydalanuvchi topilmadi!", show_alert=True)
            return

        journal_service = JournalService(session)
        records = await journal_service.get_daily_journal(user.id, target_date)
        current_status = records.get(prayer_type, "pending")

        # Holatni ketma-ket almashtirish: pending -> prayed_on_time -> qaza_recorded -> pending
        if current_status == "pending":
            new_status = "prayed_on_time"
        elif current_status == "prayed_on_time":
            new_status = "qaza_recorded"
        else:
            new_status = "pending"

        await journal_service.mark_prayer(
            user_id=user.id,
            target_date=target_date,
            prayer_type=prayer_type,
            status=new_status,
            source="journal_toggle"
        )
        await session.commit()

        # Yangilangan jurnallarni olish
        updated_records = await journal_service.get_daily_journal(user.id, target_date)
        text = journal_service.format_journal_message(updated_records, target_date)

    await callback.message.edit_text(text, reply_markup=get_journal_keyboard(target_date, updated_records))
    await callback.answer(f"Holat o'zgartirildi: {new_status}")
