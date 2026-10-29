from aiogram import Router, F
from aiogram.types import Message
from app.config import settings
from app.database.session import async_session_maker
from app.database.repository import SettingsRepository
from app.bot.keyboards.inline import get_ehson_keyboard

router = Router(name="ehson")

@router.message(F.text == "❤️ Ehson")
async def handle_ehson_menu(message: Message):
    async with async_session_maker() as session:
        settings_repo = SettingsRepository(session)
        ehson_cfg = await settings_repo.get_ehson_settings(
            fallback_enabled=settings.EHSON_ENABLED,
            fallback_text=settings.EHSON_TEXT,
            fallback_channel=settings.EHSON_CHANNEL_URL
        )

    if not ehson_cfg["enabled"]:
        await message.answer("Ehson bo'limi hozirda nofaol.")
        return

    text = (
        "❤️ <b>Loyiha taraqqiyoti va ehson</b>\n\n"
        f"{ehson_cfg['text']}\n\n"
        f"Alloh taolo barchamizdan qabul qilsin va sadaqayi joriya qilsin!"
    )
    await message.answer(text, reply_markup=get_ehson_keyboard(ehson_cfg["channel_url"]))
