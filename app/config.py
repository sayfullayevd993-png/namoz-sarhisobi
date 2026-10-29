import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    BOT_TOKEN: str = ""
    ADMIN_IDS: str = ""
    DATABASE_URL: str = ""
    DB_PATH: str = ""
    NAMOZ_API_BASE_URL: str = "https://namoz-vaqti.uz/index.php"
    
    # Ehson bo'limi sozlamalari
    EHSON_ENABLED: bool = True
    EHSON_CHANNEL_URL: str = "https://t.me/namoz_sarhisobi_ehson"
    EHSON_TEXT: str = (
        "Loyiha namoz vaqtlarini o'z vaqtida ado etish, kundalik hisob-kitobni yuritish "
        "va musulmonlarga manfaatli bo'lishi uchun xolis niyatda ishlab chiqildi.\n\n"
        "Ehson mablag'lari server to'lovlari, API qo'llab-quvvatlash va yangi qulayliklarni "
        "ishlab chiqishga sarflanadi. Shaffof hisobot bilan kanalimizda tanishishingiz mumkin."
    )
    
    # Majburiy a'zolik (ixtiyoriy)
    REQUIRED_CHANNEL_ID: str = ""
    REQUIRED_CHANNEL_URL: str = ""
    
    TIMEZONE: str = "Asia/Tashkent"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def async_database_url(self) -> str:
        """
        Railway yoki lokal muhitga qarab to'g'ri async database URL qaytaradi.
        PostgreSQL bo'lsa 'postgresql+asyncpg://', SQLite bo'lsa 'sqlite+aiosqlite:///'
        """
        url = self.DATABASE_URL.strip() if self.DATABASE_URL else ""

        # Agar DB_PATH ko'rsatilgan bo'lsa va DATABASE_URL bo'sh bo'lsa (masalan Railway Volume)
        if not url and self.DB_PATH:
            return f"sqlite+aiosqlite:///{self.DB_PATH.strip()}"

        # Agar DATABASE_URL bo'sh bo'lsa, default lokal SQLite
        if not url:
            default_sqlite_path = (BASE_DIR / "data" / "namoz.db").as_posix()
            return f"sqlite+aiosqlite:///{default_sqlite_path}"

        # Railway PostgreSQL avtomatik tarzda 'postgresql://' yoki 'postgres://' beradi
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

        return url

    @property
    def admin_id_list(self) -> List[int]:
        if not self.ADMIN_IDS:
            return []
        ids = []
        for x in self.ADMIN_IDS.split(","):
            x = x.strip()
            if x.isdigit():
                ids.append(int(x))
        return ids

settings = Settings()
