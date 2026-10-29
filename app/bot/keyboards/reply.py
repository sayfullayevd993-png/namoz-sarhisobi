from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from typing import List

def get_main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="🕌 Namoz vaqtlarim"),
            KeyboardButton(text="📖 Kundalik jurnal")
        ],
        [
            KeyboardButton(text="📊 Sarhisob"),
            KeyboardButton(text="📿 Qazo hisobi")
        ],
        [
            KeyboardButton(text="⚙️ Sozlamalar"),
            KeyboardButton(text="❤️ Ehson")
        ]
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text="🛠 Admin panel")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        persistent=True
    )
