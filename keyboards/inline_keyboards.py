from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- Ijtimoiy tarmoqlar (Inline) --- 
social_media_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="▶️ YouTube", url='https://youtube.com/@elshiftuz?si=kpL2w0vvFXH4D5nN'),
            InlineKeyboardButton(text="📸 Instagram", url='https://www.instagram.com/elshift.uz')
        ],
        [
            InlineKeyboardButton(text="📢 Telegram", url='https://t.me/elshiftuz')
        ]
    ]
)