from datetime import date
from aiogram import Router, F
from aiogram.types import Message
from app.database.session import async_session_maker
from app.database.repository import UserRepository, LocationRepository
from app.services.prayer_service import PrayerService
from app.bot.keyboards.inline import get_regions_inline_keyboard

router = Router(name="prayers")

@router.message(F.text == "🕌 Namoz vaqtlarim")
async def handle_prayer_times(message: Message):
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        loc_repo = LocationRepository(session)
        prayer_service = PrayerService(session)

        user = await user_repo.get_by_telegram_id(message.from_user.id)
        if not user or not user.location_id:
            await message.answer(
                "Siz hali hududingizni tanlamagansiz. Iltimos, avval viloyatingizni tanlang:",
                reply_markup=get_regions_inline_keyboard()
            )
            return

        location = await loc_repo.get_by_id(user.location_id)
        if not location:
            await message.answer(
                "Hudud ma'lumoti topilmadi. Qaytadan tanlang:",
                reply_markup=get_regions_inline_keyboard()
            )
            return

        pt = await prayer_service.get_or_fetch_prayer_times(location, date.today())
        await session.commit()

        if not pt:
            await message.answer(
                f"⚠️ Hozirda {location.district_name} bo'yicha namoz vaqtlarini yuklab bo'lmadi. "
                f"Birozdan so'ng qayta urinib ko'ring."
            )
            return

        text = prayer_service.format_prayer_message(pt, location.district_name)
        await message.answer(text)
