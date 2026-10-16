import asyncio
import re
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

# Konfiguratsiya faylidan sozlamalarni yuklash
from config import Config
from utils.sheets import send_data_to_sheets
from data.regions import REGIONS_DISTRICTS
from keyboards.texts import (
    CANCEL_BUTTON, BACK_BUTTON, ABOUT_BUTTON, VACANCIES_BUTTON,
    LOCATION_BUTTON, JOB_TITLE_MASTER, JOB_TITLE_APPRENTICE, JOB_TITLE_ROVER
)
from keyboards.main_menu import main_menu, jobs_menu
from keyboards.form_keyboards import (
    phone_keyboard, yes_no_buttons, reason_left_buttons,
    expected_salary_buttons, cancel_only_keyboard, region_buttons
)
from keyboards.inline_keyboards import social_media_keyboard
from keyboards.region_keyboards import create_district_keyboard
from states.apprentice_state import ApprenticeForm
from states.master_state import MasterForm
from states.student_state import StudentForm

# --- Logging sozlamalari ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Bot va Dispatcher yaratish ---
bot = Bot(
    token=Config.BOT_TOKEN, 
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher(storage=MemoryStorage())

# --- Matnlar ---
ELSHIFT_ABOUT = (
    "<b>«Elshift» qanday brend?</b>\n\n"
    "<b>Elshift</b> — bu alukabond xizmati bilan shugʻillanuvchi kompaniya hisoblanadi. "
    "Biz 12 yildan buyon xalqimizga alukabond xizmatini koʻrsatib kelyapmiz!\n\n"
    "Bizning qadriyatimiz:\n"
    "<b>Mijozlarga oʻz vaqtida va sifatli xizmat koʻrsatish — bizning eng asosiy tamoyilimiz.</b>\n\n"
    "Elshift — tanlovingizni oqlaydigan sifatli va ishonchli alukabond xizmati!\n\n"
    "<i>Kompaniya haqida batafsil ma'lumotlarni videodan va ijtimoiy tarmoqlarimizdan bilib olishingiz mumkin.</i>"
)

# =====================================================================
# --- Yordamchi Funksiyalar (Guruh, Admin va Havolalar bilan ishlash) ---
# =====================================================================

def get_telegram_message_link(chat_id: int, message_id: int) -> str:
    """Telegram guruhi yoki kanalidagi xabarga to'g'ri havolani yaratadi."""
    chat_str = str(chat_id).strip()
    if chat_str.startswith("-100"):
        return f"https://t.me/c/{chat_str[4:]}/{message_id}"
    elif chat_str.startswith("-"):
        return f"https://t.me/c/{chat_str[1:]}/{message_id}"
    return f"https://t.me/c/{chat_str}/{message_id}"


async def send_voice_to_recipients(file_id: str, caption: str) -> str:
    """Ovozli xabarni barcha guruh/adminlarga yuboradi va havolani qaytaradi."""
    targets = Config.get_notification_targets()
    voice_link = ""
    for target_id in targets:
        try:
            sent = await bot.send_voice(
                chat_id=target_id,
                voice=file_id,
                caption=caption
            )
            if not voice_link:
                voice_link = get_telegram_message_link(target_id, sent.message_id)
        except Exception as e:
            logging.error(f"Chat {target_id} ga ovozli xabar yuborishda xatolik: {e}")
            
    return voice_link or f"Telegram file_id: {file_id}"


async def send_media_to_recipients(media_type: str, file_id: str, caption: str) -> str:
    """Rasm yoki videoni guruh/adminlarga yuboradi va havolani qaytaradi."""
    targets = Config.get_notification_targets()
    media_link = ""
    for target_id in targets:
        try:
            if media_type == "photo":
                sent = await bot.send_photo(chat_id=target_id, photo=file_id, caption=caption)
            elif media_type == "video":
                sent = await bot.send_video(chat_id=target_id, video=file_id, caption=caption)
            else:
                sent = await bot.send_document(chat_id=target_id, document=file_id, caption=caption)
            if not media_link:
                media_link = get_telegram_message_link(target_id, sent.message_id)
        except Exception as e:
            logging.error(f"Chat {target_id} ga {media_type} yuborishda xatolik: {e}")
            
    return media_link or f"Telegram file_id: {file_id}"


async def notify_recipients(text: str) -> bool:
    """Arizani barcha admin va guruhlarga yuboradi."""
    targets = Config.get_notification_targets()
    if not targets:
        logging.warning("⚠️ Xabar yuborish uchun hech qanday target (admin yoki guruh) mavjud emas!")
        return False
    
    success = False
    for target_id in targets:
        try:
            await bot.send_message(
                chat_id=target_id,
                text=text,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            success = True
        except Exception as e:
            logging.error(f"Chat {target_id} ga ariza yuborishda xatolik: {e}")
            
    return success


# =====================================================================
# --- Umumiy Buyruqlar va Menyu Handlerlari ---
# =====================================================================

@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    video_file_id = "BAACAgIAAyEFAAS6OEd7AAMQaPW4c5h75xhbCwer3puhLa8VzJAAAmCKAAKEzKlLmSJO0p8oaUQ2BA"
    
    try:
        await message.answer_video(
            video=video_file_id,
            caption=ELSHIFT_ABOUT,
            reply_markup=social_media_keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logging.warning(f"Video yuborishda ogohlantirish: {e}")
        await message.answer(
            ELSHIFT_ABOUT,
            reply_markup=social_media_keyboard,
            parse_mode="HTML"
        )

    await message.answer(
        "👋 Assalomu alaykum!\n\n"
        "<b>«Elshift»</b> rasmiy botiga xush kelibsiz!\n"
        "Asosiy menyu orqali boʻlimlardan birini tanlang 👇",
        reply_markup=main_menu,
        parse_mode="HTML"
    )


@dp.message(Command("restart"))
async def restart_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🔄 Bot qayta ishga tushirildi!\n\n"
        "Quyidagi menyudan kerakli bo‘limni tanlang 👇",
        reply_markup=main_menu
    )


@dp.message(F.text == "chatid")
async def get_chat_id(message: types.Message):
    await message.answer(f"Ushbu chat ID: <code>{message.chat.id}</code>", parse_mode="HTML")


@dp.message(Command("adminid"))
async def send_my_id(message: types.Message):
    await message.answer(f"Sizning Telegram ID'ingiz: <code>{message.from_user.id}</code>", parse_mode="HTML")


# Bekor qilish tugmasi uchun universal handler (Har qanday holatda ishlaydi)
@dp.message(Command("cancel"))
@dp.message(F.text.in_([CANCEL_BUTTON, "Bekor qilish", "❌ Bekor qilish", "/cancel"]))
async def cancel_handler_global(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer(
            "❌ Anketa bekor qilindi. Asosiy menyuga qaytdingiz 👇",
            reply_markup=main_menu
        )
    else:
        await message.answer(
            "Asosiy menyudasiz 👇",
            reply_markup=main_menu
        )


# Orqaga tugmasi
@dp.message(F.text.in_([BACK_BUTTON, "🔙 Orqaga", "Orqaga"]))
async def back_handler_global(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyuga qaytdingiz 👇", reply_markup=main_menu)


# Biz haqimizda bo'limi (tugma matnlari mosligi ta'minlandi)
@dp.message(F.text.in_([ABOUT_BUTTON, "🏢 Elshift - haqida", "🏢 Biz haqimizda", "Biz haqimizda"]))
async def about_handler(message: types.Message):
    video_file_id = "BAACAgIAAyEFAAS6OEd7AAMQaPW4c5h75xhbCwer3puhLa8VzJAAAmCKAAKEzKlLmSJO0p8oaUQ2BA"
    try:
        await message.answer_video(
            video=video_file_id,
            caption=ELSHIFT_ABOUT,
            reply_markup=social_media_keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logging.warning(f"'Biz haqimizda' videosini yuborishda ogohlantirish: {e}")
        await message.answer(
            ELSHIFT_ABOUT,
            reply_markup=social_media_keyboard,
            parse_mode="HTML"
        )


# Bo'sh ish o'rinlari bo'limi
@dp.message(F.text.in_([VACANCIES_BUTTON, "💼 Bo'sh ish o'rinlari", "Bo'sh ish o'rinlari"]))
async def jobs_handler(message: types.Message):
    await message.answer(
        "👷 <b>Usta</b> — Tajribangiz bo'lsa, tayyor obyektlar va bonusli daromad sizni kutmoqda.\n\n"
        "👨‍🎓 <b>Ish o'rganuvchi</b> — 6 - 12 oyda usta darajasiga yetib, <b>Elshift</b> jamoasida o'z o'rningizga ega bo'ling.\n\n"
        "👇 Quyidagi yo‘nalishlardan birini tanlang:",
        reply_markup=jobs_menu,
        parse_mode="HTML"
    )


# Manzil bo'limi
@dp.message(F.text.in_([LOCATION_BUTTON, "📍 Manzil", "Manzil"]))
async def contact_handler(message: types.Message):
    text = (
        "🏢 <b>Bizning manzil:</b>\n"
        "<a href='https://maps.app.goo.gl/rE3iPvTM4Z3ezf1h7'>Farg‘ona viloyati, Marg‘ilon shahri</a>\n\n"
        "🕒 <b>Ish vaqti:</b> 09:00 — 18:00\n"
        "☪️ <b>Dam olish kuni:</b> Juma\n\n"
        "Sizni ofisimizda mamnuniyat bilan kutib qolamiz! 😊"
    )
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)


# =====================================================================
# --- 👨‍🎓 ISH O'RGANUVCHILAR ANKETASI (APPRENTICE) ---
# =====================================================================

@dp.message(F.text.in_([JOB_TITLE_APPRENTICE, "👨‍🎓 Ish o'rganuvchi", "Ish o'rganuvchi"]))
async def trainees_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Ish o'rganuvchilar anketasini to'ldirishni boshlaymiz.\n\n"
        "Iltimos, <b>Ism va familiyangizni</b> kiriting:",
        reply_markup=cancel_only_keyboard,
        parse_mode="HTML"
    )
    await state.set_state(ApprenticeForm.name_surname)


@dp.message(ApprenticeForm.name_surname)
async def app_name_handler(message: types.Message, state: FSMContext):
    await state.update_data(name_surname=message.text.strip())
    await message.answer(
        "<b>Yoshingiz nechchida?</b>\n"
        "(Iltimos, faqat <b>raqam</b> bilan kiriting, masalan: 21)",
        reply_markup=cancel_only_keyboard,
        parse_mode="HTML"
    )
    await state.set_state(ApprenticeForm.age)


@dp.message(ApprenticeForm.age)
async def app_age_handler(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit() or not (16 <= int(text) <= 30):
        await message.answer(
            "Iltimos, yoshingizni faqat raqamlarda kiriting (Masalan: 21).\n"
            "Nomzodlar uchun yosh chegarasi: <b>16 dan 30 yoshgacha</b>.",
            parse_mode="HTML"
        )
        return
        
    await state.update_data(age=text)
    await message.answer(
        "<b>Telefon raqamingizni</b> kiriting yoki tugma orqali <b>ulashing</b>:\n"
        "<i>(Namuna: +998901234567)</i>",
        reply_markup=phone_keyboard,
        parse_mode="HTML"
    )
    await state.set_state(ApprenticeForm.phone)


@dp.message(ApprenticeForm.phone)
async def app_phone_handler(message: types.Message, state: FSMContext):
    phone_number = None
    if message.contact:
        phone_number = message.contact.phone_number
        if not phone_number.startswith("+"):
            phone_number = "+" + phone_number
    elif message.text:
        text = message.text.replace(" ", "").strip()
        if re.match(r'^\+?\d{9,15}$', text):
            phone_number = text if text.startswith("+") else "+" + text
        
    if not phone_number:
        await message.answer(
            "Iltimos, telefon raqamini to'g'ri formatda kiriting (+998...) yoki tugma orqali ulashing.",
            reply_markup=phone_keyboard
        )
        return

    await state.update_data(phone=phone_number)
    await message.answer(
        "Endi <b>viloyatingizni</b> tanlang:",
        reply_markup=region_buttons,
        parse_mode="HTML"
    )
    await state.set_state(ApprenticeForm.address_region)


@dp.message(ApprenticeForm.address_region)
async def app_address_region_handler(message: types.Message, state: FSMContext):
    region = message.text.strip()
    if region not in REGIONS_DISTRICTS:
        await message.answer("Iltimos, menyudagi tugmalardan viloyatni tanlang.", reply_markup=region_buttons)
        return
        
    await state.update_data(address_region=region)
    district_keyboard = create_district_keyboard(region)
    await message.answer(
        f"Siz <b>{region}</b> viloyatini tanladingiz.\nEndi <b>tuman yoki shaharni</b> tanlang:",
        reply_markup=district_keyboard,
        parse_mode="HTML"
    )
    await state.set_state(ApprenticeForm.address_district)


@dp.message(ApprenticeForm.address_district)
async def app_address_district_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    region = data.get('address_region')
    district = message.text.strip()

    if region not in REGIONS_DISTRICTS or district not in REGIONS_DISTRICTS[region]:
        await message.answer("Iltimos, ro'yxatdagi tuman/shaharlardan birini tanlang.")
        return
        
    await state.update_data(address_district=district) 
    await message.answer(
        "<b>Avval qayerda ishlagansiz va nima ish qilgansiz?</b>\n\n"
        "Iltimos, <b>ovozli xabar</b> jo'nating yoki <i>\"Ishlamaganman\"</i> deb yozing.",
        reply_markup=cancel_only_keyboard,
        parse_mode="HTML"
    )
    await state.set_state(ApprenticeForm.previous_job)


@dp.message(ApprenticeForm.previous_job)
async def app_previous_job_handler(message: types.Message, state: FSMContext):
    try:
        # Matnli javob
        if message.text:
            previous_job = message.text.strip()
            await state.update_data(previous_job=previous_job)

            if previous_job.lower() in ["ishlamaganman", "yo'q", "yoq", "ishlamagan"]:
                await state.update_data(previous_salary="Kiritilmagan")
                await state.update_data(reason_left="Kiritilmagan")

                await message.answer(
                    "Biz bilan ishlashda <b>qanday oylik maosh</b> kutyapsiz?\n"
                    "Tanlang yoki summani yozing:",
                    reply_markup=expected_salary_buttons,
                    parse_mode="HTML"
                )
                await state.set_state(ApprenticeForm.expected_salary)
                return

            salary_buttons = ReplyKeyboardMarkup(
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
            await message.answer(
                "Avvalgi ish joyingizda oyligingiz qancha edi?\nTanlang yoki yozing:",
                reply_markup=salary_buttons,
                parse_mode="HTML"
            )
            await state.set_state(ApprenticeForm.previous_salary)
            return

        # Ovozli javob
        elif message.voice:
            voice_link = await send_voice_to_recipients(
                file_id=message.voice.file_id,
                caption=f"🎤 Avvalgi ish haqida ovozli javob: {message.from_user.full_name}"
            )
            await state.update_data(previous_job=voice_link)
            await message.answer("✅ Ovozli javob qabul qilindi.")

            salary_buttons = ReplyKeyboardMarkup(
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
            await message.answer(
                "Avvalgi ish joyingizda oyligingiz qancha edi?\nTanlang yoki yozing:",
                reply_markup=salary_buttons,
                parse_mode="HTML"
            )
            await state.set_state(ApprenticeForm.previous_salary)
            return

        else:
            await message.answer("❌ Faqat matn yoki ovozli xabar yuborish mumkin. Iltimos, qayta urinib ko‘ring.")
            return

    except Exception as e:
        logging.error(f"Avvalgi ish javobini qabul qilishda xatolik: {e}")
        await message.answer("⚠️ Xatolik yuz berdi. Iltimos, qayta urinib ko‘ring.")


@dp.message(ApprenticeForm.previous_salary)
async def app_previous_salary_handler(message: types.Message, state: FSMContext):
    await state.update_data(previous_salary=message.text.strip())
    await message.answer("Avvalgi ishdan nima sababdan ketgansiz?", reply_markup=reason_left_buttons)
    await state.set_state(ApprenticeForm.reason_left)


@dp.message(ApprenticeForm.reason_left)
async def app_reason_handler(message: types.Message, state: FSMContext):
    await state.update_data(reason_left=message.text.strip())
    await message.answer(
        "Biz bilan ishlashda <b>qanday oylik kutyapsiz</b>?\n"
        "(Tanlang yoki summani yozing):",
        reply_markup=expected_salary_buttons,
        parse_mode="HTML"
    )
    await state.set_state(ApprenticeForm.expected_salary)


@dp.message(ApprenticeForm.expected_salary)
async def app_expected_salary_handler(message: types.Message, state: FSMContext):
    await state.update_data(expected_salary=message.text.strip())
    await message.answer(
        "<b>Matematikani qanchalik bilasiz?</b>\n"
        "(Gradus, metr, sm, kvadrat va boshqa hisob-kitoblar bilan ishlash)\n\n"
        "Iltimos, <b>ovozli xabar</b> orqali javob yuboring yoki <b>\"Yo'q\"</b> tugmasini bosing:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Yo'q"), KeyboardButton(text=CANCEL_BUTTON)]
            ],
            resize_keyboard=True,
        ),
        parse_mode="HTML"
    )
    await state.set_state(ApprenticeForm.math_skill)


@dp.message(ApprenticeForm.math_skill)
async def app_math_skill_handler(message: types.Message, state: FSMContext):
    try:
        if message.voice:
            voice_link = await send_voice_to_recipients(
                file_id=message.voice.file_id,
                caption=f"🎤 Matematika haqida ovozli javob: {message.from_user.full_name}"
            )
            await state.update_data(math_skill=voice_link)
            await message.answer("✅ Ovozli javob qabul qilindi.")

            await message.answer(
                "<b>Hunar o'rganishdan asosiy maqsadingiz nima?</b>\nIltimos, yozib qoldiring:",
                reply_markup=cancel_only_keyboard,
                parse_mode="HTML"
            )
            await state.set_state(ApprenticeForm.goal)
            return

        elif message.text and message.text.strip().lower() in ["yo'q", "yoq", "no"]:
            await state.update_data(math_skill="Bilmaydi / Yo'q")
            await message.answer(
                "<b>Hunar o'rganishdan asosiy maqsadingiz nima?</b>\nIltimos, yozib qoldiring:",
                reply_markup=cancel_only_keyboard,
                parse_mode="HTML"
            )
            await state.set_state(ApprenticeForm.goal)
            return

        else:
            await message.answer(
                "❌ Iltimos, faqat ovozli xabar yuboring yoki 'Yo'q' tugmasini bosing.",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="Yo'q"), KeyboardButton(text=CANCEL_BUTTON)]],
                    resize_keyboard=True
                )
            )
            return

    except Exception as e:
        logging.error(f"Matematika javobini qabul qilishda xatolik: {e}")
        await message.answer("⚠️ Xatolik yuz berdi, iltimos qayta urinib ko‘ring.")


@dp.message(ApprenticeForm.goal)
async def app_goal_handler(message: types.Message, state: FSMContext):
    await state.update_data(goal=message.text.strip())
    await message.answer(
        "Oldin lesada yoki baland joylarda ishlaganmisiz?\n"
        "Agar ish joyi balandroq bo‘lsa, bunga tayyormisiz?\n\n"
        "<i>Masalan:</i>\n"
        "— Ha, ishlaganman\n"
        "— Yo‘q, lekin sinab ko‘rmoqchiman\n"
        "— Baland joydan qo‘rqaman",
        reply_markup=cancel_only_keyboard,
        parse_mode="HTML"
    )
    await state.set_state(ApprenticeForm.hardworking)


@dp.message(ApprenticeForm.hardworking)
async def app_hardworking_handler(message: types.Message, state: FSMContext):
    await state.update_data(hardworking=message.text.strip())
    await message.answer(
        "<b>Qachondan ish boshlay olasiz?</b>\n"
        "<i>Masalan:</i> Ertadan / Bir haftada / Dushanbadan",
        reply_markup=cancel_only_keyboard,
        parse_mode="HTML"
    )
    await state.set_state(ApprenticeForm.start_date)


@dp.message(ApprenticeForm.start_date)
async def app_start_date_handler(message: types.Message, state: FSMContext):
    await state.update_data(start_date=message.text.strip())
    await message.answer(
        "Boshqa <b>qo'shimcha savol</b> yoki <b>takliflaringiz</b> bo'lsa yozing.\n"
        "<i>(Agar bo'lmasa: <b>\"Yo'q\"</b> deb yozing)</i>",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Yo'q"), KeyboardButton(text=CANCEL_BUTTON)]],
            resize_keyboard=True
        ),
        parse_mode="HTML"
    )
    await state.set_state(ApprenticeForm.additional)


@dp.message(ApprenticeForm.additional)
async def app_additional_handler(message: types.Message, state: FSMContext):
    await state.update_data(additional=message.text.strip())
    data = await state.get_data()
    await state.set_state(ApprenticeForm.submitting)

    full_address = f"{data.get('address_region', 'Kiritilmagan')} viloyati, {data.get('address_district', 'Kiritilmagan')}"

    # Telegram orqali yuboriladigan ariza xabari
    application_text = (
        f"🚨 <b>YANGI ISH O'RGANUVCHI ANKETASI</b> 🚨\n\n"
        f"<b>🆔 Telegram ID:</b> <code>{message.from_user.id}</code>\n"
        f"<b>👤 Nomzod:</b> {data.get('name_surname', 'Kiritilmagan')}\n"
        f"<b>🎂 Yoshi:</b> {data.get('age', 'Kiritilmagan')}\n"
        f"<b>📱 Telefon:</b> <code>{data.get('phone', 'Kiritilmagan')}</code>\n"
        f"<b>🏠 Manzil:</b> {full_address}\n"
        f"────────────────────\n"
        f"<b>💼 Avvalgi ish:</b> {data.get('previous_job', 'Kiritilmagan')}\n"
        f"<b>💰 Avvalgi oylik:</b> {data.get('previous_salary', 'Kiritilmagan')}\n"
        f"<b>❌ Ishdan ketish sababi:</b> {data.get('reason_left', 'Kiritilmagan')}\n"
        f"<b>💰 Kutayotgan oylik:</b> {data.get('expected_salary', 'Kiritilmagan')}\n"
        f"<b>🎯 Maqsad:</b> {data.get('goal', 'Kiritilmagan')}\n"
        f"<b>💪 Baland joyda ishlash:</b> {data.get('hardworking', 'Kiritilmagan')}\n"
        f"<b>🧮 Matematika bilimi:</b> {data.get('math_skill', 'Kiritilmagan')}\n"
        f"<b>📅 Ish boshlash:</b> {data.get('start_date', 'Kiritilmagan')}\n"
        f"<b>💬 Qo'shimcha:</b> {data.get('additional', 'Kiritilmagan')}\n"
        f"<b>📌 Yo'nalish:</b> Ish o'rganuvchi"
    )

    # Google Sheets uchun ma'lumotlar
    sheets_data = {
        "Sana": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Foydalanuvchi ID": message.from_user.id,
        "Ism va Familya": data.get('name_surname'),
        "Yoshi": data.get('age'),
        "Telefon": data.get('phone'),
        "Viloyat": data.get('address_region'),
        "Tuman/Shahar": data.get('address_district'),
        "Avvalgi ish": data.get('previous_job'),
        "Avvalgi oylik": data.get('previous_salary'),
        "Ishdan ketish sababi": data.get('reason_left'),
        "Kutilayotgan oylik": data.get('expected_salary'),
        "Maqsad": data.get('goal'),
        "Baland joyda ishlash": data.get('hardworking'),
        "Matematika bilimi": data.get('math_skill'),
        "Ish boshlash sanasi": data.get('start_date'),
        "Qo'shimcha ma'lumot": data.get('additional'),
        "Vakansiya turi": "Ish o'rganuvchi"
    }
    
    # 1. Sheets ga yuborish
    sheets_success = await send_data_to_sheets(sheets_data, "Shogird")

    # 2. Admin va guruhlarga xabar yuborish
    admin_success = await notify_recipients(application_text)

    # 3. Foydalanuvchiga to'g'ri va samimiy javob qaytarish
    if admin_success or sheets_success:
        await message.answer(
            "✅ Arizangiz muvaffaqiyatli qabul qilindi 😊\n\n"
            "Ma’lumotlaringiz ko‘rib chiqiladi va mos kelsangiz, albatta siz bilan tez orada bog‘lanamiz.",
            reply_markup=main_menu
        )
    else:
        await message.answer(
            "⚠️ Arizani yuborishda texnik xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring yoki ma'murlar bilan to'g'ridan-to'g'ri bog'laning.",
            reply_markup=main_menu
        )

    await state.clear()


# =====================================================================
# --- 👷 USTALAR ANKETASI (MASTER) ---
# =====================================================================

@dp.message(F.text.in_([JOB_TITLE_MASTER, "👷 Usta", "Usta"]))
async def masters_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Ustalar anketasini to'ldirishni boshlaymiz.\n\n"
        "Iltimos, <b>Ism va familiyangizni</b> kiriting:",
        reply_markup=cancel_only_keyboard,
        parse_mode="HTML"
    )
    await state.set_state(MasterForm.name_surname)


@dp.message(MasterForm.name_surname)
async def master_name_handler(message: types.Message, state: FSMContext):
    await state.update_data(name_surname=message.text.strip())
    await message.answer(
        "<b>Yoshingiz nechchida?</b>\n"
        "(Iltimos, faqat <b>raqam</b> bilan kiriting, masalan: 28)",
        reply_markup=cancel_only_keyboard,
        parse_mode="HTML"
    )
    await state.set_state(MasterForm.age)


@dp.message(MasterForm.age)
async def master_age_handler(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit() or not (18 <= int(text) <= 45):
        await message.answer(
            "Iltimos, yoshingizni faqat raqamlarda kiriting (Masalan: 28).\n"
            "Ustalar uchun yosh chegarasi: <b>18 dan 45 yoshgacha</b>.",
            parse_mode="HTML"
        )
        return
        
    await state.update_data(age=text)
    await message.answer(
        "<b>Telefon raqamingizni</b> kiriting yoki tugma orqali <b>ulashing</b>:\n"
        "<i>(Namuna: +998901234567)</i>",
        reply_markup=phone_keyboard,
        parse_mode="HTML"
    )
    await state.set_state(MasterForm.phone)


@dp.message(MasterForm.phone)
async def master_phone_handler(message: types.Message, state: FSMContext):
    phone_number = None
    if message.contact:
        phone_number = message.contact.phone_number
        if not phone_number.startswith("+"):
            phone_number = "+" + phone_number
    elif message.text:
        text = message.text.replace(" ", "").strip()
        if re.match(r'^\+?\d{9,15}$', text):
            phone_number = text if text.startswith("+") else "+" + text
        
    if not phone_number:
        await message.answer(
            "Iltimos, telefon raqamini to'g'ri formatda kiriting (+998...) yoki tugma orqali ulashing.",
            reply_markup=phone_keyboard
        )
        return

    await state.update_data(phone=phone_number)
    await message.answer(
        "Endi <b>viloyatingizni</b> tanlang:",
        reply_markup=region_buttons,
        parse_mode="HTML"
    )
    await state.set_state(MasterForm.address_region)


@dp.message(MasterForm.address_region)
async def master_address_region_handler(message: types.Message, state: FSMContext):
    region = message.text.strip()
    if region not in REGIONS_DISTRICTS:
        await message.answer("Iltimos, yuqoridagi tugmalardan viloyatni tanlang.", reply_markup=region_buttons)
        return
        
    await state.update_data(address_region=region)
    district_keyboard = create_district_keyboard(region)
    await message.answer(
        f"Siz <b>{region}</b> viloyatini tanladingiz.\nEndi <b>tuman yoki shaharni</b> tanlang:",
        reply_markup=district_keyboard,
        parse_mode="HTML"
    )
    await state.set_state(MasterForm.address_district)


@dp.message(MasterForm.address_district)
async def master_address_district_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    region = data.get('address_region')
    district = message.text.strip()

    if region not in REGIONS_DISTRICTS or district not in REGIONS_DISTRICTS[region]:
        await message.answer("Iltimos, ro'yxatdagi tuman/shaharlardan birini tanlang.")
        return
        
    await state.update_data(address_district=district)
    await message.answer(
        "Sizning <b>asosiy mutaxassisligingiz</b> nima?\n"
        "Kim bo'lib ishlaysiz?\n\n"
        "<i>Iltimos, to'liq yozing, namuna: <b>Alukabond montajchi</b></i>",
        reply_markup=cancel_only_keyboard,
        parse_mode="HTML"
    )
    await state.set_state(MasterForm.specialty)


@dp.message(MasterForm.specialty)
async def master_specialty_handler(message: types.Message, state: FSMContext):
    await state.update_data(specialty=message.text.strip())
    await message.answer(
        "Bu sohada <b>necha yillik tajribangiz</b> bor?\n"
        "<i>(Masalan: 3 yil yoki 6 oy)</i>",
        reply_markup=cancel_only_keyboard,
        parse_mode="HTML"
    )
    await state.set_state(MasterForm.experience_years)


@dp.message(MasterForm.experience_years)
async def master_experience_handler(message: types.Message, state: FSMContext):
    await state.update_data(experience_years=message.text.strip())
    await message.answer(
        "Avval <b>jamoa (brigada)</b> boshqarganmisiz?",
        reply_markup=yes_no_buttons,
        parse_mode="HTML"
    )
    await state.set_state(MasterForm.team_management)


@dp.message(MasterForm.team_management)
async def master_team_handler(message: types.Message, state: FSMContext):
    if message.text not in ["Ha", "Yo'q"]:
        await message.answer("Iltimos, faqat <b>Ha</b> yoki <b>Yo'q</b> tugmalaridan birini tanlang.", parse_mode="HTML")
        return
        
    await state.update_data(team_management=message.text.strip())
    await message.answer(
        "Qilgan <b>ishlaringizdan namuna (portfolio)</b> bormi?\n\n"
        "<i>(Rasm, video yoki ish namunalaringiz havolasini yuboring. Agar bo'lmasa: <b>\"Yo'q\"</b> deb yozing)</i>",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Yo'q"), KeyboardButton(text=CANCEL_BUTTON)]],
            resize_keyboard=True
        ),
        parse_mode="HTML"
    )
    await state.set_state(MasterForm.portfolio_link)


@dp.message(MasterForm.portfolio_link, F.content_type.in_({'text', 'photo', 'video', 'animation', 'document', 'voice'}))
async def master_portfolio_handler(message: types.Message, state: FSMContext):
    # Agar foydalanuvchi "Yo'q" deb yozsa
    if message.text and message.text.strip().lower() in ["yo'q", "yo‘q", "yoq", "no"]:
        current_portfolio = (await state.get_data()).get("portfolio", [])
        if not current_portfolio:
            await state.update_data(portfolio=[])
            
        await message.answer(
            "💰 Endi <b>kutayotgan oylik maoshingizni</b> yozing:\n"
            "<i>(So‘mda yoki kelishilgan foizda yozishingiz mumkin)</i>",
            reply_markup=cancel_only_keyboard,
            parse_mode="HTML"
        )
        await state.set_state(MasterForm.expected_salary_usta)
        return

    portfolio_list = (await state.get_data()).get("portfolio", [])
    if not isinstance(portfolio_list, list):
        portfolio_list = []

    file_id = None
    file_type = None
    portfolio_link = ""

    try:
        # Rasm yuborilsa
        if message.photo:
            file_id = message.photo[-1].file_id
            file_type = "photo"
            portfolio_link = await send_media_to_recipients(
                media_type="photo",
                file_id=file_id,
                caption=f"📁 Portfolio rasm: {message.from_user.full_name}"
            )

        # Video yuborilsa
        elif message.video:
            file_id = message.video.file_id
            file_type = "video"
            loading_msg = await message.answer("⏳ Video yuklanmoqda, biroz kuting...")
            portfolio_link = await send_media_to_recipients(
                media_type="video",
                file_id=file_id,
                caption=f"📁 Portfolio video: {message.from_user.full_name}"
            )
            await loading_msg.edit_text("✅ Video muvaffaqiyatli qabul qilindi!")

        # Matnli havola yuborilsa
        elif message.text:
            text = message.text.strip()
            if text.startswith("http://") or text.startswith("https://"):
                file_id = text
                file_type = "link"
                portfolio_link = text
            else:
                await message.answer(
                    "⚠️ Iltimos, rasm, video yoki to‘g‘ri havola yuboring (http:// yoki https:// bilan boshlanadigan).\n"
                    "Agar portfolio bo'lmasa, <b>\"Yo'q\"</b> tugmasini bosing.",
                    reply_markup=ReplyKeyboardMarkup(
                        keyboard=[[KeyboardButton(text="Yo'q"), KeyboardButton(text=CANCEL_BUTTON)]],
                        resize_keyboard=True
                    ),
                    parse_mode="HTML"
                )
                return

        else:
            await message.answer(
                "❌ Bu turdagi faylni qabul qilib bo‘lmaydi.\n"
                "Iltimos, faqat <b>rasm</b>, <b>video</b> yoki <b>havola</b> yuboring.",
                parse_mode="HTML"
            )
            return

        portfolio_list.append({
            "file_id": file_id,
            "type": file_type,
            "link": portfolio_link or ""
        })
        await state.update_data(portfolio=portfolio_list)

        await message.answer(
            "Yana portfolio (rasm/video/havola) yubormoqchimisiz?",
            reply_markup=yes_no_buttons,
            parse_mode="HTML"
        )
        await state.set_state(MasterForm.more_portfolio)

    except Exception as e:
        logging.error(f"Portfolio yuborishda xatolik: {e}")
        await message.answer("❌ Faylni yuborishda xatolik yuz berdi. Iltimos, qayta urinib ko‘ring.")


@dp.message(MasterForm.more_portfolio)
async def master_more_portfolio_handler(message: types.Message, state: FSMContext):
    if message.text not in ["Ha", "Yo'q"]:
        await message.answer("Iltimos, faqat <b>Ha</b> yoki <b>Yo‘q</b> tugmasini tanlang.", parse_mode="HTML")
        return

    if message.text == "Ha":
        await message.answer(
            "Yana portfolio faylini (rasm, video yoki havola) yuboring:",
            reply_markup=cancel_only_keyboard,
            parse_mode="HTML"
        )
        await state.set_state(MasterForm.portfolio_link)
    else:
        await message.answer(
            "💰 Endi <b>kutayotgan oylik maoshingizni</b> yozing:\n"
            "<i>(So‘mda yoki kelishilgan foizda yozishingiz mumkin)</i>",
            reply_markup=cancel_only_keyboard,
            parse_mode="HTML"
        )
        await state.set_state(MasterForm.expected_salary_usta)


@dp.message(MasterForm.expected_salary_usta)
async def master_expected_salary_handler(message: types.Message, state: FSMContext):
    await state.update_data(expected_salary_usta=message.text.strip())
    await message.answer(
        "<b>Oldin lesada yoki baland joylarda ishlaganmisiz? Ish joyi balandroq bo'lsa, bunga tayyormisiz?</b>\n"
        "<i>(Masalan: fasadda, lesada yoki narvonlarda)</i>",
        reply_markup=yes_no_buttons,
        parse_mode="HTML"
    )
    await state.set_state(MasterForm.hardworking_usta)


@dp.message(MasterForm.hardworking_usta)
async def master_hardworking_handler(message: types.Message, state: FSMContext):
    if message.text not in ["Ha", "Yo'q"]:
        await message.answer("Iltimos, faqat <b>Ha</b> yoki <b>Yo'q</b> tugmalaridan birini tanlang.", parse_mode="HTML")
        return

    await state.update_data(hardworking_usta=message.text.strip())
    await message.answer(
        "<b>Qachondan ish boshlay olasiz?</b>\n"
        "<i>(Masalan: Ertadan / Bir haftada / Kelishuvga ko'ra)</i>",
        reply_markup=cancel_only_keyboard,
        parse_mode="HTML"
    )
    await state.set_state(MasterForm.start_date_usta)


@dp.message(MasterForm.start_date_usta)
async def master_start_date_handler(message: types.Message, state: FSMContext):
    await state.update_data(start_date_usta=message.text.strip())
    data = await state.get_data()
    await state.set_state(MasterForm.submitting)

    full_address = f"{data.get('address_region', 'Kiritilmagan')} viloyati, {data.get('address_district', 'Kiritilmagan')}"

    portfolio_list = data.get("portfolio", [])
    portfolio_links = "\n".join([str(p.get("link") or "") for p in portfolio_list if p.get("link")]) or "Kiritilmagan"

    application_text = (
        f"👑 <b>YANGI USTA ANKETASI</b> 👑\n\n"
        f"<b>🆔 Telegram ID:</b> <code>{message.from_user.id}</code>\n"
        f"<b>👤 Nomzod:</b> {data.get('name_surname', 'Kiritilmagan')}\n"
        f"<b>🎂 Yoshi:</b> {data.get('age', 'Kiritilmagan')}\n"
        f"<b>📱 Telefon:</b> <code>{data.get('phone', 'Kiritilmagan')}</code>\n"
        f"<b>🏠 Manzil:</b> {full_address}\n"
        f"────────────────────\n"
        f"<b>🔨 Mutaxassislik:</b> {data.get('specialty', 'Kiritilmagan')}\n"
        f"<b>🗓 Tajriba:</b> {data.get('experience_years', 'Kiritilmagan')}\n"
        f"<b>👨‍💼 Jamoa boshqargan:</b> {data.get('team_management', 'Kiritilmagan')}\n"
        f"<b>🔗 Portfolio:</b>\n{portfolio_links}\n"
        f"<b>💰 Kutayotgan maosh:</b> {data.get('expected_salary_usta', 'Kiritilmagan')}\n"
        f"<b>💪 Baland joyda ishlash:</b> {data.get('hardworking_usta', 'Kiritilmagan')}\n"
        f"<b>📅 Ish boshlash:</b> {data.get('start_date_usta', 'Kiritilmagan')}\n"
        f"<b>📌 Yo'nalish:</b> Usta"
    )

    sheets_data = {
        "Sana": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Foydalanuvchi ID": message.from_user.id,
        "Ism va Familya": data.get('name_surname'),
        "Yoshi": data.get('age'),
        "Telefon": data.get('phone'),
        "Viloyat": data.get('address_region'),
        "Tuman/Shahar": data.get('address_district'),
        "Mutaxassislik": data.get('specialty'),
        "Tajriba (yil)": data.get('experience_years'),
        "Jamoa boshqaruvi": data.get('team_management'),
        "Portfolio": portfolio_links,
        "Kutayotgan maosh": data.get('expected_salary_usta'),
        "Baland joyda ishlash": data.get('hardworking_usta'),
        "Ish boshlash sanasi": data.get('start_date_usta'),
        "Vakansiya": "Usta"
    }

    # 1. Sheets ga yuborish
    sheets_success = await send_data_to_sheets(sheets_data, "Usta")

    # 2. Guruh va adminlarga yuborish
    admin_success = await notify_recipients(application_text)

    # 3. Javob
    if admin_success or sheets_success:
        await message.answer(
            "✅ Arizangiz muvaffaqiyatli yuborildi!\nTez orada ma'murlarimiz siz bilan bog'lanishadi.",
            reply_markup=main_menu
        )
    else:
        await message.answer(
            "⚠️ Arizani yuborishda texnik xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko‘ring.",
            reply_markup=main_menu
        )

    await state.clear()


# =====================================================================
# --- 👨‍🎓 SHOGIRD (ROVERCHI) ANKETASI ---
# =====================================================================

@dp.message(F.text.in_([JOB_TITLE_ROVER, "👨‍🎓 Shogird (Roverchi)", "Roverchi"]))
async def student_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Shogirdlar (Roverchi) anketasini to'ldirishni boshlaymiz.\n\n"
        "Iltimos, <b>Ism va familiyangizni</b> kiriting:",
        reply_markup=cancel_only_keyboard,
        parse_mode="HTML"
    )
    await state.set_state(StudentForm.name_surname)


@dp.message(StudentForm.name_surname)
async def student_name_handler(message: types.Message, state: FSMContext):
    await state.update_data(name_surname=message.text.strip())
    await message.answer(
        "<b>Yoshingiz nechchida?</b>\n"
        "(Iltimos, faqat <b>raqam</b> bilan kiriting)\n"
        "Yosh chegarasi: <b>16 dan 30 yoshgacha</b>",
        reply_markup=cancel_only_keyboard,
        parse_mode="HTML"
    )
    await state.set_state(StudentForm.age)


@dp.message(StudentForm.age)
async def student_age_handler(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit() or not (16 <= int(text) <= 30):
        await message.answer(
            "Iltimos, yoshingizni faqat raqamlarda kiriting (Masalan: 21).\n"
            "Yosh chegarasi: <b>16 dan 30 yoshgacha</b> bo'lsin.",
            parse_mode="HTML"
        )
        return
    
    await state.update_data(age=text)
    await message.answer(
        "<b>Telefon raqamingizni</b> kiriting yoki tugma orqali <b>ulashing</b>:\n"
        "<i>(Namuna: +998901234567)</i>",
        reply_markup=phone_keyboard,
        parse_mode="HTML"
    )
    await state.set_state(StudentForm.phone)


@dp.message(StudentForm.phone)
async def student_phone_handler(message: types.Message, state: FSMContext):
    phone_number = None
    if message.contact:
        phone_number = message.contact.phone_number
        if not phone_number.startswith("+"):
            phone_number = "+" + phone_number
    elif message.text:
        text = message.text.replace(" ", "").strip()
        if re.match(r'^\+?\d{9,15}$', text):
            phone_number = text if text.startswith("+") else "+" + text

    if not phone_number:
        await message.answer(
            "Iltimos, telefon raqamini to'g'ri formatda kiriting (+998...) yoki tugma orqali ulashing.",
            reply_markup=phone_keyboard
        )
        return
    
    await state.update_data(phone=phone_number)
    await message.answer(
        "Endi <b>viloyatingizni</b> tanlang:",
        reply_markup=region_buttons,
        parse_mode="HTML"
    )
    await state.set_state(StudentForm.address_region)


@dp.message(StudentForm.address_region)
async def student_address_region_handler(message: types.Message, state: FSMContext):
    region = message.text.strip()
    if region not in REGIONS_DISTRICTS:
        await message.answer("Iltimos, menyudagi tugmalardan viloyatni tanlang.", reply_markup=region_buttons)
        return
    
    await state.update_data(address_region=region)
    district_keyboard = create_district_keyboard(region)
    await message.answer(
        f"Siz <b>{region}</b> viloyatini tanladingiz.\nEndi <b>tuman yoki shaharni</b> tanlang:",
        reply_markup=district_keyboard,
        parse_mode="HTML"
    )
    await state.set_state(StudentForm.address_district)


@dp.message(StudentForm.address_district)
async def student_address_district_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    region = data.get('address_region')
    district = message.text.strip()

    if region not in REGIONS_DISTRICTS or district not in REGIONS_DISTRICTS[region]:
        await message.answer("Iltimos, ro'yxatdagi tuman/shaharlardan birini tanlang.")
        return

    await state.update_data(address_district=district)
    await message.answer(
        "<b>Kompyuter va dasturlarda ishlash tajribangiz bormi?</b>\n"
        "<i>(Masalan: AutoCAD, CorelDRAW, Excel yoki oddiy foydalanuvchi)</i>",
        reply_markup=cancel_only_keyboard,
        parse_mode="HTML"
    )
    await state.set_state(StudentForm.computer_skill)


@dp.message(StudentForm.computer_skill)
async def student_computer_skill_handler(message: types.Message, state: FSMContext):
    await state.update_data(computer_skill=message.text.strip())
    await message.answer(
        "<b>Qachondan ish boshlay olasiz?</b>\n"
        "<i>(Masalan: Ertadan / Bir haftada)</i>",
        reply_markup=cancel_only_keyboard,
        parse_mode="HTML"
    )
    await state.set_state(StudentForm.start_date)


@dp.message(StudentForm.start_date)
async def student_start_date_handler(message: types.Message, state: FSMContext):
    await state.update_data(start_date=message.text.strip())
    await message.answer(
        "Boshqa <b>qo'shimcha savol</b> yoki <b>takliflaringiz</b> bo'lsa yozing:\n"
        "<i>(Agar bo'lmasa: <b>\"Yo'q\"</b> deb yozing)</i>",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Yo'q"), KeyboardButton(text=CANCEL_BUTTON)]],
            resize_keyboard=True
        ),
        parse_mode="HTML"
    )
    await state.set_state(StudentForm.additional)


@dp.message(StudentForm.additional)
async def student_additional_handler(message: types.Message, state: FSMContext):
    await state.update_data(additional=message.text.strip())
    data = await state.get_data()
    await state.set_state(StudentForm.submitting)

    full_address = f"{data.get('address_region', 'Kiritilmagan')} viloyati, {data.get('address_district', 'Kiritilmagan')}"

    application_text = (
        f"👨‍🎓 <b>YANGI SHOGIRD (ROVERCHI) ANKETASI</b> 👨‍🎓\n\n"
        f"<b>🆔 Telegram ID:</b> <code>{message.from_user.id}</code>\n"
        f"<b>👤 Nomzod:</b> {data.get('name_surname', 'Kiritilmagan')}\n"
        f"<b>🎂 Yoshi:</b> {data.get('age', 'Kiritilmagan')}\n"
        f"<b>📱 Telefon:</b> <code>{data.get('phone', 'Kiritilmagan')}</code>\n"
        f"<b>🏠 Manzil:</b> {full_address}\n"
        f"────────────────────\n"
        f"<b>💻 Kompyuter bilimi:</b> {data.get('computer_skill', 'Kiritilmagan')}\n"
        f"<b>📅 Ish boshlash:</b> {data.get('start_date', 'Kiritilmagan')}\n"
        f"<b>💬 Qo'shimcha:</b> {data.get('additional', 'Kiritilmagan')}\n"
        f"<b>📌 Yo'nalish:</b> Shogird (Roverchi)"
    )

    sheets_data = {
        "Sana": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Foydalanuvchi ID": message.from_user.id,
        "Ism va Familya": data.get('name_surname'),
        "Yoshi": data.get('age'),
        "Telefon": data.get('phone'),
        "Viloyat": data.get('address_region'),
        "Tuman/Shahar": data.get('address_district'),
        "Kompyuter bilimi": data.get('computer_skill'),
        "Ish boshlash sanasi": data.get('start_date'),
        "Qo'shimcha": data.get('additional'),
        "Vakansiya": "Shogird (Roverchi)"
    }

    sheets_success = await send_data_to_sheets(sheets_data, "Roverchi")
    admin_success = await notify_recipients(application_text)

    if admin_success or sheets_success:
        await message.answer(
            "✅ Arizangiz muvaffaqiyatli qabul qilindi 😊\nTez orada siz bilan bog'lanamiz.",
            reply_markup=main_menu
        )
    else:
        await message.answer(
            "⚠️ Arizani yuborishda texnik xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.",
            reply_markup=main_menu
        )

    await state.clear()


# =====================================================================
# --- Botni ishga tushirish ---
# =====================================================================

async def main():
    logging.info("🚀 Elshift Bot ishga tushmoqda...")
    # Eski yangilanishlarni (updates) tashlab yuborish
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("🛑 Bot to‘xtatildi.")