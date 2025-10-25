from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from keyboards import main_menu

dp = Dispatcher(storage=MemoryStorage)

# --- /start komandasi uchun handler ---
@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()  # har qanday eski holatni tozalash
    await message.answer(
        "👋 Assalomu alaykum!\n\n"
        "<b>«Elshift»</b> rasmiy botiga xush kelibsiz!\n\n"
        "Asosiy menyu orqali boʻlimlardan birini tanlang 👇",
        reply_markup=main_menu
    )