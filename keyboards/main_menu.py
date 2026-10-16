from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from keyboards.texts import (
    BACK_BUTTON, CANCEL_BUTTON, ABOUT_BUTTON, VACANCIES_BUTTON,
    LOCATION_BUTTON, JOB_TITLE_MASTER, JOB_TITLE_APPRENTICE
)

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=ABOUT_BUTTON), KeyboardButton(text=VACANCIES_BUTTON)],
        [KeyboardButton(text=LOCATION_BUTTON)]
    ],
    resize_keyboard=True
)

jobs_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=JOB_TITLE_MASTER), KeyboardButton(text=JOB_TITLE_APPRENTICE)],
        [KeyboardButton(text=BACK_BUTTON)]
    ],
    resize_keyboard=True
)