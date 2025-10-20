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
        GROUP_IDS = [int(group_id.strip()) for group_id in os.getenv("GROUP_IDS", "").split(",") if group_id.strip()]
    except (TypeError, ValueError):
        GROUP_IDS = []

    # --- Google Sheets API Sozlamalari ---
    SHEETS_API_URL = os.getenv("SHEETS_API_URL")
    SHEETS_API_TOKEN = os.getenv("SHEETS_API_TOKEN")

    # --- Xatoliklarni tekshirish ---
    if not BOT_TOKEN:
        print("❌ KRITIK XATO: BOT_TOKEN muhit o'zgaruvchisi o‘rnatilmagan!")
    if not ADMIN_IDS:
        print("⚠️ DIQQAT: ADMIN_IDS o‘rnatilmagan yoki noto‘g‘ri. Hech bir admin aniqlanmadi.")
    if GROUP_IDS:
        print("⚠️ DIQQAT: GROUP_IDS o‘rnatilmagan yoki noto‘g‘ri. Guruhga xabar yuborilmaydi.")

# --- Konsolga chiqarish ---
print("BOT_TOKEN:", Config.BOT_TOKEN)
print("ADMIN_IDS:", Config.ADMIN_IDS)
print("GROUP_IDS:", Config.GROUP_IDS)
print("SHEETS_API_URL:", Config.SHEETS_API_URL)
print("SHEETS_API_TOKEN:", Config.SHEETS_API_TOKEN)