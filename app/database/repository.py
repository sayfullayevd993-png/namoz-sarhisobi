from datetime import date, datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import select, update, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import (
    User, Location, PrayerTime, PrayerRecord, QazaAccount,
    QazaEvent, NotificationJob, ReportDelivery, BotSetting, AuditLog
)

def utc_now():
    return datetime.now(timezone.utc)

PRAYER_NAMES = ["bomdod", "peshin", "asr", "shom", "xufton"]
ALL_QAZA_TYPES = ["bomdod", "peshin", "asr", "shom", "xufton", "vitr"]

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update(self, telegram_id: int, username: Optional[str] = None, full_name: Optional[str] = None) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
                created_at=utc_now()
            )
            self.session.add(user)
            await self.session.flush()

            # Boshlang'ich qazo hisoblarini yaratish
            for p_type in ALL_QAZA_TYPES:
                qaza_acc = QazaAccount(
                    user_id=user.id,
                    prayer_type=p_type,
                    initial_count=0,
                    added_count=0,
                    completed_count=0
                )
                self.session.add(qaza_acc)
            await self.session.flush()
        else:
            user.username = username
            user.full_name = full_name
            await self.session.flush()

        return user

    async def set_location(self, user_id: int, location_id: int):
        stmt = update(User).where(User.id == user_id).values(location_id=location_id)
        await self.session.execute(stmt)
        await self.session.flush()

    async def get_all_active_users(self) -> List[User]:
        stmt = select(User).where(User.blocked_at.is_(None))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_users_for_reminders(self) -> List[User]:
        stmt = select(User).where(
            and_(
                User.blocked_at.is_(None),
                User.reminders_enabled == True,
                User.location_id.is_not(None)
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_stats(self) -> Dict[str, int]:
        total = await self.session.scalar(select(func.count(User.id)))
        active = await self.session.scalar(select(func.count(User.id)).where(User.blocked_at.is_(None)))
        with_location = await self.session.scalar(select(func.count(User.id)).where(User.location_id.is_not(None)))
        blocked = await self.session.scalar(select(func.count(User.id)).where(User.blocked_at.is_not(None)))
        return {
            "total": total or 0,
            "active": active or 0,
            "with_location": with_location or 0,
            "blocked": blocked or 0
        }


class LocationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, loc_id: int) -> Optional[Location]:
        stmt = select(Location).where(Location.id == loc_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(self, region_name: str, district_name: str, slug: str) -> Location:
        stmt = select(Location).where(Location.slug == slug)
        result = await self.session.execute(stmt)
        loc = result.scalar_one_or_none()
        if not loc:
            loc = Location(
                region_name=region_name,
                district_name=district_name,
                slug=slug
            )
            self.session.add(loc)
            await self.session.flush()
        return loc


class PrayerTimeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_prayer_time(self, location_id: int, target_date: date) -> Optional[PrayerTime]:
        stmt = select(PrayerTime).where(
            and_(
                PrayerTime.location_id == location_id,
                PrayerTime.prayer_date == target_date
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def save_prayer_time(self, location_id: int, target_date: date, times: Dict[str, str]) -> PrayerTime:
        pt = await self.get_prayer_time(location_id, target_date)
        if not pt:
            pt = PrayerTime(
                location_id=location_id,
                prayer_date=target_date,
                bomdod=times["bomdod"],
                quyosh=times["quyosh"],
                peshin=times["peshin"],
                asr=times["asr"],
                shom=times["shom"],
                xufton=times["xufton"],
                source="namoz-vaqti.uz"
            )
            self.session.add(pt)
        else:
            pt.bomdod = times["bomdod"]
            pt.quyosh = times["quyosh"]
            pt.peshin = times["peshin"]
            pt.asr = times["asr"]
            pt.shom = times["shom"]
            pt.xufton = times["xufton"]
        await self.session.flush()
        return pt


class PrayerRecordRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_record(self, user_id: int, target_date: date, prayer_type: str) -> Optional[PrayerRecord]:
        stmt = select(PrayerRecord).where(
            and_(
                PrayerRecord.user_id == user_id,
                PrayerRecord.prayer_date == target_date,
                PrayerRecord.prayer_type == prayer_type
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_daily_records(self, user_id: int, target_date: date) -> Dict[str, str]:
        stmt = select(PrayerRecord).where(
            and_(
                PrayerRecord.user_id == user_id,
                PrayerRecord.prayer_date == target_date
            )
        )
        result = await self.session.execute(stmt)
        records = result.scalars().all()
        status_map = {r.prayer_type: r.status for r in records}
        return {p: status_map.get(p, "pending") for p in PRAYER_NAMES}

    async def set_record_status(self, user_id: int, target_date: date, prayer_type: str, status: str) -> PrayerRecord:
        record = await self.get_record(user_id, target_date, prayer_type)
        if not record:
            record = PrayerRecord(
                user_id=user_id,
                prayer_date=target_date,
                prayer_type=prayer_type,
                status=status
            )
            self.session.add(record)
        else:
            record.status = status
            record.updated_at = utc_now()
        await self.session.flush()
        return record


class QazaRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_accounts(self, user_id: int) -> Dict[str, QazaAccount]:
        stmt = select(QazaAccount).where(QazaAccount.user_id == user_id)
        result = await self.session.execute(stmt)
        accounts = {acc.prayer_type: acc for acc in result.scalars().all()}
        
        # Agar qaysidir tur mavjud bo'lmasa, yaratish
        for p_type in ALL_QAZA_TYPES:
            if p_type not in accounts:
                new_acc = QazaAccount(user_id=user_id, prayer_type=p_type)
                self.session.add(new_acc)
                accounts[p_type] = new_acc
        await self.session.flush()
        return accounts

    async def add_missed_prayer(self, user_id: int, prayer_type: str, qty: int = 1, source: str = "button_ulgurmadim"):
        """
        Namoz qazo bo'lganda (masalan, Ulgurmadim bosilganda) qazo sonini oshirish.
        Qoida: Agar Xufton bo'lsa, Vitr ham birga oshiriladi (Foydalanuvchi talabi bo'yicha).
        """
        targets = [prayer_type]
        if prayer_type == "xufton":
            targets.append("vitr")

        for target in targets:
            stmt = select(QazaAccount).where(
                and_(QazaAccount.user_id == user_id, QazaAccount.prayer_type == target)
            )
            result = await self.session.execute(stmt)
            acc = result.scalar_one_or_none()
            if not acc:
                acc = QazaAccount(user_id=user_id, prayer_type=target, initial_count=0, added_count=qty, completed_count=0)
                self.session.add(acc)
            else:
                acc.added_count += qty
                acc.updated_at = utc_now()

            # Hodisani yozish
            event = QazaEvent(
                user_id=user_id,
                prayer_type=target,
                event_type="missed",
                quantity=qty,
                source=source
            )
            self.session.add(event)
        await self.session.flush()

    async def complete_prayer_qaza(self, user_id: int, prayer_type: str, qty: int = 1) -> bool:
        """
        Qazo ado etilganda sonni kamaytirish.
        Qoida: Xufton ado etilsa, Vitr ham birga hisoblanishi mumkin.
        """
        targets = [prayer_type]
        if prayer_type == "xufton":
            targets.append("vitr")

        for target in targets:
            stmt = select(QazaAccount).where(
                and_(QazaAccount.user_id == user_id, QazaAccount.prayer_type == target)
            )
            result = await self.session.execute(stmt)
            acc = result.scalar_one_or_none()
            if acc and acc.remaining > 0:
                acc.completed_count += qty
                acc.updated_at = utc_now()
                event = QazaEvent(
                    user_id=user_id,
                    prayer_type=target,
                    event_type="completed",
                    quantity=qty,
                    source="manual"
                )
                self.session.add(event)
        await self.session.flush()
        return True

    async def set_initial_count(self, user_id: int, prayer_type: str, count: int):
        stmt = select(QazaAccount).where(
            and_(QazaAccount.user_id == user_id, QazaAccount.prayer_type == prayer_type)
        )
        result = await self.session.execute(stmt)
        acc = result.scalar_one_or_none()
        if not acc:
            acc = QazaAccount(user_id=user_id, prayer_type=prayer_type, initial_count=count)
            self.session.add(acc)
        else:
            acc.initial_count = max(0, count)
            acc.updated_at = utc_now()

        event = QazaEvent(
            user_id=user_id,
            prayer_type=prayer_type,
            event_type="set_initial",
            quantity=count,
            source="manual"
        )
        self.session.add(event)
        await self.session.flush()


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def is_sent_or_pending(self, user_id: int, prayer_date: date, prayer_type: str) -> bool:
        stmt = select(NotificationJob).where(
            and_(
                NotificationJob.user_id == user_id,
                NotificationJob.prayer_date == prayer_date,
                NotificationJob.prayer_type == prayer_type
            )
        )
        result = await self.session.execute(stmt)
        job = result.scalar_one_or_none()
        return job is not None

    async def record_job(self, user_id: int, prayer_date: date, prayer_type: str, scheduled_time: str, status: str = "sent"):
        job = NotificationJob(
            user_id=user_id,
            prayer_date=prayer_date,
            prayer_type=prayer_type,
            scheduled_time=scheduled_time,
            status=status,
            sent_at=utc_now() if status == "sent" else None
        )
        self.session.add(job)
        await self.session.flush()


class SettingsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        stmt = select(BotSetting.value).where(BotSetting.key == key)
        result = await self.session.execute(stmt)
        val = result.scalar_one_or_none()
        return val if val is not None else default

    async def set_value(self, key: str, value: str, description: Optional[str] = None):
        stmt = select(BotSetting).where(BotSetting.key == key)
        result = await self.session.execute(stmt)
        setting = result.scalar_one_or_none()
        if not setting:
            setting = BotSetting(key=key, value=value, description=description)
            self.session.add(setting)
        else:
            setting.value = value
            if description:
                setting.description = description
            setting.updated_at = utc_now()
        await self.session.flush()

    async def get_ehson_settings(self, fallback_enabled: bool, fallback_text: str, fallback_channel: str) -> Dict[str, Any]:
        enabled_val = await self.get_value("ehson_enabled", "true" if fallback_enabled else "false")
        text_val = await self.get_value("ehson_text", fallback_text)
        channel_val = await self.get_value("ehson_channel_url", fallback_channel)
        return {
            "enabled": enabled_val.lower() == "true",
            "text": text_val,
            "channel_url": channel_val
        }

    async def set_ehson_text(self, text: str):
        await self.set_value("ehson_text", text, description="Ehson bo'limi matni")

    async def set_ehson_channel(self, url: str):
        await self.set_value("ehson_channel_url", url, description="Ehson hisobot kanali havolasi")

    async def toggle_ehson(self, current_status: bool) -> bool:
        new_status = not current_status
        await self.set_value("ehson_enabled", "true" if new_status else "false", description="Ehson bo'limi faolligi")
        return new_status

