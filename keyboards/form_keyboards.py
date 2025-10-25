from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from keyboards.texts import CANCEL_BUTTON

# --- Telefon raqamini ulashish uchun keyboard ---
phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📞 Raqamni ulashish", request_contact=True)],
        [KeyboardButton(text=CANCEL_BUTTON)]
    ],
    resize_keyboard=True
)

yes_no_buttons = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Ha"), KeyboardButton(text="Yo'q")],
        [KeyboardButton(text=CANCEL_BUTTON)]
    ],
    resize_keyboard=True
)

reason_left_buttons = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Oylik kamligi")],
        [KeyboardButton(text="Ish sharoiti yaxshi emasligi")],
        [KeyboardButton(text="O'z ustimda ishlash uchun")],
        [KeyboardButton(text="Boshqa sabab")],
        [KeyboardButton(text=CANCEL_BUTTON)]
    ],
    resize_keyboard=True
)