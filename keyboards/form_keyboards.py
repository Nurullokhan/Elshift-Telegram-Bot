from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from keyboards.texts import CANCEL_BUTTON

# --- Bekor qilish tugmasining o'zi ---
cancel_only_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=CANCEL_BUTTON)]],
    resize_keyboard=True
)

# --- Telefon raqamini ulashish uchun keyboard ---
phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📞 Raqamni ulashish", request_contact=True)],
        [KeyboardButton(text=CANCEL_BUTTON)]
    ],
    resize_keyboard=True
)

# --- Ha / Yo'q tugmalari ---
yes_no_buttons = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Ha"), KeyboardButton(text="Yo'q")],
        [KeyboardButton(text=CANCEL_BUTTON)]
    ],
    resize_keyboard=True
)

# --- Ishdan ketish sababi tugmalari ---
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

# --- Oylik tanlash tugmalari ---
expected_salary_buttons = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="1,000,000 so'm"), KeyboardButton(text="1,500,000 so'm")],
        [KeyboardButton(text="2,000,000 so'm"), KeyboardButton(text="2,500,000 so'm")],
        [KeyboardButton(text="3,000,000 so'm"), KeyboardButton(text="4,000,000 so'm")],
        [KeyboardButton(text="5,000,000+ so'm"), KeyboardButton(text="Oylik muhim emas")],
        [KeyboardButton(text="Boshqa summa")],
        [KeyboardButton(text=CANCEL_BUTTON)]
    ],
    resize_keyboard=True
)

# --- Viloyatlar klaviaturasi ---
region_buttons = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Farg'ona"), KeyboardButton(text="Andijon")],
        [KeyboardButton(text="Namangan")],
        [KeyboardButton(text=CANCEL_BUTTON)]
    ],
    resize_keyboard=True
)