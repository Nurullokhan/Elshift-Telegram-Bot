from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from keyboards.main_menu import main_menu
from keyboards.texts import CANCEL_BUTTON, BACK_BUTTON

router = Router()

# --- Restart komandasi ---
@router.message(Command("restart"))
async def restart_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🔄 Bot qayta ishga tushirildi!\n\n"
        "Quyidagi menyudan kerakli bo‘limni tanlang 👇",
        reply_markup=main_menu
    )

# --- Chat ID olish ---
@router.message(F.text == "chatid")
async def get_chat_id(message: types.Message):
    await message.answer(f"Chat ID: <code>{message.chat.id}</code>", parse_mode="HTML")

# --- Admin ID (yoki user ID) ---
@router.message(Command("adminid"))
async def send_my_id(message: types.Message):
    user_id = message.from_user.id
    await message.answer(f"Sizning Telegram ID'ingiz: <code>{user_id}</code>", parse_mode="HTML")

# --- Asosiy menyuga qaytish (🔙 Orqaga) ---
@router.message(F.text.in_([BACK_BUTTON, "🔙 Orqaga", "Orqaga"]))
async def back_handler_global(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyuga qaytdingiz 👇", reply_markup=main_menu)

# --- Anketani bekor qilish (❌ Bekor qilish) ---
@router.message(Command("cancel"))
@router.message(F.text.in_([CANCEL_BUTTON, "❌ Bekor qilish", "Bekor qilish", "/cancel"]))
async def cancel_handler_in_form(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Anketa bekor qilindi. Asosiy menyuga qaytdingiz 👇", reply_markup=main_menu)