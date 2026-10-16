from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from keyboards.main_menu import main_menu

router = Router()

# --- /start komandasi uchun handler ---
@router.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()  # har qanday eski holatni tozalash
    await message.answer(
        "👋 Assalomu alaykum!\n\n"
        "<b>«Elshift»</b> rasmiy botiga xush kelibsiz!\n\n"
        "Asosiy menyu orqali boʻlimlardan birini tanlang 👇",
        reply_markup=main_menu
    )