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

    # GROUP_IDS ni o‘qish (GROUP_IDS yoki GROUP_ID muhit o'zgaruvchisidan)
    group_ids_raw = os.getenv("GROUP_IDS") or os.getenv("GROUP_ID", "")
    try:
        GROUP_IDS = [int(group_id.strip()) for group_id in group_ids_raw.split(",") if group_id.strip()]
    except (TypeError, ValueError):
        GROUP_IDS = []

    # --- Google Sheets API Sozlamalari ---
    SHEETS_API_URL = os.getenv("SHEETS_API_URL")
    SHEETS_API_TOKEN = os.getenv("SHEETS_API_TOKEN")

    @classmethod
    def get_notification_targets(cls):
        """Barcha admin va guruh ID larini takrorlanishlarsiz ro'yxat sifatida qaytaradi."""
        targets = []
        for target in cls.GROUP_IDS + cls.ADMIN_IDS:
            if target and target not in targets:
                targets.append(target)
        return targets

    # --- Xatoliklarni tekshirish ---
    if not BOT_TOKEN:
        print("❌ KRITIK XATO: BOT_TOKEN muhit o'zgaruvchisi o‘rnatilmagan!")
    if not ADMIN_IDS:
        print("⚠️ DIQQAT: ADMIN_IDS o‘rnatilmagan yoki noto‘g‘ri. Hech bir admin aniqlanmadi.")
    if not GROUP_IDS:
        print("⚠️ DIQQAT: GROUP_IDS o‘rnatilmagan yoki noto‘g‘ri. Guruhga xabar yuborilmaydi.")

# --- Xavfsiz konsolga chiqarish (tokenlarni oshkor qilmasdan) ---
print(f"BOT_TOKEN: {'O‘rnatilgan ✅' if Config.BOT_TOKEN else 'Topilmadi ❌'}")
print(f"ADMIN_IDS: {Config.ADMIN_IDS}")
print(f"GROUP_IDS: {Config.GROUP_IDS}")
print(f"SHEETS_API_URL: {'O‘rnatilgan ✅' if Config.SHEETS_API_URL else 'Topilmadi ❌'}")
print(f"SHEETS_API_TOKEN: {'O‘rnatilgan ✅' if Config.SHEETS_API_TOKEN else 'Topilmadi ❌'}")