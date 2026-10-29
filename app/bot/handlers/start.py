from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from app.database.session import async_session_maker
from app.database.repository import UserRepository, LocationRepository
from app.bot.keyboards.reply import get_main_keyboard
from app.bot.keyboards.inline import get_regions_inline_keyboard, get_districts_inline_keyboard
from app.services.prayer_service import PrayerService
from app.utils.regions import find_district_by_slug, get_region_name_by_key
from app.config import settings

router = Router(name="start")

@router.message(CommandStart())
async def handle_start(message: Message):
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.create_or_update(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name
        )
        await session.commit()

        is_admin = message.from_user.id in settings.admin_id_list

        if not user.location_id:
            text = (
                f"Assalomu alaykum, <b>{message.from_user.first_name}</b>!\n\n"
                f"<b>«Namoz sarhisobi»</b> botiga xush kelibsiz.\n"
                f"Bu bot sizga namoz vaqtlarini aniq eslatib borish, kundalik namozlaringizni "
                f"qayd qilib borish va qazo namozlaringiz hisobini tartibli yuritishda yordam beradi.\n\n"
                f"Iltimos, namoz vaqtlarini aniqlash uchun o'z <b>viloyatingizni</b> tanlang:"
            )
            await message.answer(text, reply_markup=get_regions_inline_keyboard())
        else:
            text = (
                f"Assalomu alaykum, <b>{message.from_user.first_name}</b>!\n"
                f"Asosiy menyudasiz. Kerakli bo'limni tanlang:"
            )
            await message.answer(text, reply_markup=get_main_keyboard(is_admin=is_admin))

@router.callback_query(F.data.startswith("sel_reg:"))
async def handle_select_region(callback: CallbackQuery):
    reg_key = callback.data.split(":")[1]
    reg_name = get_region_name_by_key(reg_key)
    
    text = f"📍 <b>{reg_name}</b>\n\nIltimos, shahar yoki tumaningizni tanlang:"
    await callback.message.edit_text(text, reply_markup=get_districts_inline_keyboard(reg_key))
    await callback.answer()

@router.callback_query(F.data == "back_to_regions")
async def handle_back_to_regions(callback: CallbackQuery):
    text = "Iltimos, o'z <b>viloyatingizni</b> tanlang:"
    await callback.message.edit_text(text, reply_markup=get_regions_inline_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("sel_dist:"))
async def handle_select_district(callback: CallbackQuery):
    slug = callback.data.split(":")[1]
    dist_info = find_district_by_slug(slug)
    
    if not dist_info:
        await callback.answer("Hudud topilmadi!", show_alert=True)
        return

    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        loc_repo = LocationRepository(session)
        prayer_service = PrayerService(session)

        # Hududni bazada topish yoki yaratish
        loc = await loc_repo.get_or_create(
            region_name=dist_info["region_name"],
            district_name=dist_info["district_name"],
            slug=dist_info["slug"]
        )

        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if user:
            await user_repo.set_location(user.id, loc.id)
            await session.commit()

        # Bugungi namoz vaqtlarini olish
        pt = await prayer_service.get_or_fetch_prayer_times(loc)
        await session.commit()

    is_admin = callback.from_user.id in settings.admin_id_list
    success_text = (
        f"✅ <b>Hudud muvaffaqiyatli saqlandi:</b> {dist_info['district_name']}\n\n"
    )

    if pt:
        success_text += prayer_service.format_prayer_message(pt, dist_info['district_name'])
    else:
        success_text += "Bugungi namoz vaqtlari tez orada yangilanadi."

    await callback.message.delete()
    await callback.message.answer(
        success_text,
        reply_markup=get_main_keyboard(is_admin=is_admin)
    )
    await callback.answer("Hudud saqlandi!")
