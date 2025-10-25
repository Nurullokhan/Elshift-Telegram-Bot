from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

BACK_BUTTON = "🔙 Orqaga"
CANCEL_BUTTON = "Bekor qilish"

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("🏢 Biz haqimizda"), KeyboardButton("💼 Bo'sh ish o'rinlari")],
        [KeyboardButton("📍 Manzil")]
    ],
    resize_keyboard=True
)

jobs_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("👷 Usta"), KeyboardButton("👨‍🎓 Ish o'rganuvchi")],
        [KeyboardButton(BACK_BUTTON)]
    ],
    resize_keyboard=True
)