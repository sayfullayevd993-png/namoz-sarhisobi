from datetime import datetime, date, timezone
from sqlalchemy import (
    Column, Integer, BigInteger, String, Boolean, Date, DateTime,
    ForeignKey, UniqueConstraint, Text, func
)
from sqlalchemy.orm import relationship
from app.database.base import Base

def utc_now():
    return datetime.now(timezone.utc)

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    region_name = Column(String(100), nullable=False)     # Masalan: Toshkent viloyati
    district_name = Column(String(100), nullable=False)   # Masalan: Angren shahri
    slug = Column(String(100), unique=True, nullable=False, index=True) # API uchun slug: angren
    timezone = Column(String(50), default="Asia/Tashkent", nullable=False)
    created_at = Column(DateTime, default=utc_now)

    users = relationship("User", back_populates="location")
    prayer_times = relationship("PrayerTime", back_populates="location", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Location {self.district_name} ({self.slug})>"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    full_name = Column(String(200), nullable=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    timezone = Column(String(50), default="Asia/Tashkent", nullable=False)
    
    # Sozlamalar
    reminders_enabled = Column(Boolean, default=True, nullable=False)
    weekly_report_enabled = Column(Boolean, default=True, nullable=False)
    monthly_report_enabled = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=utc_now, nullable=False)
    blocked_at = Column(DateTime, nullable=True)

    location = relationship("Location", back_populates="users")
    prayer_records = relationship("PrayerRecord", back_populates="user", cascade="all, delete-orphan")
    qaza_accounts = relationship("QazaAccount", back_populates="user", cascade="all, delete-orphan")
    qaza_events = relationship("QazaEvent", back_populates="user", cascade="all, delete-orphan")
    notification_jobs = relationship("NotificationJob", back_populates="user", cascade="all, delete-orphan")


class PrayerTime(Base):
    __tablename__ = "prayer_times"

    id = Column(Integer, primary_key=True, autoincrement=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False, index=True)
    prayer_date = Column(Date, nullable=False, index=True)
    bomdod = Column(String(10), nullable=False)
    quyosh = Column(String(10), nullable=False)
    peshin = Column(String(10), nullable=False)
    asr = Column(String(10), nullable=False)
    shom = Column(String(10), nullable=False)
    xufton = Column(String(10), nullable=False)
    source = Column(String(100), default="namoz-vaqti.uz")
    created_at = Column(DateTime, default=utc_now)

    location = relationship("Location", back_populates="prayer_times")

    __table_args__ = (
        UniqueConstraint("location_id", "prayer_date", name="uq_location_prayer_date"),
    )


class PrayerRecord(Base):
    __tablename__ = "prayer_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    prayer_date = Column(Date, nullable=False, index=True)
    prayer_type = Column(String(20), nullable=False) # bomdod, peshin, asr, shom, xufton
    status = Column(String(30), nullable=False, default="pending") # prayed_on_time, qaza_recorded, pending
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="prayer_records")

    __table_args__ = (
        UniqueConstraint("user_id", "prayer_date", "prayer_type", name="uq_user_date_prayer"),
    )


class QazaAccount(Base):
    __tablename__ = "qaza_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    prayer_type = Column(String(20), nullable=False) # bomdod, peshin, asr, shom, xufton, vitr
    initial_count = Column(Integer, default=0, nullable=False)
    added_count = Column(Integer, default=0, nullable=False)
    completed_count = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="qaza_accounts")

    __table_args__ = (
        UniqueConstraint("user_id", "prayer_type", name="uq_user_qaza_type"),
    )

    @property
    def remaining(self) -> int:
        total = (self.initial_count + self.added_count) - self.completed_count
        return max(0, total)


class QazaEvent(Base):
    __tablename__ = "qaza_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    prayer_type = Column(String(20), nullable=False)
    event_type = Column(String(30), nullable=False) # set_initial, missed, completed, reset
    quantity = Column(Integer, nullable=False, default=1)
    event_date = Column(Date, nullable=False, default=date.today)
    source = Column(String(50), nullable=False, default="manual") # 'button_ulgurmadim', 'manual', 'journal'
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="qaza_events")


class NotificationJob(Base):
    __tablename__ = "notification_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    prayer_type = Column(String(20), nullable=False)
    prayer_date = Column(Date, nullable=False, index=True)
    scheduled_time = Column(String(10), nullable=False) # e.g. "05:15"
    status = Column(String(20), nullable=False, default="pending") # pending, sent, failed, skipped
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="notification_jobs")

    __table_args__ = (
        UniqueConstraint("user_id", "prayer_date", "prayer_type", name="uq_user_date_prayer_notif"),
    )


class ReportDelivery(Base):
    __tablename__ = "report_deliveries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    report_type = Column(String(20), nullable=False) # weekly, monthly
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    sent_at = Column(DateTime, default=utc_now)
    status = Column(String(20), default="sent")

    __table_args__ = (
        UniqueConstraint("user_id", "report_type", "period_start", "period_end", name="uq_user_report_period"),
    )


class BotSetting(Base):
    __tablename__ = "bot_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(BigInteger, nullable=False)
    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)


class BroadcastJob(Base):
    __tablename__ = "broadcast_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_text = Column(Text, nullable=False)
    total_users = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    status = Column(String(30), default="pending") # pending, in_progress, completed, failed
    created_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, nullable=True)
