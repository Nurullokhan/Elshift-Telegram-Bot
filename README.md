# 🏢 Elshift Telegram Bot

**Elshift Telegram Bot** — bu «Elshift» kompaniyasi uchun ish o'rganuvchilar (shogirdlar), tajribali ustalar hamda roverchilarni ro'yxatdan o'tkazish, arizalarni avtomatlashtirilgan tarzda qabul qilish, ularni Google Sheets jadvali bilan integratsiya qilish hamda kompaniya rahbariyati va adminlar guruhiga yo'naltirish uchun mo'ljallangan zamonaviy bot tizimi.

---

## 🚀 Asosiy Imkoniyatlar va Xususiyatlar

- ✅ **Ko'p bosqichli FSM anketalar**:
  - 👨‍🎓 **Ish o'rganuvchi** anketasi (Yosh, telefon, manzil, avvalgi ish va oylik, matematika bilimi ovozli xabarda, baland joyda ishlash, maqsad va hk).
  - 👷 **Usta** anketasi (Mutaxassislik, tajriba, jamoa boshqaruvi, portfolio rasm/video/havola, kutayotgan daromad).
  - 👨‍🎓 **Shogird (Roverchi)** anketasi (Kompyuter dasturlari bilimi, manzil va ish boshlash muddati).
- ✅ **Ovozli va Media fayllar bilan ishlash**: Nomzodlarning ovozli javoblari, portfolio rasmlari va videolari adminlar guruhiga yuboriladi va to'g'ridan-to'g'ri havolalar anketaga biriktiriladi.
- ✅ **Google Sheets integratsiyasi**: Barcha arizalar Google Apps Script Web App orqali real vaqt rejimida tegishli jadvallarga yozib boriladi.
- ✅ **Guruh va Adminlarga xabarnoma**: Bir nechta adminlar va Telegram guruhlariga xabarlarni xavfsiz va sinxron yo'naltirish.
- ✅ **Universal Bekor qilish va Orqaga**: Istalgan bosqichda `/cancel` yoki «Bekor qilish» orqali anketani to'xtatish va asosiy menyuga qaytish imkoniyati.

---

## 📁 Loyiha Strukturasi

```text
Elshift-Telegram-Bot/
├── .github/workflows/deploy.yml   # Railway avtomatik deploy workflow
├── data/
│   └── regions.py                 # Viloyat va tumanlar ma'lumotlar bazasi
├── handler/
│   ├── start_handler.py           # /start buyrug'i uchun router handler
│   └── common_handlers.py         # Umumiy buyruqlar va xizmatlar
├── keyboards/
│   ├── texts.py                   # Barcha tugma matnlari va konstantalar
│   ├── main_menu.py               # Asosiy menyu va bo'sh ish o'rinlari klaviaturalari
│   ├── form_keyboards.py          # Anketalar uchun yordamchi tugmalar (telefon, ha/yo'q)
│   ├── inline_keyboards.py        # Ijtimoiy tarmoqlar havolalari
│   └── region_keyboards.py        # Dinamik tuman tanlash klaviaturasi
├── states/
│   ├── apprentice_state.py        # Ish o'rganuvchi FSM holatlari
│   ├── master_state.py            # Usta FSM holatlari
│   └── student_state.py           # Roverchi FSM holatlari
├── utils/
│   └── sheets.py                  # Google Sheets API bilan asinxron integratsiya
├── .env.example                   # Muhit o'zgaruvchilari namunasi
├── .gitignore                     # Git e'tiborsiz qoldiradigan fayllar
├── Procfile                       # Bulutli serverlar uchun start buyrug'i
├── requirements.txt               # Python bog'liqliklari
├── config.py                      # Konfiguratsiya va xavfsizlik tekshiruvlari
├── bot.py                         # Asosiy ishga tushiruvchi bot fayli
└── README.md                      # Loyiha qo'llanmasi
```

---

## 🛠 O'rnatish va Ishga Tushirish

### 1. Kodni yuklab olish
```bash
git clone <repository-url>
cd Elshift-Telegram-Bot
```

### 2. Virtual muhit yaratish va faollashtirish
**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Bog'liqliklarni o'rnatish
```bash
pip install -r requirements.txt
```

### 4. Muhit o'zgaruvchilarini sozlash
`.env.example` faylidan nusxa olib, `.env` faylini yarating:
```bash
cp .env.example .env
```
`.env` faylini ochib, quyidagi o'zgaruvchilarni to'ldiring:
```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_IDS=123456789,987654321
GROUP_IDS=-1001234567890
SHEETS_API_URL=https://script.google.com/macros/s/AKfycb.../exec
SHEETS_API_TOKEN=your_secret_sheets_token
```

### 5. Botni ishga tushirish
```bash
python bot.py
```

---

## ☁️ Railway / VPS Deploy

Loyihada **Railway** yoki **Render / Heroku** kabi PaaS platformalarida tezkor ishga tushirish uchun `Procfile` fayli mavjud:
```text
worker: python bot.py
```
Railway loyihangizda muhit o'zgaruvchilari (Environment Variables) bo'limida `.env` dagi kalitlarni kiritishingiz kifoya.
