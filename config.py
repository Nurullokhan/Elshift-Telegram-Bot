import os
from dotenv import load_dotenv

# .env faylidan o'qish va muhit o'zgaruvchilarini yuklash
load_dotenv()

class Config:
    """Bot konfiguratsiyasini muhit o'zgaruvchilaridan yuklaydi."""
    
    # --- Telegram Sozlamalari ---
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    # ADMIN_ID ni integer (son) turiga o'tkazish
    try:
        ADMIN_ID = int(os.getenv("ADMIN_ID"))
    except (TypeError, ValueError):
        # Agar ADMIN_ID yuklanmasa yoki noto'g'ri bo'lsa, xavfsiz default qiymat
        ADMIN_ID = 0
    
    # --- Google Sheets API Sozlamalari ---
    SHEETS_API_URL = os.getenv("SHEETS_API_URL")
    SHEETS_API_TOKEN = os.getenv("SHEETS_API_TOKEN")

    # Konfiguratsiya tekshiruvi (Ixtiyoriy, lekin foydali)
    if not BOT_TOKEN:
        print("KRITIK XATO: BOT_TOKEN muhit o'zgaruvchisi o'rnatilmagan!")
        # Botni ishga tushirishga harakat qilishdan oldin uni to'g'rilash kerak
    if ADMIN_ID == 0:
        print("DIQQAT: ADMIN_ID o'rnatilmagan yoki noto'g'ri. Ma'mur xabarlari yuborilmaydi.")

print("BOT_TOKEN:", Config.BOT_TOKEN)
print("ADMIN_ID:", Config.ADMIN_ID)
print("SHEETS_API_URL:", Config.SHEETS_API_URL)
print("SHEETS_API_TOKEN:", Config.SHEETS_API_TOKEN)