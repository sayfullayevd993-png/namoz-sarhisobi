import pytest
import pytest_asyncio
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.repository import (
    UserRepository, LocationRepository, PrayerRecordRepository,
    QazaRepository, NotificationRepository
)
from app.services.journal_service import JournalService
from app.services.qaza_service import QazaService
from app.services.report_service import ReportService
from app.utils.regions import find_district_by_slug, REGIONS_DATA

@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as sess:
        yield sess
        await sess.close()
    await engine.dispose()

def test_region_data_and_slug_lookup():
    # Toshkent shahri tekshiruvi
    info = find_district_by_slug("chilonzor")
    assert info is not None
    assert info["district_name"] == "Chilonzor tumani"
    assert info["region_name"] == "Toshkent shahri"

    # Samarqand tekshiruvi
    sam_info = find_district_by_slug("samarqand-shahri")
    assert sam_info is not None
    assert "Samarqand" in sam_info["region_name"]

@pytest.mark.asyncio
async def test_user_creation_and_qaza_initialization(session: AsyncSession):
    user_repo = UserRepository(session)
    user = await user_repo.create_or_update(
        telegram_id=999888777,
        username="test_user",
        full_name="Test Foydalanuvchi"
    )
    await session.commit()

    assert user.id is not None
    assert user.telegram_id == 999888777

    # Qaza hisoblar tekshiruvi (6 ta: bomdod, peshin, asr, shom, xufton, vitr)
    qaza_repo = QazaRepository(session)
    accounts = await qaza_repo.get_accounts(user.id)
    assert len(accounts) == 6
    assert "vitr" in accounts
    assert "xufton" in accounts
    assert accounts["bomdod"].remaining == 0

@pytest.mark.asyncio
async def test_qaza_formula_and_xufton_vitr_linking(session: AsyncSession):
    user_repo = UserRepository(session)
    user = await user_repo.create_or_update(telegram_id=111222333)
    await session.commit()

    qaza_service = QazaService(session)

    # 1. Boshlang'ich qazo kiritish
    await qaza_service.set_initial(user.id, "bomdod", 10)
    await session.commit()

    accs = await qaza_service.get_qaza_summary(user.id)
    assert accs["bomdod"].remaining == 10

    # 2. "Ulgurmadim" orqali Xufton qazo bo'ldi -> Xufton va Vitr birga oshishi kerak
    await qaza_service.add_qaza(user.id, "xufton", 1, source="button_ulgurmadim")
    await session.commit()

    accs = await qaza_service.get_qaza_summary(user.id)
    assert accs["xufton"].remaining == 1
    assert accs["vitr"].remaining == 1

    # 3. Xufton qazosini ado etish -> Xufton va Vitr birga kamayishi kerak
    await qaza_service.complete_qaza(user.id, "xufton", 1)
    await session.commit()

    accs = await qaza_service.get_qaza_summary(user.id)
    assert accs["xufton"].remaining == 0
    assert accs["vitr"].remaining == 0
    assert accs["xufton"].completed_count == 1
    assert accs["vitr"].completed_count == 1

@pytest.mark.asyncio
async def test_journal_marking_and_qaza_integration(session: AsyncSession):
    user_repo = UserRepository(session)
    user = await user_repo.create_or_update(telegram_id=444555666)
    await session.commit()

    journal_service = JournalService(session)
    qaza_service = QazaService(session)
    today = date.today()

    # Bomdodni vaqtida o'qildi deb belgilash
    await journal_service.mark_prayer(user.id, today, "bomdod", "prayed_on_time")
    # Peshinni qazo deb belgilash (Ulgurmadim)
    await journal_service.mark_prayer(user.id, today, "peshin", "qaza_recorded")
    await session.commit()

    records = await journal_service.get_daily_journal(user.id, today)
    assert records["bomdod"] == "prayed_on_time"
    assert records["peshin"] == "qaza_recorded"
    assert records["asr"] == "pending"

    # Peshin qazosi avtomatik 1 ta bo'lishi kerak
    accs = await qaza_service.get_qaza_summary(user.id)
    assert accs["peshin"].remaining == 1

@pytest.mark.asyncio
async def test_duplicate_notification_prevention(session: AsyncSession):
    user_repo = UserRepository(session)
    user = await user_repo.create_or_update(telegram_id=777888999)
    await session.commit()

    notif_repo = NotificationRepository(session)
    today = date.today()

    # Hali yuborilmagan
    assert await notif_repo.is_sent_or_pending(user.id, today, "bomdod") is False

    # Yuborildi deb yozish
    await notif_repo.record_job(user.id, today, "bomdod", "05:30", status="sent")
    await session.commit()

    # Endi tekshirganda dublikat oldi olinadi
    assert await notif_repo.is_sent_or_pending(user.id, today, "bomdod") is True

@pytest.mark.asyncio
async def test_report_service(session: AsyncSession):
    user_repo = UserRepository(session)
    user = await user_repo.create_or_update(telegram_id=123123123)
    await session.commit()

    journal_service = JournalService(session)
    report_service = ReportService(session)
    today = date.today()

    await journal_service.mark_prayer(user.id, today, "bomdod", "prayed_on_time")
    await journal_service.mark_prayer(user.id, today, "peshin", "prayed_on_time")
    await journal_service.mark_prayer(user.id, today, "asr", "qaza_recorded")
    await session.commit()

    stats = await report_service.get_period_stats(user.id, today, today)
    assert stats["prayed_on_time"] == 2
    assert stats["qaza_recorded"] == 1
    assert stats["expected_total"] == 5
    assert stats["total_days"] == 1

    formatted = report_service.format_report_message(stats)
    assert "40.0%" in formatted
    assert "<b>Qazo qilingan namozlar:</b> 1 ta" in formatted

@pytest.mark.asyncio
async def test_settings_repository_ehson(session: AsyncSession):
    from app.database.repository import SettingsRepository

    repo = SettingsRepository(session)

    # 1. Boshlang'ich default qiymatlar
    cfg = await repo.get_ehson_settings(
        fallback_enabled=True,
        fallback_text="Standart matn",
        fallback_channel="https://t.me/default_channel"
    )
    assert cfg["enabled"] is True
    assert cfg["text"] == "Standart matn"
    assert cfg["channel_url"] == "https://t.me/default_channel"

    # 2. Yangi matn kiritish
    await repo.set_ehson_text("Yangi xayriya matni")
    # 3. Yangi kanal kiritish
    await repo.set_ehson_channel("https://t.me/yangi_ehson")
    # 4. Holatni o'chirish
    new_status = await repo.toggle_ehson(cfg["enabled"])
    assert new_status is False
    await session.commit()

    # 5. Yangilangan qiymatlarni tekshirish
    updated_cfg = await repo.get_ehson_settings(
        fallback_enabled=True,
        fallback_text="Standart matn",
        fallback_channel="https://t.me/default_channel"
    )
    assert updated_cfg["enabled"] is False
    assert updated_cfg["text"] == "Yangi xayriya matni"
    assert updated_cfg["channel_url"] == "https://t.me/yangi_ehson"

def test_database_url_resolution_for_railway():
    from app.config import Settings

    # 1. Railway PostgreSQL 'postgres://' format
    s1 = Settings(DATABASE_URL="postgres://user:pass@roundhouse.proxy.rlwy.net:1234/railway")
    assert s1.async_database_url == "postgresql+asyncpg://user:pass@roundhouse.proxy.rlwy.net:1234/railway"

    # 2. Standard 'postgresql://' format
    s2 = Settings(DATABASE_URL="postgresql://user:pass@localhost:5432/namoz")
    assert s2.async_database_url == "postgresql+asyncpg://user:pass@localhost:5432/namoz"

    # 3. Railway Persistent Volume DB_PATH
    s3 = Settings(DATABASE_URL="", DB_PATH="/data/namoz.db")
    assert s3.async_database_url == "sqlite+aiosqlite:////data/namoz.db"

    # 4. Default fallback to local SQLite
    s4 = Settings(DATABASE_URL="", DB_PATH="")
    assert s4.async_database_url.startswith("sqlite+aiosqlite:///")

