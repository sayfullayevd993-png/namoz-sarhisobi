import asyncio
import logging
from datetime import datetime, date, timedelta
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from app.config import settings
from app.database.session import async_session_maker
from app.database.repository import (
    UserRepository, LocationRepository, NotificationRepository
)
from app.services.prayer_service import PrayerService
from app.services.report_service import ReportService
from app.bot.keyboards.inline import get_reminder_keyboard

logger = logging.getLogger(__name__)

PRAYER_DISPLAY = {
    "bomdod": ("Bomdod", "🌅"),
    "peshin": ("Peshin", "☀️"),
    "asr": ("Asr", "⛅"),
    "shom": ("Shom", "🌇"),
    "xufton": ("Xufton", "🌌")
}

async def check_and_send_prayer_reminders(bot: Bot):
    """
    Har daqiqada ishga tushib, ayni vaqtda kirgan namoz eslatmalarini yuboradi.
    """
    tz = pytz.timezone(settings.TIMEZONE)
    now = datetime.now(tz)
    current_time_str = now.strftime("%H:%M")
    today = now.date()

    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        loc_repo = LocationRepository(session)
        notif_repo = NotificationRepository(session)
        prayer_service = PrayerService(session)

        users = await user_repo.get_users_for_reminders()
        if not users:
            return

        # Hududlar bo'yicha namoz vaqtlarini keshda saqlash
        cached_pt = {}

        for user in users:
            loc_id = user.location_id
            if loc_id not in cached_pt:
                loc = await loc_repo.get_by_id(loc_id)
                if not loc:
                    continue
                pt = await prayer_service.get_or_fetch_prayer_times(loc, today)
                cached_pt[loc_id] = (loc, pt)

            loc, pt = cached_pt.get(loc_id, (None, None))
            if not pt:
                continue

            # Har bir namoz vaqtini ayni daqiqa bilan solishtiramiz
            prayer_map = {
                "bomdod": pt.bomdod,
                "peshin": pt.peshin,
                "asr": pt.asr,
                "shom": pt.shom,
                "xufton": pt.xufton
            }

            for p_type, p_time in prayer_map.items():
                if p_time == current_time_str:
                    # Dublikat tekshiruvi
                    already_sent = await notif_repo.is_sent_or_pending(user.id, today, p_type)
                    if already_sent:
                        continue

                    # Eslatma matni va tugmalar
                    p_name, icon = PRAYER_DISPLAY.get(p_type, (p_type.capitalize(), "🕌"))
                    msg_text = (
                        f"{icon} <b>{p_name} namozi vaqti kirdi!</b>\n"
                        f"📍 Hudud: {loc.district_name}\n"
                        f"⏰ Vaqt: {p_time}\n\n"
                        f"<i>Namozni o'z vaqtida ado etish ulug' fazilatdir. Ado etgach, quyidagi tugmani bosing:</i>"
                    )

                    try:
                        await bot.send_message(
                            chat_id=user.telegram_id,
                            text=msg_text,
                            reply_markup=get_reminder_keyboard(p_type, today.isoformat())
                        )
                        await notif_repo.record_job(user.id, today, p_type, p_time, status="sent")
                        await asyncio.sleep(0.04)
                    except TelegramAPIError as e:
                        logger.warning(f"Foydalanuvchiga ({user.telegram_id}) xabar yuborilmadi: {e}")
                        await notif_repo.record_job(user.id, today, p_type, p_time, status="failed")

        await session.commit()

async def send_weekly_reports(bot: Bot):
    """
    Yakshanba soat 20:00 da haftalik hisobot yuborish
    """
    tz = pytz.timezone(settings.TIMEZONE)
    today = datetime.now(tz).date()
    week_start = today - timedelta(days=6)

    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        report_service = ReportService(session)

        users = await user_repo.get_all_active_users()
        for user in users:
            if not user.weekly_report_enabled:
                continue

            stats = await report_service.get_period_stats(user.id, week_start, today)
            text = report_service.format_report_message(stats, title="Haftalik sarhisob (Yakshanba)")

            try:
                await bot.send_message(chat_id=user.telegram_id, text=text)
                await asyncio.sleep(0.04)
            except TelegramAPIError:
                pass

def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    tz = pytz.timezone(settings.TIMEZONE)
    scheduler = AsyncIOScheduler(timezone=tz)

    # Har daqiqada eslatmalarni tekshirish
    scheduler.add_job(
        check_and_send_prayer_reminders,
        "cron",
        second=0,
        args=[bot],
        id="prayer_reminders_job",
        replace_existing=True
    )

    # Har yakshanba soat 20:00 da haftalik hisobot
    scheduler.add_job(
        send_weekly_reports,
        "cron",
        day_of_week="sun",
        hour=20,
        minute=0,
        args=[bot],
        id="weekly_reports_job",
        replace_existing=True
    )

    return scheduler
