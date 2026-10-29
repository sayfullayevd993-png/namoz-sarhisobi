from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from app.database.session import async_session_maker
from app.database.repository import UserRepository
from app.services.qaza_service import QazaService, QAZA_NAMES
from app.bot.keyboards.inline import get_qaza_keyboard

router = Router(name="qaza")

class QazaInputState(StatesGroup):
    waiting_for_prayer_type = State()
    waiting_for_count = State()

@router.message(F.text == "📿 Qazo hisobi")
async def handle_qaza_menu(message: Message, state: FSMContext):
    await state.clear()
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("Avval /start buyrug'ini bosing.")
            return

        qaza_service = QazaService(session)
        accounts = await qaza_service.get_qaza_summary(user.id)
        text = qaza_service.format_qaza_message(accounts)

    await message.answer(text, reply_markup=get_qaza_keyboard(accounts))

@router.callback_query(F.data.startswith("qaza_sub:"))
async def handle_qaza_subtract(callback: CallbackQuery):
    prayer_type = callback.data.split(":")[1]

    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("Foydalanuvchi topilmadi!", show_alert=True)
            return

        qaza_service = QazaService(session)
        await qaza_service.complete_qaza(user.id, prayer_type, qty=1)
        await session.commit()

        accounts = await qaza_service.get_qaza_summary(user.id)
        text = qaza_service.format_qaza_message(accounts)

    await callback.message.edit_text(text, reply_markup=get_qaza_keyboard(accounts))
    p_name = QAZA_NAMES.get(prayer_type, prayer_type)
    await callback.answer(f"1 ta {p_name} qazosi ado etildi deb belgilandi. Alloh qabul qilsin!")

@router.callback_query(F.data == "qaza_set_initial_menu")
async def handle_qaza_set_initial_menu(callback: CallbackQuery, state: FSMContext):
    keyboard = []
    for p_key, p_name in QAZA_NAMES.items():
        keyboard.append([
            InlineKeyboardButton(text=f"{p_name} qazosini kiritish", callback_data=f"set_q_type:{p_key}")
        ])
    keyboard.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="qaza_back_to_main")])

    text = (
        "✍️ <b>Boshlang'ich qazo namozlari sonini kiritish</b>\n\n"
        "O'zingizda taxminan yoki aniq necha mahal qazo borligini bilgan holda, "
        "quyidagi namoz turini tanlang va sonini yozib yuboring:"
    )
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    await callback.answer()

@router.callback_query(F.data.startswith("set_q_type:"))
async def handle_set_q_type(callback: CallbackQuery, state: FSMContext):
    prayer_type = callback.data.split(":")[1]
    await state.update_data(selected_prayer=prayer_type)
    await state.set_state(QazaInputState.waiting_for_count)

    p_name = QAZA_NAMES.get(prayer_type, prayer_type)
    text = (
        f"✍️ <b>{p_name}</b> namozi uchun boshlang'ich qazo sonini raqam ko'rinishida yuboring:\n"
        f"<i>(Masalan: 30 yoki 365)</i>"
    )
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="qaza_back_to_main")]
    ])
    await callback.message.edit_text(text, reply_markup=cancel_kb)
    await callback.answer()

@router.message(QazaInputState.waiting_for_count)
async def handle_count_input(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, faqat butun musbat son kiriting (masalan: 10, 50, 100):")
        return

    count = int(message.text)
    data = await state.get_data()
    prayer_type = data.get("selected_prayer")
    await state.clear()

    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("Foydalanuvchi topilmadi.")
            return

        qaza_service = QazaService(session)
        await qaza_service.set_initial(user.id, prayer_type, count)
        await session.commit()

        accounts = await qaza_service.get_qaza_summary(user.id)
        text = qaza_service.format_qaza_message(accounts)

    p_name = QAZA_NAMES.get(prayer_type, prayer_type)
    await message.answer(
        f"✅ <b>{p_name}</b> namozi uchun boshlang'ich qazo soni <b>{count} ta</b> qilib saqlandi!\n\n" + text,
        reply_markup=get_qaza_keyboard(accounts)
    )

@router.callback_query(F.data == "qaza_back_to_main")
async def handle_qaza_back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("Foydalanuvchi topilmadi!", show_alert=True)
            return

        qaza_service = QazaService(session)
        accounts = await qaza_service.get_qaza_summary(user.id)
        text = qaza_service.format_qaza_message(accounts)

    await callback.message.edit_text(text, reply_markup=get_qaza_keyboard(accounts))
    await callback.answer()
