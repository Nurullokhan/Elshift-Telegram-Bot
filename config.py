import os
from dotenv import load_dotenv

# .env faylidan o'qish va muhit o'zgaruvchilarini yuklash
load_dotenv()

class Config:
    """Bot konfiguratsiyasini muhit o'zgaruvchilaridan yuklaydi."""
    
    # --- Telegram Sozlamalari ---
    BOT_TOKEN = os.getenv("BOT_TOKEN")

    # ADMIN_IDS ni ro'yxat (list) sifatida o‘qish
    try:
        ADMIN_IDS = [int(admin_id.strip()) for admin_id in os.getenv("ADMIN_IDS", "").split(",") if admin_id.strip()]
    except (TypeError, ValueError):
        ADMIN_IDS = []

    # GROUP_ID ni o‘qish
    try:
        GROUP_ID = int(os.getenv("GROUP_ID", "0"))
    except (TypeError, ValueError):
        GROUP_ID = 0

    # --- Google Sheets API Sozlamalari ---
    SHEETS_API_URL = os.getenv("SHEETS_API_URL")
    SHEETS_API_TOKEN = os.getenv("SHEETS_API_TOKEN")

    # --- Xatoliklarni tekshirish ---
    if not BOT_TOKEN:
        print("❌ KRITIK XATO: BOT_TOKEN muhit o'zgaruvchisi o‘rnatilmagan!")
    if not ADMIN_IDS:
        print("⚠️ DIQQAT: ADMIN_IDS o‘rnatilmagan yoki noto‘g‘ri. Hech bir admin aniqlanmadi.")
    if GROUP_ID == 0:
        print("⚠️ DIQQAT: GROUP_ID o‘rnatilmagan yoki noto‘g‘ri. Guruhga xabar yuborilmaydi.")

# --- Konsolga chiqarish ---
print("BOT_TOKEN:", Config.BOT_TOKEN)
print("ADMIN_IDS:", Config.ADMIN_IDS)
print("GROUP_ID:", Config.GROUP_ID)
print("SHEETS_API_URL:", Config.SHEETS_API_URL)
print("SHEETS_API_TOKEN:", Config.SHEETS_API_TOKEN)