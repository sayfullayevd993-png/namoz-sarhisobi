from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from app.database.session import async_session_maker
from app.database.repository import UserRepository, LocationRepository, QazaRepository
from app.bot.keyboards.inline import get_settings_keyboard, get_regions_inline_keyboard

router = Router(name="settings")

@router.message(F.text == "⚙️ Sozlamalar")
async def handle_settings_menu(message: Message):
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        loc_repo = LocationRepository(session)

        user = await user_repo.get_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("Avval /start buyrug'ini bosing.")
            return

        loc_name = "Belgilanmagan"
        if user.location_id:
            loc = await loc_repo.get_by_id(user.location_id)
            if loc:
                loc_name = f"{loc.region_name}, {loc.district_name}"

        text = (
            f"⚙️ <b>Sozlamalar bo'limi</b>\n\n"
            f"📍 <b>Hozirgi hudud:</b> {loc_name}\n"
            f"🔔 <b>Eslatmalar holati:</b> {'Yoqilgan ✅' if user.reminders_enabled else 'O\'chirilgan ❌'}\n"
            f"📊 <b>Haftalik sarhisob:</b> {'Yoqilgan ✅' if user.weekly_report_enabled else 'O\'chirilgan ❌'}\n\n"
            f"<i>Kerakli sozlamani o'zgartirish uchun quyidagi tugmalardan foydalaning:</i>"
        )
        await message.answer(
            text,
            reply_markup=get_settings_keyboard(user.reminders_enabled, user.weekly_report_enabled)
        )

@router.callback_query(F.data == "change_location")
async def handle_change_location(callback: CallbackQuery):
    text = "📍 Namoz vaqtlarini hisoblash uchun <b>viloyatingizni</b> tanlang:"
    await callback.message.edit_text(text, reply_markup=get_regions_inline_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("toggle_setting:"))
async def handle_toggle_setting(callback: CallbackQuery):
    setting_type = callback.data.split(":")[1]
    
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        loc_repo = LocationRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("Foydalanuvchi topilmadi!", show_alert=True)
            return

        if setting_type == "reminders":
            user.reminders_enabled = not user.reminders_enabled
        elif setting_type == "weekly_report":
            user.weekly_report_enabled = not user.weekly_report_enabled

        await session.commit()

        loc_name = "Belgilanmagan"
        if user.location_id:
            loc = await loc_repo.get_by_id(user.location_id)
            if loc:
                loc_name = f"{loc.region_name}, {loc.district_name}"

        text = (
            f"⚙️ <b>Sozlamalar bo'limi</b>\n\n"
            f"📍 <b>Hozirgi hudud:</b> {loc_name}\n"
            f"🔔 <b>Eslatmalar holati:</b> {'Yoqilgan ✅' if user.reminders_enabled else 'O\'chirilgan ❌'}\n"
            f"📊 <b>Haftalik sarhisob:</b> {'Yoqilgan ✅' if user.weekly_report_enabled else 'O\'chirilgan ❌'}\n\n"
            f"<i>Sozlamalar yangilandi:</i>"
        )
        await callback.message.edit_text(
            text,
            reply_markup=get_settings_keyboard(user.reminders_enabled, user.weekly_report_enabled)
        )
    await callback.answer("Sozlama yangilandi!")

@router.callback_query(F.data == "clear_my_data")
async def handle_clear_data_prompt(callback: CallbackQuery):
    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚠️ Ha, barchasini tozalash", callback_data="confirm_clear_my_data")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_clear_my_data")]
    ])
    text = (
        "⚠️ <b>Diqqat!</b>\n\n"
        "Barcha qazo hisoblaringiz va jurnal qaydlaringiz nollashtiriladi. "
        "Ushbu amalni ortga qaytarib bo'lmaydi.\n\n"
        "Haqiqatan ham ma'lumotlaringizni tozalashni xohlaysizmi?"
    )
    await callback.message.edit_text(text, reply_markup=confirm_kb)
    await callback.answer()

@router.callback_query(F.data == "cancel_clear_my_data")
async def handle_cancel_clear(callback: CallbackQuery):
    await callback.answer("Bekor qilindi.")
    await callback.message.delete()

@router.callback_query(F.data == "confirm_clear_my_data")
async def handle_confirm_clear(callback: CallbackQuery):
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if user:
            qaza_repo = QazaRepository(session)
            accounts = await qaza_repo.get_accounts(user.id)
            for acc in accounts.values():
                acc.initial_count = 0
                acc.added_count = 0
                acc.completed_count = 0
            await session.commit()

    await callback.message.edit_text("✅ Sizning qazo hisoblaringiz muvaffaqiyatli nollashtirildi.")
    await callback.answer()
