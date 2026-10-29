# Namoz Sarhisobi — Telegram Bot (MVP)

Namoz vaqtlarini aniqlash, kundalik namozlarni qayd qilib borish va qazo namozlari hisobini tartibli yuritish uchun mo'ljallangan Telegram bot.

---

## 🕌 Asosiy imkoniyatlar

1. **Hudud bo'yicha namoz vaqtlari:**
   - O'zbekistonning barcha viloyat va tumanlari (inline tugmalar orqali oson tanlash).
   - [namoz-vaqti.uz](https://namoz-vaqti.uz) API orqali O'zbekiston Musulmonlari Idorasi rasmiy taqvimi bilan muvofiqlashtirilgan vaqtlar.
   - Kunlik 5 mahal farz namozlari hamda Quyosh chiqish vaqti.

2. **Kundalik namoz jurnali:**
   - Har bir namoz holati: `✅ O'qildi`, `❌ Qazo (Ulgurmagan)`, `⏳ Belgilanmagan`.
   - Kunlar bo'yicha navigatsiya: Kecha, Bugun va o'tgan sanalar.
   - Tugma orqali holatni bir zumda o'zgartirish.

3. **Qazo namozlari hisob-kitobi:**
   - Formula: `Qolgan qazo = Boshlang'ich qazo + Qo'shilgan qazo - Ado etilgan qazo`.
   - 6 ta namoz turi: Bomdod, Peshin, Asr, Shom, Xufton va Vitr vojib.
   - **Xufton va Vitr bog'liqligi:** Xufton qazo bo'lganda (yoki ado etilganda), unga mos ravishda Vitr namozi ham birgalikda hisoblanadi.
   - Boshlang'ich qazolarni istalgan paytda kiritish va tahrirlash.
   - Har bir o'qilgan qazo uchun `➖ 1 ta o'qidim` tugmasi.

4. **Avtomatik eslatmalar (Scheduler):**
   - Namoz vaqti kirishi bilan foydalanuvchiga inline tugmali eslatma yuboriladi:
     - `[ ✅ O'qidim ]` -> Jurnalda vaqtida o'qildi deb belgilanadi.
     - `[ ❌ Ulgurmadim ]` -> Jurnalda qayd qilinadi va avtomatik ravishda qazo hisobiga qo'shiladi.
   - Qayta ishga tushganda va scheduler sikllarida dublikat xabar yuborilmasligi to'liq ta'minlangan.

5. **Haftalik va oylik sarhisob:**
   - So'nggi 7 kun va 30 kun bo'yicha foizlar va aniq statistikalar.
   - Har yakshanba soat 20:00 da avtomatik haftalik hisobot.

6. **Admin boshqaruv paneli:**
   - Jami, faol va hudud tanlagan foydalanuvchilar statistikasi.
   - Barcha foydalanuvchilarga xavfsiz ommaviy xabar yuborish (Broadcast).
   - Tizim va API holati monitoringi.

7. **Ehson bo'limi:**
   - Loyiha rivoji uchun shaffof ehson bo'limi va hisobot kanali havolasi.

---

## 🛠 Texnologiyalar

- **Til:** Python 3.12+
- **Bot freymvorki:** `aiogram 3.x`
- **Ma'lumotlar bazasi:** `SQLAlchemy 2.x`, `PostgreSQL` (production) / `aiosqlite` (lokal/test)
- **Vaqt va rejalashtirish:** `APScheduler`, `pytz` (`Asia/Tashkent`)
- **HTTP mijoz:** `httpx`
- **Konteynerlash:** `Docker`, `Docker Compose`

---

## 🚀 Ishga tushirish yo'riqnomasi

### 1. Sozlamalarni kiritish
`.env.example` faylidan nusxa olib `.env` yarating:
```bash
cp .env.example .env
```
`.env` faylini oching va bot tokeningizni kiriting:
```ini
BOT_TOKEN=1234567890:ABCdef...
ADMIN_IDS=123456789
DATABASE_URL=sqlite+aiosqlite:///data/namoz.db
TIMEZONE=Asia/Tashkent
```

### 2. Lokal ishga tushirish (Python venv bilan)
```bash
# Virtual muhitni faollashtirish (Windows)
.venv\Scripts\activate

# Botni yurgizish
python -m app.main
```

### 3. Docker Compose orqali ishga tushirish
```bash
docker compose up -d --build
```

### 4. Testlarni yurgizish
```bash
pytest tests/ -v
```

---

## ☁️ Railway.app platformasiga deploy qilish

### 1-qadam: GitHub repozitoriy yaratish
1. [github.com](https://github.com) da yangi private yoki public repozitoriy oching.
2. Loyihani GitHub'ga yuklang:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for Railway deploy"
   git branch -M main
   git remote add origin https://github.com/USERNAME/REPO_NAME.git
   git push -u origin main
   ```

### 2-qadam: Railway'da PostgreSQL yaratish
1. [railway.app](https://railway.app) ga kiring va **New Project** bosing.
2. **Provision PostgreSQL** tugmasini bosing (1-bosqichda avtomatik bepul/managed PostgreSQL ishga tushadi).

### 3-qadam: Bot servisini ulash
1. Loyiha ekranida **+ Create** -> **GitHub Repo** ni bosing va repozitoriyingizni tanlang.
2. Bot servisi sozlamalariga (`Variables`) kiring va quyidagi o'zgaruvchilarni kiriting:
   - `BOT_TOKEN` = *Sizning Telegram bot tokeningiz*
   - `ADMIN_IDS` = *Sizning Telegram ID raqamingiz*
   - `DATABASE_URL` = `${{Postgres.DATABASE_URL}}` *(yoki PostgreSQL servisi manzilini bog'lang)*
   - `TIMEZONE` = `Asia/Tashkent`
   - `NAMOZ_API_BASE_URL` = `https://namoz-vaqti.uz/index.php`

### 4-qadam: Ishga tushirish
Railway avtomatik tarzda `Dockerfile` orqali botni quradi, jadvallarni avtomatik yaratadi va 24/7 rejimda polling orqali ishga tushiradi!
Loglarni **Deployments** -> **View Logs** bo'limida kuzatishingiz mumkin.
