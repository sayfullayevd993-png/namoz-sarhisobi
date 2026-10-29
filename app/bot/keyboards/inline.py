from datetime import date, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.utils.regions import REGIONS_DATA

def get_regions_inline_keyboard() -> InlineKeyboardMarkup:
    """Viloyatlar ro'yxati (2 ustun)"""
    keyboard = []
    row = []
    for r_key, r_val in REGIONS_DATA.items():
        row.append(InlineKeyboardButton(text=r_val["name"], callback_data=f"sel_reg:{r_key}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_districts_inline_keyboard(region_key: str) -> InlineKeyboardMarkup:
    """Tanlangan viloyatning tuman/shaharlari ro'yxati"""
    region = REGIONS_DATA.get(region_key)
    if not region:
        return InlineKeyboardMarkup(inline_keyboard=[])

    keyboard = []
    row = []
    for d in region["districts"]:
        row.append(InlineKeyboardButton(text=d["name"], callback_data=f"sel_dist:{d['slug']}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # Ortga qaytish tugmasi
    keyboard.append([InlineKeyboardButton(text="⬅️ Viloyatlarga qaytish", callback_data="back_to_regions")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_reminder_keyboard(prayer_type: str, prayer_date: str) -> InlineKeyboardMarkup:
    """Namoz eslatmasi ostidagi tugmalar"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ O'qidim",
                    callback_data=f"rem_act:prayed:{prayer_type}:{prayer_date}"
                ),
                InlineKeyboardButton(
                    text="❌ Ulgurmadim",
                    callback_data=f"rem_act:missed:{prayer_type}:{prayer_date}"
                )
            ]
        ]
    )

def get_journal_keyboard(target_date: date, records: dict) -> InlineKeyboardMarkup:
    """Kundalik jurnal boshqaruvi va sanalar orasida harakat"""
    keyboard = []

    # Namozlarni o'zgartirish tugmalari
    prayers = [
        ("Bomdod", "bomdod"),
        ("Peshin", "peshin"),
        ("Asr", "asr"),
        ("Shom", "shom"),
        ("Xufton", "xufton")
    ]
    
    # Har bir namoz uchun bitta qator: Nom va holatni almashtirish tugmasi
    for label, p_type in prayers:
        current_status = records.get(p_type, "pending")
        if current_status == "prayed_on_time":
            badge = "✅ O'qildi"
        elif current_status == "qaza_recorded":
            badge = "❌ Qazo"
        else:
            badge = "⏳ Belgilanmagan"
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"{label}: {badge} (O'zgartirish)",
                callback_data=f"jnl_toggle:{p_type}:{target_date.isoformat()}"
            )
        ])

    # Sana navigatsiyasi
    prev_date = (target_date - timedelta(days=1)).isoformat()
    next_date = (target_date + timedelta(days=1)).isoformat()
    today_date = date.today().isoformat()

    nav_row = [
        InlineKeyboardButton(text="⬅️ Kecha", callback_data=f"jnl_date:{prev_date}"),
        InlineKeyboardButton(text="📅 Bugun", callback_data=f"jnl_date:{today_date}")
    ]
    if target_date < date.today():
        nav_row.append(InlineKeyboardButton(text="➡️ Keyingi kun", callback_data=f"jnl_date:{next_date}"))

    keyboard.append(nav_row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_qaza_keyboard(accounts: dict) -> InlineKeyboardMarkup:
    """Qazo o'qish (kamaytirish) va sozlash tugmalari"""
    keyboard = []
    
    prayers = [
        ("Bomdod", "bomdod"),
        ("Peshin", "peshin"),
        ("Asr", "asr"),
        ("Shom", "shom"),
        ("Xufton", "xufton"),
        ("Vitr", "vitr")
    ]

    for label, p_type in prayers:
        acc = accounts.get(p_type)
        rem = acc.remaining if acc else 0
        keyboard.append([
            InlineKeyboardButton(
                text=f"{label} ({rem} ta qolgan) ➖ 1 ta o'qidim",
                callback_data=f"qaza_sub:{p_type}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="✍️ Boshlang'ich qazo sonlarini kiritish",
            callback_data="qaza_set_initial_menu"
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_settings_keyboard(reminders_enabled: bool, weekly_enabled: bool) -> InlineKeyboardMarkup:
    """Foydalanuvchi sozlamalari"""
    rem_text = "🔔 Eslatmalar: Yoqilgan ✅" if reminders_enabled else "🔕 Eslatmalar: O'chirilgan ❌"
    rep_text = "📊 Haftalik sarhisob: Yoqilgan ✅" if weekly_enabled else "📊 Haftalik sarhisob: O'chirilgan ❌"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📍 Hududni o'zgartirish", callback_data="change_location")],
            [InlineKeyboardButton(text=rem_text, callback_data="toggle_setting:reminders")],
            [InlineKeyboardButton(text=rep_text, callback_data="toggle_setting:weekly_report")],
            [InlineKeyboardButton(text="🗑 Barcha hisoblarimni tozalash", callback_data="clear_my_data")]
        ]
    )

def get_ehson_keyboard(channel_url: str) -> InlineKeyboardMarkup:
    """Ehson bo'limi tugmalari"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Shaffof hisobot kanali", url=channel_url)]
        ]
    )
