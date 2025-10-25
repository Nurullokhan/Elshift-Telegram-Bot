from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from keyboards.main_menu import main_menu
from keyboards.texts import CANCEL_BUTTON
from keyboards.texts import BACK_BUTTON

dp = Dispatcher(storage=MemoryStorage())

# --- Restart komandasi ---
@dp.message(Command("restart"))
async def restart_handler(message: types.Message, state: FSMContext):
    # 1️⃣ Har qanday holatda state (holat)ni tozalaymiz
    await state.clear()

    # 2️⃣ Foydalanuvchiga qayta start holatini chiqaramiz
    await message.answer(
        "🔄 Bot qayta ishga tushirildi!\n\n"
        "Quyidagi menyudan kerakli bo‘limni tanlang 👇",
        reply_markup=main_menu
    )


# --- Chat ID olish ---
@dp.message(F.text == "chatid")
async def get_chat_id(message: types.Message):
    await message.answer(f"Chat ID: <code>{message.chat.id}</code>", parse_mode="HTML")

# --- Admin ID (yoki user ID) ---
@dp.message(Command("adminid"))
async def send_my_id(message: types.Message):
    user_id = message.from_user.id
    await message.answer(f"Sizning Telegram ID'ingiz: <code>{user_id}</code>", parse_mode="HTML")

# --- Asosiy menyuga qaytish (⬅️ Orqaga) ---
@dp.message(F.text == BACK_BUTTON)
async def back_handler_global(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyuga qaytdingiz 👇", reply_markup=main_menu)

# --- Anketani bekor qilish (❌ Bekor qilish) ---
@dp.message(F.text == CANCEL_BUTTON)
async def cancel_handler_in_form(message: types.Message, state: FSMContext):
    # Har qanday holatda formani tozalaymiz
    await state.clear()
    await message.answer("Anketa bekor qilindi. Asosiy menyuga qaytdingiz 👇", reply_markup=main_menu)