from datetime import date, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from app.database.session import async_session_maker
from app.database.repository import UserRepository
from app.services.report_service import ReportService

router = Router(name="reports")

def get_report_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🗓 So'nggi 7 kunlik", callback_data="rep_view:weekly"),
                InlineKeyboardButton(text="📆 So'nggi 30 kunlik", callback_data="rep_view:monthly")
            ]
        ]
    )

@router.message(F.text == "📊 Sarhisob")
async def handle_reports_menu(message: Message):
    today = date.today()
    week_start = today - timedelta(days=6)

    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("Avval /start buyrug'ini bosing.")
            return

        report_service = ReportService(session)
        stats = await report_service.get_period_stats(user.id, week_start, today)
        text = report_service.format_report_message(stats, title="Haftalik sarhisob")

    await message.answer(text, reply_markup=get_report_type_keyboard())

@router.callback_query(F.data.startswith("rep_view:"))
async def handle_report_view(callback: CallbackQuery):
    r_type = callback.data.split(":")[1]
    today = date.today()

    if r_type == "monthly":
        start_date = today - timedelta(days=29)
        title = "Oylik sarhisob (So'nggi 30 kun)"
    else:
        start_date = today - timedelta(days=6)
        title = "Haftalik sarhisob (So'nggi 7 kun)"

    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("Foydalanuvchi topilmadi!", show_alert=True)
            return

        report_service = ReportService(session)
        stats = await report_service.get_period_stats(user.id, start_date, today)
        text = report_service.format_report_message(stats, title=title)

    await callback.message.edit_text(text, reply_markup=get_report_type_keyboard())
    await callback.answer()
