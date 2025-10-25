from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from data.regions import REGIONS_DISTRICTS  # viloyatlar va tumanlar ro‘yxati shu faylda bo‘ladi
from keyboards.texts import CANCEL_BUTTON    # "Bekor qilish" tugmasi matni

# --- Yordamchi funksiya: Tumanlar klaviaturasini yaratish ---
def create_district_keyboard(region_name: str) -> ReplyKeyboardMarkup:
    """Berilgan viloyat uchun tuman/shaharlar tugmalarini yaratadi."""
    districts = REGIONS_DISTRICTS.get(region_name, [])
    keyboard_rows = []
    
    # 2 tadan tugma joylashtirish
    for i in range(0, len(districts), 2):
        row = [KeyboardButton(text=districts[i])]
        if i + 1 < len(districts):
            row.append(KeyboardButton(text=districts[i+1]))
        keyboard_rows.append(row)
    
    # "Bekor qilish" tugmasi
    keyboard_rows.append([KeyboardButton(text=CANCEL_BUTTON)])
    
    return ReplyKeyboardMarkup(keyboard=keyboard_rows, resize_keyboard=True)