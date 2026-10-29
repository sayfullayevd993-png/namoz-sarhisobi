import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramAPIError
from app.config import settings
from app.database.session import async_session_maker
from app.database.repository import UserRepository, SettingsRepository
from app.database.models import BroadcastJob, AuditLog

router = Router(name="admin")

class BroadcastState(StatesGroup):
    waiting_for_message = State()
    confirm_broadcast = State()

class EhsonEditState(StatesGroup):
    waiting_for_text = State()
    waiting_for_channel = State()

def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Umumiy statistika", callback_data="admin_stats")],
            [InlineKeyboardButton(text="📢 Ommaviy xabar yuborish", callback_data="admin_broadcast_start")],
            [InlineKeyboardButton(text="❤️ Ehson bo'limi sozlamalari", callback_data="admin_ehson_menu")],
            [InlineKeyboardButton(text="⚙️ Tizim holati", callback_data="admin_sys_status")]
        ]
    )

def get_ehson_admin_keyboard(is_enabled: bool) -> InlineKeyboardMarkup:
    toggle_text = "🔴 Bo'limni o'chirish" if is_enabled else "🟢 Bo'limni yoqish"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=toggle_text, callback_data="admin_ehson_toggle")],
            [InlineKeyboardButton(text="✍️ Matnni tahrirlash", callback_data="admin_ehson_edit_text")],
            [InlineKeyboardButton(text="🔗 Kanal havolasini o'zgartirish", callback_data="admin_ehson_edit_channel")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_back_main")]
        ]
    )

@router.message(F.text == "🛠 Admin panel")
async def handle_admin_entry(message: Message, state: FSMContext):
    if message.from_user.id not in settings.admin_id_list:
        return
    await state.clear()
    text = (
        "🛠 <b>Admin boshqaruv paneli</b>\n\n"
        "Quyidagi amallardan birini tanlang:"
    )
    await message.answer(text, reply_markup=get_admin_main_keyboard())

@router.callback_query(F.data == "admin_stats")
async def handle_admin_stats(callback: CallbackQuery):
    if callback.from_user.id not in settings.admin_id_list:
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        stats = await user_repo.get_stats()

    text = (
        "📊 <b>Bot foydalanuvchilari statistikasi:</b>\n\n"
        f"👥 <b>Jami foydalanuvchilar:</b> {stats['total']}\n"
        f"🟢 <b>Faol akkauntlar:</b> {stats['active']}\n"
        f"📍 <b>Hududni tanlaganlar:</b> {stats['with_location']}\n"
        f"🚫 <b>Bloklaganlar:</b> {stats['blocked']}\n"
    )
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_back_main")]
    ])
    await callback.message.edit_text(text, reply_markup=back_kb)
    await callback.answer()

# ==================== EHSON BO'LIMI BOSHQARUVI ====================

@router.callback_query(F.data == "admin_ehson_menu")
async def handle_admin_ehson_menu(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in settings.admin_id_list:
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return
    await state.clear()

    async with async_session_maker() as session:
        settings_repo = SettingsRepository(session)
        cfg = await settings_repo.get_ehson_settings(
            fallback_enabled=settings.EHSON_ENABLED,
            fallback_text=settings.EHSON_TEXT,
            fallback_channel=settings.EHSON_CHANNEL_URL
        )

    status_badge = "Yoqilgan ✅" if cfg["enabled"] else "O'chirilgan ❌"
    text = (
        "❤️ <b>Ehson bo'limi sozlamalari</b>\n\n"
        f"🔘 <b>Holati:</b> {status_badge}\n"
        f"🔗 <b>Kanal havolasi:</b> {cfg['channel_url']}\n\n"
        f"📝 <b>Hozirgi matn:</b>\n"
        f"<i>{cfg['text']}</i>\n\n"
        "O'zgartirish uchun kerakli tugmani bosing:"
    )
    await callback.message.edit_text(text, reply_markup=get_ehson_admin_keyboard(cfg["enabled"]))
    await callback.answer()

@router.callback_query(F.data == "admin_ehson_toggle")
async def handle_admin_ehson_toggle(callback: CallbackQuery):
    if callback.from_user.id not in settings.admin_id_list:
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    async with async_session_maker() as session:
        settings_repo = SettingsRepository(session)
        cfg = await settings_repo.get_ehson_settings(
            fallback_enabled=settings.EHSON_ENABLED,
            fallback_text=settings.EHSON_TEXT,
            fallback_channel=settings.EHSON_CHANNEL_URL
        )
        new_status = await settings_repo.toggle_ehson(cfg["enabled"])
        
        audit = AuditLog(
            admin_id=callback.from_user.id,
            action="toggle_ehson",
            details=f"Yangi holat: {'Yoqildi' if new_status else 'Ochirildi'}"
        )
        session.add(audit)
        await session.commit()

        # Yangilangan sozlamalar
        cfg["enabled"] = new_status

    status_badge = "Yoqilgan ✅" if cfg["enabled"] else "O'chirilgan ❌"
    text = (
        "❤️ <b>Ehson bo'limi sozlamalari</b>\n\n"
        f"🔘 <b>Holati:</b> {status_badge}\n"
        f"🔗 <b>Kanal havolasi:</b> {cfg['channel_url']}\n\n"
        f"📝 <b>Hozirgi matn:</b>\n"
        f"<i>{cfg['text']}</i>\n\n"
        "O'zgartirish uchun kerakli tugmani bosing:"
    )
    await callback.message.edit_text(text, reply_markup=get_ehson_admin_keyboard(cfg["enabled"]))
    await callback.answer("Ehson holati yangilandi!")

@router.callback_query(F.data == "admin_ehson_edit_text")
async def handle_admin_ehson_edit_text(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in settings.admin_id_list:
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    await state.set_state(EhsonEditState.waiting_for_text)
    text = (
        "✍️ <b>Ehson bo'limi uchun yangi matnni kiriting:</b>\n\n"
        "<i>(Foydalanuvchi «❤️ Ehson» tugmasini bosganida chiqadigan xabar matnini yuboring. HTML formatlashdan foydalanishingiz mumkin)</i>"
    )
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_ehson_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=cancel_kb)
    await callback.answer()

@router.message(EhsonEditState.waiting_for_text)
async def handle_save_ehson_text(message: Message, state: FSMContext):
    if message.from_user.id not in settings.admin_id_list:
        return

    new_text = message.html_text or message.text
    await state.clear()

    async with async_session_maker() as session:
        settings_repo = SettingsRepository(session)
        await settings_repo.set_ehson_text(new_text)

        audit = AuditLog(
            admin_id=message.from_user.id,
            action="edit_ehson_text",
            details=f"Yangi matn: {new_text[:80]}..."
        )
        session.add(audit)
        await session.commit()

        cfg = await settings_repo.get_ehson_settings(
            fallback_enabled=settings.EHSON_ENABLED,
            fallback_text=settings.EHSON_TEXT,
            fallback_channel=settings.EHSON_CHANNEL_URL
        )

    await message.answer(
        "✅ <b>Ehson matni muvaffaqiyatli yangilandi!</b>\n\n"
        f"📝 <b>Yangi matn:</b>\n<i>{new_text}</i>",
        reply_markup=get_ehson_admin_keyboard(cfg["enabled"])
    )

@router.callback_query(F.data == "admin_ehson_edit_channel")
async def handle_admin_ehson_edit_channel(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in settings.admin_id_list:
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    await state.set_state(EhsonEditState.waiting_for_channel)
    text = (
        "🔗 <b>Ehson hisobot kanali havolasini yuboring:</b>\n\n"
        "<i>(Masalan: https://t.me/namoz_sarhisobi_ehson)</i>"
    )
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_ehson_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=cancel_kb)
    await callback.answer()

@router.message(EhsonEditState.waiting_for_channel)
async def handle_save_ehson_channel(message: Message, state: FSMContext):
    if message.from_user.id not in settings.admin_id_list:
        return

    new_url = message.text.strip()
    if not (new_url.startswith("https://t.me/") or new_url.startswith("http://t.me/") or new_url.startswith("@")):
        await message.answer("⚠️ Iltimos, to'g'ri Telegram havolasini kiriting (masalan: https://t.me/kanal_nomi):")
        return

    if new_url.startswith("@"):
        new_url = f"https://t.me/{new_url[1:]}"

    await state.clear()

    async with async_session_maker() as session:
        settings_repo = SettingsRepository(session)
        await settings_repo.set_ehson_channel(new_url)

        audit = AuditLog(
            admin_id=message.from_user.id,
            action="edit_ehson_channel",
            details=f"Yangi kanal: {new_url}"
        )
        session.add(audit)
        await session.commit()

        cfg = await settings_repo.get_ehson_settings(
            fallback_enabled=settings.EHSON_ENABLED,
            fallback_text=settings.EHSON_TEXT,
            fallback_channel=settings.EHSON_CHANNEL_URL
        )

    await message.answer(
        f"✅ <b>Kanal havolasi muvaffaqiyatli saqlandi:</b> {new_url}",
        reply_markup=get_ehson_admin_keyboard(cfg["enabled"])
    )

# =================================================================

@router.callback_query(F.data == "admin_sys_status")
async def handle_admin_sys_status(callback: CallbackQuery):
    if callback.from_user.id not in settings.admin_id_list:
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    async with async_session_maker() as session:
        settings_repo = SettingsRepository(session)
        cfg = await settings_repo.get_ehson_settings(
            fallback_enabled=settings.EHSON_ENABLED,
            fallback_text=settings.EHSON_TEXT,
            fallback_channel=settings.EHSON_CHANNEL_URL
        )

    text = (
        "⚙️ <b>Tizim holati:</b>\n\n"
        f"🌐 <b>API manbasi:</b> {settings.NAMOZ_API_BASE_URL}\n"
        f"🕒 <b>Vaqt mintaqasi:</b> {settings.TIMEZONE}\n"
        f"💾 <b>Ma'lumotlar bazasi:</b> Faol\n"
        f"❤️ <b>Ehson bo'limi:</b> {'Yoqilgan' if cfg['enabled'] else 'O\'chirilgan'}\n"
        f"📢 <b>Majburiy kanal:</b> {settings.REQUIRED_CHANNEL_ID or 'Yo\'q'}\n"
    )
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_back_main")]
    ])
    await callback.message.edit_text(text, reply_markup=back_kb)
    await callback.answer()

@router.callback_query(F.data == "admin_back_main")
async def handle_admin_back_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🛠 <b>Admin boshqaruv paneli</b>", reply_markup=get_admin_main_keyboard())
    await callback.answer()

@router.callback_query(F.data == "admin_broadcast_start")
async def handle_admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in settings.admin_id_list:
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    await state.set_state(BroadcastState.waiting_for_message)
    text = (
        "📢 <b>Ommaviy xabar yuborish</b>\n\n"
        "Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringiz matnini kiriting:\n"
        "<i>(Xabar matnida HTML teglardan foydalanishingiz mumkin)</i>"
    )
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_back_main")]
    ])
    await callback.message.edit_text(text, reply_markup=cancel_kb)
    await callback.answer()

@router.message(BroadcastState.waiting_for_message)
async def handle_broadcast_preview(message: Message, state: FSMContext):
    if message.from_user.id not in settings.admin_id_list:
        return

    broadcast_text = message.html_text or message.text
    await state.update_data(broadcast_text=broadcast_text)
    await state.set_state(BroadcastState.confirm_broadcast)

    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Yuborishni tasdiqlash", callback_data="admin_broadcast_confirm")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_back_main")]
    ])

    await message.answer(
        f"<b>Xabar namunasi:</b>\n"
        f"────────────────────\n"
        f"{broadcast_text}\n"
        f"────────────────────\n\n"
        f"Haqiqatan ham barcha foydalanuvchilarga yuborasizmi?",
        reply_markup=confirm_kb
    )

@router.callback_query(F.data == "admin_broadcast_confirm", BroadcastState.confirm_broadcast)
async def handle_broadcast_send(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in settings.admin_id_list:
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    data = await state.get_data()
    broadcast_text = data.get("broadcast_text")
    await state.clear()

    await callback.message.edit_text("⏳ Xabar foydalanuvchilarga yuborilmoqda, kuting...")
    await callback.answer()

    sent_count = 0
    failed_count = 0

    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        users = await user_repo.get_all_active_users()

        for u in users:
            try:
                await callback.bot.send_message(chat_id=u.telegram_id, text=broadcast_text)
                sent_count += 1
                await asyncio.sleep(0.05) # Telegram flood limits
            except TelegramAPIError:
                failed_count += 1

        # Audit yozuvi
        audit = AuditLog(
            admin_id=callback.from_user.id,
            action="broadcast",
            details=f"Yuborildi: {sent_count}, Xatolik: {failed_count}"
        )
        session.add(audit)
        await session.commit()

    await callback.message.answer(
        f"✅ <b>Ommaviy xabar yuborish yakunlandi!</b>\n\n"
        f"📤 Yuborildi: {sent_count} ta\n"
        f"❌ Xatolik (bloklaganlar): {failed_count} ta"
    )
