import asyncio
import re
import logging
import aiohttp # Google Sheets API ga ma'lumot yuborish uchun kerak

from datetime import datetime  # 🟢 Shu qatorni qo‘shing

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, FSInputFile,
    InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

# Konfiguratsiya faylidan sozlamalarni yuklash
try:
    # 'config' faylini bir xil joyda joylashtiring
    from config import Config
except ImportError:
    logging.error("config.py fayli topilmadi yoki import qilinmadi. Iltimos, fayl mavjudligiga ishonch hosil qiling.")
    raise SystemExit(1)

# --- Logging sozlamalari ---
# Barcha xato va axborot xabarlarini terminalda ko'rsatish
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Bot va Dispatcher yaratish ---
# Konfiguratsiyadan olingan BOT_TOKEN va ADMIN_ID dan foydalanamiz
# Yangi (to'g'ri) usul
bot = Bot(
    token=Config.BOT_TOKEN, 
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher(storage=MemoryStorage())

DEFAULT_ERROR_MSG = "Noma'lum xato"

# --- Mintaqa va Tuman/Shaharlar ma'lumotlar bazasi ---
REGIONS_DISTRICTS = {
    "Farg'ona": [
        "Farg'ona shahar", "Marg'ilon shahar", "Qo'qon shahar", "Quvasoy shahar",
        "Qo'shtepa tumani", "Bag'dod tumani", "Beshariq tumani", "Buvayda tumani",
        "Dang'ara tumani", "Farg'ona tumani", "Furqat tumani", "Oltiariq tumani",
        "Quva tumani", "Rishton tumani", "So'x tumani", "Toshloq tumani",
        "Uchko'prik tumani", "Yozyovon tumani"
    ],
    "Andijon": [
        "Andijon shahar", "Andijon tumani", "Asaka tumani", "Baliqchi tumani",
        "Bo'z tumani", "Buloqboshi tumani", "Izboskan tumani", "Jalaquduq tumani",
        "Qo'rg'ontepa tumani", "Marhamat tumani", "Oltinko'l tumani", "Paxtaobod tumani",
        "Ulug'nor tumani", "Xo'jaobod tumani", "Shahrixon tumani"
    ],
    "Namangan": [
        "Namangan shahar", "Chortoq tumani", "Chust tumani", "Kosonsoy tumani",
        "Mingbuloq tumani", "Namangan tumani", "Norin tumani", "Pop tumani",
        "To'raqo'rg'on tumani", "Uchqo'rg'on tumani", "Uychi tumani", "Yangiqo'rg'on tumani"
    ]
}

# --- FSM States for Ish o'rganuvchilar Anketasi (ApprenticeForm) ---
class ApprenticeForm(StatesGroup):
    name_surname = State()
    age = State()
    phone = State()
    address_region = State()
    address_district = State()
    previous_job = State()
    previous_salary = State()
    reason_left = State()
    expected_salary = State()
    goal = State()
    math_skill = State()          # 🆕 Yangi qo‘shildi
    hardworking = State()
    start_date = State()
    additional = State()
    submitting = State()

# --- FSM States for ROVERCHI Anketasi (StudentForm) ---
class StudentForm(StatesGroup):
    name_surname = State()
    age = State()
    phone = State()
    address_region = State()
    address_district = State()
    previous_job = State()
    previos_salary = State()
    reason_left = State()
    computer_skill = State()
    start_date = State()
    additional = State()
    submitting = State()

# --- FSM States for Ustalar Anketasi (MasterForm) ---
class MasterForm(StatesGroup):
    name_surname = State()
    age = State()
    phone = State()
    address_region = State()
    address_district = State()
    specialty = State()
    experience_years = State()
    team_management = State()
    portfolio_link = State()      # Fayl / havola yuborish
    more_portfolio = State()      # “Yana portfolio yuborasizmi?” savoli
    expected_salary_usta = State()
    hardworking_usta = State()
    start_date_usta = State()
    submitting = State()

# --- Matn va Havolalar ---
ELSHIFT_ABOUT = (
    "<b>«Elshift» qanday brend?</b>\n\n"
    "<b>Elshift</b> — bu alukabond xizmati bilan shugʻillanuvchi kompaniya hisoblanadi, biz 12 yildan buyon xalqimizga alukabond xizmatini koʻrsatib kelyapmiz!\n\n"
    "Bizni qadriyatimiz:\n\n"
    "<b>Mijozlarga oʻz vaqtida va sifatli xizmat koʻrsatish - bu bizning eng asosiy tamoyilimiz.</b>\n\n"
    "Elshift - tanlovingizni oqlaydigan sifatli va ishonchli alukabond xizmati!\n\n"
    "<i>Yuqoridagi videoni koʻrib kompaniya  haqida ma'lumotlarni  rahbardan bilib olishingiz mumkin!</i>\n"
)

# --- Umumiy Tugmalar ---
BACK_BUTTON = "🔙 Orqaga"
CANCEL_BUTTON = "Bekor qilish"
JOB_TITLE_APPRENTICE = "👨‍🎓 Ish o'rganuvchi"
JOB_TITLE_MASTER = "👷 Usta"
JOB_TITLE_ROVER = "👨‍🎓 Shogird (Roverchi)"

# --- Tugmalar (asosiy menyu) ---
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏢 Biz haqimizda"), KeyboardButton(text="💼 Bo'sh ish o'rinlari")],
        [KeyboardButton(text="📍 Manzil")],
    ],
    resize_keyboard=True
)

# --- "Bo'sh ish o'rinlari" menyusi ---
jobs_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=JOB_TITLE_MASTER),
         KeyboardButton(text=JOB_TITLE_APPRENTICE)],
        #  [KeyboardButton(text=JOB_TITLE_ROVER)]
        [KeyboardButton(text=BACK_BUTTON)]
    ],
    resize_keyboard=True
)

# --- "Ishdan ketish sababi" uchun tugmalar ---
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

# --- "Ha / Yo'q" uchun tugmalar ---
yes_no_buttons = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Ha"), KeyboardButton(text="Yo'q")],
        [KeyboardButton(text=CANCEL_BUTTON)]
    ],
    resize_keyboard=True
)

# --- Telefon raqam kiritish/ulashish klaviaturasi ---
phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📞 Raqamni ulashish", request_contact=True)],
        [KeyboardButton(text=CANCEL_BUTTON)]
    ],
    resize_keyboard=True
)

# --- Yordamchi funksiya: Tumanlar klaviaturasini yaratish ---
def create_district_keyboard(region_name: str) -> ReplyKeyboardMarkup:
    """Berilgan viloyat uchun tuman/shaharlar tugmalarini yaratadi."""
    districts = REGIONS_DISTRICTS.get(region_name, [])
    keyboard_rows = []
    
    # 2 tadan joylashtirish
    for i in range(0, len(districts), 2):
        row = [KeyboardButton(text=districts[i])]
        if i + 1 < len(districts):
            row.append(KeyboardButton(text=districts[i+1]))
        keyboard_rows.append(row)
    
    keyboard_rows.append([KeyboardButton(text=CANCEL_BUTTON)])
    
    return ReplyKeyboardMarkup(keyboard=keyboard_rows, resize_keyboard=True)

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

# --- Restart ---
@dp.message(Command("restart"))
async def restart_handler(message: types.Message, state: FSMContext):
    # 1️⃣ Har qanday holatda state (holat)ni tozalaymiz
    await state.clear()

    # 2️⃣ Foydalanuvchiga qayta start holatini chiqaramiz
    await message.answer(
        "🔄 Bot qayta ishga tushirildi!\n\n"
        "Quyidagi menyudan kerakli bo‘limni tanlang 👇",
        reply_markup=main_menu  # sizning asosiy menyuingiz
    )

# --- Google Sheets ga ma'lumot yuborish uchun soddalashtirilgan funksiya ---
async def send_data_to_sheets(data: dict, sheet_name: str) -> bool:
    """
    Ma'lumotlarni Google Sheets ga yuboradi (Apps Script Web App orqali).
    Faqat 200 status keldi va 'success' bo'lsa True qaytaradi.
    """

    if not Config.SHEETS_API_URL or not Config.SHEETS_API_TOKEN:
        logging.error("❌ Config.SHEETS_API_URL yoki Config.SHEETS_API_TOKEN belgilanmagan.")
        return False

    # Google Apps Script Web App'ga yuboriladigan ma'lumot
    payload = {
        "token": Config.SHEETS_API_TOKEN,  # 🔥 Token qo‘shildi!
        "sheet": sheet_name,
        "data": data
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(Config.SHEETS_API_URL, json=payload, timeout=15) as response:
                text = await response.text()
                if response.status == 200:
                    try:
                        result = await response.json()
                        if result.get("status") == "success":
                            logging.info(f"✅ Ma'lumotlar '{sheet_name}' jadvaliga yuborildi.")
                            return True
                        else:
                            logging.error(f"⚠️ Sheets javobi: {result}")
                            return False
                    except Exception:
                        logging.info(f"📄 Sheets javobi (text): {text}")
                        if "success" in text.lower():
                            return True
                        return False
                else:
                    logging.error(f"❌ Sheets API xato status: {response.status} | Javob: {text}")
                    return False

    except Exception as e:
        logging.error(f"❌ Sheets ga yuborishda xatolik: {e}")
        return False

# --- Handlers (Global Logika) ---

@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Assalomu alaykum!\n\n"
                         "<b>«Elshift»</b> rasmiy botiga xush kelibsiz! Asosiy menyu orqali boʻlimlardan birini tanlang 👇",
                         reply_markup=main_menu)
    
@dp.message(F.text == "/chatid")
async def get_chat_id(message: types.Message):
    await message.answer(f"Chat ID: <code>{message.chat.id}</code>", parse_mode="HTML")

@dp.message(Command("adminid"))
async def send_my_id(message: types.Message):
    user_id = message.from_user.id
    await message.answer(f"Sizning Telegram ID'ingiz: <code>{user_id}</code>", parse_mode="HTML")

# BACK_BUTTON handler
@dp.message(F.text == BACK_BUTTON)
async def back_handler_global(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyuga qaytdingiz 👇", reply_markup=main_menu)

# CANCEL_BUTTON handler
@dp.message(F.text == CANCEL_BUTTON, F.fsm_context.in_state(ApprenticeForm) | F.fsm_context.in_state(MasterForm))
async def cancel_handler_in_form(message: types.Message, state: FSMContext):
    # Anketa holatini tozalaydi
    await state.clear()
    # Foydalanuvchini asosiy menyuga qaytaradi
    await message.answer("Anketa bekor qilindi. Asosiy menyuga qaytdingiz 👇", reply_markup=main_menu)

# --- Biz haqimizda ---
@dp.message(F.text == "🏢 Biz haqimizda")
async def about_handler(message: types.Message):
    try:
        # 🎬 Telegram serverida saqlangan videoning file_id'si
        # ⚠️ Quyidagi file_id ni o'z videongiznikiga almashtiring
        video_file_id = "BAACAgIAAyEFAAS6OEd7AAMQaPW4c5h75xhbCwer3puhLa8VzJAAAmCKAAKEzKlLmSJO0p8oaUQ2BA"
        #BAACAgIAAyEFAAS6OEd7AAMaaPX8zzofZLvfM093D9-EA2NB-WwAAmCKAAKEzKlLW5YHi2VVLlc2BA

        # 📩 Video yuborish
        await message.answer_video(
            video=video_file_id,
            caption=ELSHIFT_ABOUT,
            reply_markup=social_media_keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        logging.error(f"'Biz haqimizda' xabarini yuborishda xatolik: {e}")
        # Agar video yuborishda xatolik bo'lsa, faqat matn yuboriladi
        await message.answer(ELSHIFT_ABOUT, parse_mode="HTML")

# @dp.message(F.video)
# async def get_file_id(message: types.Message):
    # await message.answer(f"🎬 file_id:\n<code>{message.video.file_id}</code>", parse_mode="HTML")

# Bo'sh ish o'rinlari
@dp.message(F.text == "💼 Bo'sh ish o'rinlari")
async def jobs_handler(message: types.Message):
    await message.answer("👷 <b>Usta</b> - Tajribangiz bo'lsa, tayyor obyektlar va bonusli ish sizni kutmoqda.\n\n👨‍🎓 <b>Ish o'rganuvchi</b> - 6 - 12 oyda usta bo'lib, <b>Elshift</b> jamoasida o'z o'rningizga ega bo'ling.\n\n👇 Quyidagilardan birini tanlang.",
                         reply_markup=jobs_menu)

# Aloqa
@dp.message(F.text == "📍 Manzil")
async def contact_handler(message: types.Message):
    text = (
        "📍 <b>Manzil:</b> <a href='https://maps.app.goo.gl/rE3iPvTM4Z3ezf1h7'>Farg'ona viloyati, Marg'ilon shahri</a>\n"
        "🕒 <b>Ish vaqti:</b> 09:00 – 18:00\n"
        "☪️ <b>Dam olish kuni:</b> Juma"
    )
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)

# ===============================================
# --- 🧑‍🎓 ISH O'RGANUVCHILAR ANKETASI (APPRENTICE) ---
# ===============================================

@dp.message(F.text == JOB_TITLE_APPRENTICE)
async def trainees_handler(message: types.Message, state: FSMContext):
    initial_form_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_BUTTON)]], resize_keyboard=True
    )
    # 1-savol
    await message.answer("Ish o'rganuvchilar anketasini to'ldirishni boshlaymiz.\n\n"
                         "Iltimos, <b>Ism va familyangizni</b> yozing:",
                         reply_markup=initial_form_keyboard,
                         parse_mode="HTML")
    await state.set_state(ApprenticeForm.name_surname)

# --- 1. Ism va familya (ApprenticeForm) ---
@dp.message(ApprenticeForm.name_surname)
async def app_name_handler(message: types.Message, state: FSMContext):
    await state.update_data(name_surname=message.text)
    
    # 2-savol: Yosh kiritish bosqichi
    await message.answer("<b>Yoshingiz nechchida?</b>\n"
                         "<b>(Iltimos, faqat raqam bilan kiriting)</b>",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text=CANCEL_BUTTON)]], resize_keyboard=True
                         ),
                         parse_mode="HTML")
    await state.set_state(ApprenticeForm.age)

# --- 2. Yoshingiz (ApprenticeForm) ---
@dp.message(ApprenticeForm.age)
async def app_age_handler(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit() or not (16 <= int(text) <= 60):
        await message.answer("Iltimos, yoshingizni faqat raqamlarda kiriting (Masalan: 21) va 18 yoshdan katta bo'lsin.")
        return
        
    await state.update_data(age=text)

    # 3-savol: Telefon raqami
    await message.answer("<b>Telefon raqamingizni</b> kiriting yoki tugma orqali <b>ulashing</b>:\n"
                         "<b>(Misol: +998901234567)</b>",
                         reply_markup=phone_keyboard,
                         parse_mode="HTML")
    await state.set_state(ApprenticeForm.phone)

# --- 3. Telefon raqami (ApprenticeForm) ---
@dp.message(ApprenticeForm.phone)
async def app_phone_handler(message: types.Message, state: FSMContext):
    
    phone_number = None
    if message.contact:
        phone_number = message.contact.phone_number
    elif message.text:
        text = message.text.replace(" ", "").strip()
        # Oddiy telefon raqam validatsiyasi
        if re.match(r'^\+?\d{9,15}$', text):
            phone_number = text
        
    if not phone_number:
        await message.answer("Iltimos, telefon raqamini to'g'ri formatda kiriting (+998...) yoki tugma orqali ulashing.")
        return

    await state.update_data(phone=phone_number)
    
    # 4-savol: Viloyat tanlash
    region_buttons = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Farg'ona"), KeyboardButton(text="Andijon")],
            [KeyboardButton(text="Namangan")],
            [KeyboardButton(text=CANCEL_BUTTON)]
        ],
        resize_keyboard=True
    )
    await message.answer("Endi <b>viloyatingizni</b> tanlang:", reply_markup=region_buttons, parse_mode="HTML")
    await state.set_state(ApprenticeForm.address_region)

# --- 4. Manzil (Viloyat tanlash - ApprenticeForm) ---
@dp.message(ApprenticeForm.address_region)
async def app_address_region_handler(message: types.Message, state: FSMContext):
    region = message.text
    if region not in REGIONS_DISTRICTS:
        await message.answer("Iltimos, menyudagi tugmalardan viloyatni tanlang.")
        return
        
    await state.update_data(address_region=region)
    district_keyboard = create_district_keyboard(region)

    # 5-savol: Tuman/shahar tanlash
    await message.answer(f"Siz <b>{region}</b>ni tanladingiz.\n"
                         f"Endi <b>tuman yoki shaharni</b> tanlang:",
                         reply_markup=district_keyboard,
                         parse_mode="HTML")
    await state.set_state(ApprenticeForm.address_district)

# --- 5. Manzil (Tuman/shahar tanlash - ApprenticeForm) ---
@dp.message(ApprenticeForm.address_district)
async def app_address_district_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    region = data.get('address_region')
    district = message.text

    if region not in REGIONS_DISTRICTS or district not in REGIONS_DISTRICTS[region]:
        await message.answer("Iltimos, ro'yxatdagi tuman/shaharlardan birini tanlang.")
        return
        
    # address_district ga faqat tumanni saqlaymiz (Viloyat 'address_region' da saqlangan)
    await state.update_data(address_district=district) 
    
    # 6-savol: Avvalgi ish
    await message.answer("<b>Avval qayerda ishlagansiz va nima ish qilgansiz?</b>\n"
                         "Iltimos, <b>Ovozli</b> xabar jo'nating yoki ishlamaganman deb yozing.", 
                         reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_BUTTON)]], resize_keyboard=True
    ), parse_mode="HTML")
    await state.set_state(ApprenticeForm.previous_job)

# --- 6. Avvalgi ish (ApprenticeForm) ---
@dp.message(ApprenticeForm.previous_job)
async def app_previous_job_handler(message: types.Message, state: FSMContext):
    try:
        # 🔹 Matnli javob
        if message.text:
            previous_job = message.text.strip()
            await state.update_data(previous_job=previous_job)

            # Agar "ishlamaganman" deb yozgan bo‘lsa
            if previous_job.lower() in ["ishlamaganman", "yo'q", "yoq"]:
                await state.update_data(previous_salary="Kiritilmagan")
                await state.update_data(reason_left="Kiritilmagan")

                # 🔸 To‘g‘ridan-to‘g‘ri kutayotgan oylikka o‘tamiz
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

                await message.answer(
                    "Qaysi oylik sizni qoniqtiradi?\nTanlang yoki yozing.",
                    reply_markup=expected_salary_buttons,
                    parse_mode="HTML"
                )
                await state.set_state(ApprenticeForm.expected_salary)
                return

            # 🔹 Aks holda avvalgi ish uchun oylik so‘raladi
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
                "Avvalgi ish joyingizda oyligingiz qancha edi?\nTanlang yoki yozing.",
                reply_markup=salary_buttons,
                parse_mode="HTML"
            )
            await state.set_state(ApprenticeForm.previous_salary)
            return

        # 🔹 Ovozli javob
        elif message.voice:
            for group_id in Config.GROUP_IDS:
                if group_id == 0:
                    await message.answer("⚠️ Guruh ID noto‘g‘ri yoki o‘rnatilmagan.")
                    return

            file_id = message.voice.file_id
            voice_link = None

            # Guruhga yuborish
            for group_id in Config.GROUP_IDS:
                try:
                    sent = await bot.send_voice(
                        chat_id=group_id,
                        voice=file_id,
                        caption=f"🎤 Ovozli javob {message.from_user.full_name} dan"
                    )
                    voice_link = f"https://t.me/c/{str(group_id)[4:]}/{sent.message_id}"
                except Exception as e:
                    logging.error(f"Ovozli javobni guruhga yuborishda xatolik: {e}")
                    await message.answer("❌ Ovozli javobni yuborishda xatolik yuz berdi.")
                    return

            await state.update_data(previous_job=voice_link)
            await message.answer("✅ Ovozli javob qabul qilindi va guruhga yuborildi.")

            # Keyingi bosqich: avvalgi oylik
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
                "Avvalgi ish joyingizda oyligingiz qancha edi?\nTanlang yoki yozing.",
                reply_markup=salary_buttons,
                parse_mode="HTML"
            )
            await state.set_state(ApprenticeForm.previous_salary)
            return

        # 🔹 Boshqa turdagi xabarlar (rasm, fayl va hokazo)
        else:
            await message.answer("❌ Faqat matn yoki ovozli xabar yuborish mumkin. Iltimos, qayta urinib ko‘ring.")
            return

    except Exception as e:
        logging.error(f"Avvalgi ish javobini qabul qilishda xatolik: {e}")
        await message.answer("⚠️ Xatolik yuz berdi. Iltimos, qayta urinib ko‘ring.")

# --- 7. Avvalgi oylik (ApprenticeForm) ---
@dp.message(ApprenticeForm.previous_salary)
async def app_previous_salary_handler(message: types.Message, state: FSMContext):
    await state.update_data(previous_salary=message.text)
    
    # 8-savol: Ishdan ketish sababi
    await message.answer("Avvalgi ishdan nima sababdan ketdingiz?", reply_markup=reason_left_buttons)
    await state.set_state(ApprenticeForm.reason_left)

# --- 8. Sabab ketish (ApprenticeForm) ---
@dp.message(ApprenticeForm.reason_left)
async def app_reason_handler(message: types.Message, state: FSMContext):
    await state.update_data(reason_left=message.text)
    
    # 9-savol: Kutayotgan oylik
    expected_salary_buttons = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1,000,000 so'm"), KeyboardButton(text="1,500,000 so'm")],
            [KeyboardButton(text="2,000,000 so'm"), KeyboardButton(text="2,500,000 so'm")],
            [KeyboardButton(text="3,000,000 so'm"), KeyboardButton(text="4,000,000 so'm")],
            [KeyboardButton(text="5,000,000+ so'm"), KeyboardButton(text="Oylik muhim emas")],
            [KeyboardButton(text="Boshqa summa")],
            [KeyboardButton(text=CANCEL_BUTTON)]
        ], resize_keyboard=True
    )
    await message.answer("Biz bilan ishlashda <b>qancha oylik kutyapsiz</b>?\n"
                         "<b>(Tanlang yoki yozing)</b>",
                         reply_markup=expected_salary_buttons,
                         parse_mode="HTML")
    await state.set_state(ApprenticeForm.expected_salary)

# --- 9. Kutayotgan oylik (ApprenticeForm) ---
@dp.message(ApprenticeForm.expected_salary)
async def app_expected_salary_handler(message: types.Message, state: FSMContext):
    await state.update_data(expected_salary=message.text)

    # 9.1. savol: Matematika (faqat ovozli xabar)
    await message.answer(
        "<b>Matematikani qanchalik bilasiz?</b>\n"
        "(Gradus, metr, sm, kvadrat va boshqa xisob kitoblar bilan ishlash)\n\n"
        "Iltimos, <b>ovozi orqali javob yuboring</b> yoki <b>Yo'q</b> tugmasini bosing.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Yo'q"), KeyboardButton(text=CANCEL_BUTTON)]
            ],
            resize_keyboard=True,
        ),  # faqat Ha/Yo'q tugmalari bilan
        parse_mode="HTML"
    )
    await state.set_state(ApprenticeForm.math_skill)

# --- 9.1. Matematika (ApprenticeForm) ---
@dp.message(ApprenticeForm.math_skill)
async def app_math_skill_handler(message: types.Message, state: FSMContext):
    try:
        # 🔹 Agar ovozli xabar bo‘lsa
        if message.voice:
            file_id = message.voice.file_id

            # Guruhga yuborish
            for group_id in Config.GROUP_IDS:
                sent = await bot.send_voice(
                    chat_id=group_id,
                    voice=file_id,
                    caption=f"🎤 Matematikaga javob {message.from_user.full_name} dan"
                )

                # Telegramdagi havolani saqlaymiz
                voice_link = f"https://t.me/c/{str(group_id)[4:]}/{sent.message_id}"
                await state.update_data(math_skill=voice_link)

            await message.answer("✅ Ovozli javob qabul qilindi. Endi davom etamiz.")
            # Keyingi bosqichga o'tish
            await message.answer(
                "<b>Hunar o'rganishdan maqsadingiz</b> nima?\nIltimos yozing.",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text=CANCEL_BUTTON)]],
                    resize_keyboard=True
                ),
                parse_mode="HTML"
            )
            await state.set_state(ApprenticeForm.goal)
            return

        # 🔹 Agar matn bo‘lsa, faqat "Yo'q" ni qabul qilamiz
        elif message.text and message.text == "Yo'q":
            await state.update_data(math_skill=message.text)
            await message.answer(
                "<b>Hunar o'rganishdan maqsadingiz</b> nima?\nIltimos yozing.",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text=CANCEL_BUTTON)]],
                    resize_keyboard=True
                ),
                parse_mode="HTML"
            )
            await state.set_state(ApprenticeForm.goal)
            return

        # 🔹 Boshqa matn yuborilsa
        else:
            await message.answer(
                "❌ Iltimos, faqat ovozli xabar yuboring yoki 'Yo'q' tugmasini bosing.",
                parse_mode="HTML"
            )
            return

    except Exception as e:
        logging.error(f"Matematika javobini qabul qilishda xatolik: {e}")
        await message.answer("⚠️ Xatolik yuz berdi, iltimos qayta urinib ko‘ring.")

# --- 10. Maqsad (ApprenticeForm) ---
@dp.message(ApprenticeForm.goal)
async def app_goal_handler(message: types.Message, state: FSMContext):
    await state.update_data(goal=message.text)
    
    # 11-savol: Baland joyda ishlash
    await message.answer(
        "Oldin lesada yoki baland joylarda ishlaganmisiz?\n"
        "Agar ish joyi balandroq bo‘lsa, bunga tayyormisiz?\n\n"
        "<i>Masalan:</i>\n"
        "— Ha, ishlaganman\n"
        "— Yo‘q, lekin sinab ko‘rmoqchiman\n"
        "— Baland joydan qo‘rqaman",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=CANCEL_BUTTON)]],
            resize_keyboard=True
        ),
        parse_mode="HTML"
    )
    await state.set_state(ApprenticeForm.hardworking)


# --- 11. Baland joyda ishlash savoli (ApprenticeForm) ---
@dp.message(ApprenticeForm.hardworking)
async def app_hardworking_handler(message: types.Message, state: FSMContext):
    hardworking = message.text.strip()
    await state.update_data(hardworking=hardworking)

    # 12-savol: Ish boshlash
    await message.answer(
        "<b>Qachondan ish boshlay olasiz?</b>\n"
        "<i>Masalan:</i> Ertadan / Bir haftada / Dushanbadan",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=CANCEL_BUTTON)]],
            resize_keyboard=True
        ),
        parse_mode="HTML"
    )
    await state.set_state(ApprenticeForm.start_date)

# --- 12. Ish boshlash (ApprenticeForm) ---
@dp.message(ApprenticeForm.start_date)
async def app_start_date_handler(message: types.Message, state: FSMContext):
    await state.update_data(start_date=message.text)
    
    # 13-savol: Qo'shimcha savollar va yakun
    await message.answer("Boshqa <b>qo'shimcha savol</b> yoki <b>takliflar</b> bo'lsa yozing.\n"
                         "<b>(Agar bo'lmasa: Yo'q)</b>", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Yo'q"), KeyboardButton(text=CANCEL_BUTTON)]], resize_keyboard=True
    ), parse_mode="HTML")
    await state.set_state(ApprenticeForm.additional)

# --- 13. Qo'shimcha savollar va yakun (ApprenticeForm SUBMIT) ---
@dp.message(ApprenticeForm.additional)
async def app_additional_handler(message: types.Message, state: FSMContext):
    await state.update_data(additional=message.text)
    data = await state.get_data()
    
    # Ma'lumot yuborish holatiga o'tish (ortiqcha bosishlarning oldini olish uchun)
    await state.set_state(ApprenticeForm.submitting)

    full_address = f"{data.get('address_region', 'Kiritilmagan')} viloyati, {data.get('address_district', 'Kiritilmagan')}"

    # Xabar matnini tuzish (Admin uchun)
    application_text = (
        f"🚨 <b>YANGI ISH O'RGANUVCHI ANKETASI</b> 🚨\n\n"
        f"<b>🆔 Foydalanuvchi ID:</b> <code>{message.from_user.id}</code>\n"
        f"<b>👤 Nomzod:</b> {data.get('name_surname', 'Kiritilmagan')}\n"
        f"<b>🎂 Yoshi:</b> {data.get('age', 'Kiritilmagan')}\n"
        f"<b>📱 Telefon:</b> <code>{data.get('phone', 'Kiritilmagan')}</code>\n"
        f"<b>🏠 Manzil:</b> {full_address}\n"
        f"--- Kasbiy ma'lumot ---\n"
        f"<b>💼 Avvalgi ish:</b> {data.get('previous_job', 'Kiritilmagan')}\n"
        f"<b>💰 Avvalgi oylik:</b> {data.get('previous_salary', 'Kiritilmagan')}\n"
        f"<b>❌ Ishdan ketish sababi:</b> {data.get('reason_left', 'Kiritilmagan')}\n"
        f"<b>💰 Kutayotgan oylik:</b> {data.get('expected_salary', 'Kiritilmagan')}\n"
        f"<b>🎯 Maqsad:</b> {data.get('goal', 'Kiritilmagan')}\n"
        f"<b>💪 Baland joyda ishlashga tayyor:</b> {data.get('hardworking', 'Kiritilmagan')}\n"
        f"<b>🧮 Matematikani biladi:</b> {data.get('math_skill', 'Kiritilmagan')}\n"
        f"<b>📅 Ish boshlash:</b> {data.get('start_date', 'Kiritilmagan')}\n"
        f"<b>💬 Qo'shimcha:</b> {data.get('additional', 'Kiritilmagan')}\n"
        f"<b>Vakansiya turi:</b> Ish o'rganuvchi"
    )

    # Google Sheets ga yuborish uchun lug'at
    sheets_data = {
        "Sana": str(datetime.now()),
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
    
    # 1. Google Sheets ga yuborish
    sheets_success = await send_data_to_sheets(sheets_data, "Shogird")

    # 2. Ma'murlarga xabar yuborish (bir nechta admin)
    admin_success = False
    for group_id in Config.GROUP_IDS:  # Config.GROUP_IDS = [8026404520, 6415901177]
        try:
            await bot.send_message(chat_id=group_id, text=application_text, parse_mode="HTML")
            admin_success = True
        except Exception as e:
            logging.error(f"Admin {group_id} ga yuborishda xatolik: {e}")

    # 3. Foydalanuvchiga xabar
    if sheets_success and admin_success:
        await message.answer(
            "✅ Arizangiz muvaffaqiyatli qabul qilindi 😊\n"
            "Ma’lumotlaringizni ko‘rib chiqamiz va mos bo‘lsangiz, albatta siz bilan bog‘lanamiz.",
            reply_markup=main_menu
        )
    elif sheets_success:
        await message.answer(
            "⚠️ Arizangiz ma'lumotlar bazasiga saqlandi, ammo ma'murlarga xabar yuborishda texnik xatolik yuz berdi. Tez orada aloqaga chiqishadi.",
            reply_markup=main_menu
        )
    else:
        await message.answer(
            "❌ Arizani yuborishda texnik xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring yoki ma'lumotlaringizni to'g'ridan-to'g'ri menejerga yuboring.",
            reply_markup=main_menu
        )

    await state.clear()

# ========================================
# --- 👨‍🎓 SHOGIRD ANKETASI (ROVERCHI) ---
# ========================================

@dp.message(F.text == JOB_TITLE_ROVER)
async def student_handler(message: types.Message, state: FSMContext):
    initial_form_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_BUTTON)]], resize_keyboard=True
    )
    # 1-savol
    await message.answer("Shogirdlar (Roverchi) anketasini to'ldirishni boshlaymiz.\n\n"
                         "Iltimos, <b>Ism va familyangizni</b> yozing:",
                         reply_markup=initial_form_keyboard,
                         parse_mode="HTML")
    await state.set_state(StudentForm.name_surname)

# -- 1. Ism va familya (StudentForm) ---
@dp.message(StudentForm.name_surname)
async def student_name_handler(message: types.Message, state: FSMContext):
    await state.update_data(name_surname=message.text)

    # 2-savol: Yosh
    await message.answer("Yoshingiz nechchida?\n"
                         "<b>(Iltimos, faqat raqam bilan kiriting)</b>\n",
                         "Yosh chegarasi: <b>30 yosh</b>",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text=CANCEL_BUTTON)]], resize_keyboard=True
                         ),
                         parse_mode="HTML")
    await state.set_state(StudentForm.age)

# --- 2. Yoshingiz (StudentForm) ---
@dp.message(StudentForm.age)
async def student_age_handler(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit() or not (16 <= int(text) <= 30):
        await message.answer("Iltimos, yoshingizni faqat raqamlarda kiriting (Masalan: 30) va 16 yoshdan katta bo'lsin.")
        return
    
    await state.update_data(age=text)

    # 3-savol: Telefon raqami
    await message.answer("<b>Telefon raqamingizni</b> kiriting yoki tugma orqali <b>ulashing</b>:\n"
                         "<b>(Namuna: +998901234567)</b>",
                         reply_markup=phone_keyboard,
                         parse_mode="HTML")
    await state.set_state(StudentForm.phone)

# --- 3. Telefon raqami (StudentForm) ---
@dp.message(StudentForm.phone)
async def student_phone_handler(message: types.Message, state: FSMContext):
    phone_number = None
    if message.contact:
        phone_number = message.contact.phone_number
    elif message.text:
        text = message.text.replace(" ", "").strip()
        if re.match(r'^\+?\d{9,15}$', text):
            phone_number = text

        if not phone_number:
            await message.answer("Iltimos, telefon raqamini to'g'ri formatda kiriting (+998...) yoki tugma orqali ulashing.")
            return
        
        await state.update_data(phone=phone_number)

        # 4-savol: Viloyat tanlash
        region_buttons = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Farg'ona"), KeyboardButton(text="Namangan")],
                [KeyboardButton(text="Andijon")],
                [KeyboardButton(text=CANCEL_BUTTON)]
            ],
            resize_keyboard=True
        )
        await message.answer("Endi <b>viloyatingizni</b> tanlang:", reply_markup=region_buttons, parse_mode="HTML")
        await state.set_state(StudentForm.address_region)

# --- 4. Manzil (Viloyat tanlash - StudentForm) ---
@dp.message(StudentForm.address_region)
async def student_address_region_handler(message: types.Message, state: FSMContext):
    region = message.text
    if region not in REGIONS_DISTRICTS:
        await message.answer("Iltimos, menyudagi tugmalardan viloyatni tanlang.")
        return
    
    await state.update_data(address_region=region)
    district_keyboard = create_district_keyboard(region)

    # 5-savol. Tuman/shahar tanlash
    await message.answer(f"Siz <b>{region}</b>ni tanladingiz.\n"
                         f"Endi <b> tuman yoki shaharni</b> tanlang:",
                         reply_markup=district_keyboard,
                         parse_mode="HTML")
    await state.set_state(StudentForm.address_district)

# ======================================
# --- 👷 USTALAR ANKETASI (MASTER) ---
# ======================================

@dp.message(F.text == JOB_TITLE_MASTER)
async def masters_handler(message: types.Message, state: FSMContext):
    initial_form_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_BUTTON)]], resize_keyboard=True
    )
    # 1-savol
    await message.answer("Ustalar anketasini to'ldirishni boshlaymiz.\n\n"
                         "Iltimos, <b>Ism va familyangizni</b> yozing:",
                         reply_markup=initial_form_keyboard,
                         parse_mode="HTML")
    await state.set_state(MasterForm.name_surname)

# --- 1. Ism va familya (MasterForm) ---
@dp.message(MasterForm.name_surname)
async def master_name_handler(message: types.Message, state: FSMContext):
    await state.update_data(name_surname=message.text)
    
    # 2-savol: Yosh
    await message.answer("<b>Yoshingiz nechchida?</b>\n"
                         "(Iltimos, faqat <b>raqam</b> bilan kiriting)",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text=CANCEL_BUTTON)]],
                             resize_keyboard=True
                         ),
                         parse_mode="HTML")
    await state.set_state(MasterForm.age)

# --- 2. Yoshingiz (MasterForm) ---
@dp.message(MasterForm.age)
async def master_age_handler(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit() or not (18 <= int(text) <= 65):
        await message.answer("Iltimos, yoshingizni faqat raqamlarda kiriting (Masalan: 30) va 18 yoshdan katta bo'lsin.")
        return
        
    await state.update_data(age=text)

    # 3-savol: Telefon raqami
    await message.answer("<b>Telefon raqamingizni</b> kiriting yoki tugma orqali <b>ulashing</b>:\n"
                         "<b>(Misol: +998901234567)</b>",
                         reply_markup=phone_keyboard,
                         parse_mode="HTML")
    await state.set_state(MasterForm.phone)

# --- 3. Telefon raqami (MasterForm) ---
@dp.message(MasterForm.phone)
async def master_phone_handler(message: types.Message, state: FSMContext):
    phone_number = None
    if message.contact:
        phone_number = message.contact.phone_number
    elif message.text:
        text = message.text.replace(" ", "").strip()
        if re.match(r'^\+?\d{9,15}$', text):
            phone_number = text
        
    if not phone_number:
        await message.answer("Iltimos, telefon raqamini to'g'ri formatda kiriting (+998...) yoki tugma orqali ulashing.")
        return

    await state.update_data(phone=phone_number)
    
    # 4-savol: Viloyat tanlash
    region_buttons = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Farg'ona"), KeyboardButton(text="Andijon")],
            [KeyboardButton(text="Namangan")],
            [KeyboardButton(text=CANCEL_BUTTON)]
        ],
        resize_keyboard=True
    )
    await message.answer("Endi <b>viloyatingizni</b> tanlang:", reply_markup=region_buttons, parse_mode="HTML")
    await state.set_state(MasterForm.address_region)

# --- 4. Manzil (Viloyat tanlash - MasterForm) ---
@dp.message(MasterForm.address_region)
async def master_address_region_handler(message: types.Message, state: FSMContext):
    region = message.text
    if region not in REGIONS_DISTRICTS:
        await message.answer("Iltimos, yuqoridagi tugmalardan viloyatni tanlang.")
        return
        
    await state.update_data(address_region=region)
    district_keyboard = create_district_keyboard(region)

    # 5-savol: Tuman/shahar tanlash
    await message.answer(f"Siz <b>{region}</b>ni tanladingiz.\n"
                         f"Endi <b>tuman yoki shaharni</b> tanlang:",
                         reply_markup=district_keyboard,
                         parse_mode="HTML")
    await state.set_state(MasterForm.address_district)

# --- 5. Manzil (Tuman/shahar tanlash - MasterForm) ---
@dp.message(MasterForm.address_district)
async def master_address_district_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    region = data.get('address_region')
    district = message.text

    if region not in REGIONS_DISTRICTS or district not in REGIONS_DISTRICTS[region]:
        await message.answer("Iltimos, ro'yxatdagi tuman/shaharlardan birini tanlang.")
        return
        
    # address_district ga faqat tumanni saqlaymiz (Viloyat 'address_region' da saqlangan)
    await state.update_data(address_district=district)
    
    # 6-savol: Mutaxassislik
    await message.answer("Sizning <b>asosiy mutaxassisligingiz</b> nima?\n"
                         "Kim bo'lib ishlaysiz?\n\n"
                         "Iltimos, to'liq yozing, namuna: <b>Alukabond montajchi</b>",
                         reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_BUTTON)]], resize_keyboard=True
    ), parse_mode="HTML")
    await state.set_state(MasterForm.specialty)

# --- 6. Mutaxassislik (MasterForm) ---
@dp.message(MasterForm.specialty)
async def master_specialty_handler(message: types.Message, state: FSMContext):
    await state.update_data(specialty=message.text)
    
    # 7-savol: Tajriba
    await message.answer("Bu sohada <b>necha yillik tajribangiz</b> bor?\n"
                         "<b>(Masalan: 5 yil yoki 1 yildan kam)</b>", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_BUTTON)]], resize_keyboard=True
    ), parse_mode="HTML")
    await state.set_state(MasterForm.experience_years)

# --- 7. Tajriba (MasterForm) ---
@dp.message(MasterForm.experience_years)
async def master_experience_handler(message: types.Message, state: FSMContext):
    await state.update_data(experience_years=message.text)
    
    # 8-savol: Jamoa boshqaruvi
    await message.answer("Avval <b>jamoa (brigada)</b> boshqarganmisiz?",
                         reply_markup=yes_no_buttons,
                         parse_mode="HTML")
    await state.set_state(MasterForm.team_management)

# --- 8. Jamoa boshqaruvi (MasterForm) ---
@dp.message(MasterForm.team_management)
async def master_team_handler(message: types.Message, state: FSMContext):
    if message.text not in ["Ha", "Yo'q"]:
        await message.answer("Iltimos, faqat <b>Ha</b> yoki <b>Yo'q</b> tugmalaridan birini tanlang.", parse_mode="HTML")
        return
        
    await state.update_data(team_management=message.text)
    
    # 9-savol: Portfolio
    await message.answer("Qilgan <b>ishlaringizdan namuna (portfolio)</b> bormi?\n"
                         "<b>(Rasm, Video,</b> Portfolio uchun <b>Havola</b> kiriting, aks holda <b>Yo'q</b> deb yozing)", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_BUTTON)]], resize_keyboard=True
    ), parse_mode="HTML")
    await state.set_state(MasterForm.portfolio_link)

# --- 9. Portfolio (MasterForm) ---
@dp.message(MasterForm.portfolio_link, F.content_type.in_({'text', 'photo', 'video', 'animation', 'document', 'voice'}))
async def master_portfolio_handler(message: types.Message, state: FSMContext):
    # Agar foydalanuvchi “Yo‘q” deb yozsa — keyingi bosqichga o‘tamiz
    if message.text and message.text.strip().lower() in ["yo'q", "yo‘q", "yoq", "no"]:
        await state.update_data(portfolio=[])
        await message.answer(
            "💰 Endi <b>kutayotgan oylik maoshingizni</b> yozing.\n"
            "<b>(So‘mda yoki kelishilgan protsentda yozing)</b>",
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
        # 🖼️ Agar rasm yuborsa
        if message.photo:
            file_id = message.photo[-1].file_id
            file_type = "photo"
            for group_id in Config.GROUP_IDS:
                sent = await bot.send_photo(
                    chat_id=group_id,
                    photo=file_id,
                    caption=f"📁 Portfolio {message.from_user.full_name} dan"
                )
                portfolio_link = f"https://t.me/c/{str(group_id)[4:]}/{sent.message_id}"

        # 🎥 Agar video yuborsa
        elif message.video:
            file_id = message.video.file_id
            file_type = "video"

            # 🔄 Yuklanayotganini bildir
            loading_msg = await message.answer("⏳ Video yuklanmoqda, biroz kuting...")

            for group_id in Config.GROUP_IDS:
                try:
                    sent = await bot.send_video(
                        chat_id=group_id,
                        video=file_id,
                        caption=f"📁 Portfolio {message.from_user.full_name} dan"
                    )
                    portfolio_link = f"https://t.me/c/{str(group_id)[4:]}/{sent.message_id}"
                except Exception as e:
                    logging.error(f"🎥 Video yuborishda xatolik: {e}")
                    await loading_msg.edit_text("❌ Video guruhga yuborishda xatolik yuz berdi.")
                    return

            await loading_msg.edit_text("✅ Video muvaffaqiyatli yuklandi va guruhga joylandi!")

        # 🔗 Agar oddiy matnli havola yuborsa
        elif message.text:
            text = message.text.strip()
            if text.startswith("http://") or text.startswith("https://"):
                file_id = text
                file_type = "link"
                portfolio_link = text
            else:
                await message.answer(
                    "⚠️ Iltimos, faqat rasm, video yoki to‘liq havola yuboring "
                    "(http:// yoki https:// bilan boshlanadigan)."
                )
                return

        # ❌ Boshqa turdagi fayl yuborilsa
        else:
            await message.answer(
                "❌ Bu turdagi faylni yuborib bo‘lmaydi.\n"
                "Iltimos, faqat <b>rasm</b>, <b>video</b> yoki <b>havola</b> yuboring.",
                parse_mode="HTML"
            )
            return

        # 🧩 Portfolioni ro‘yxatga qo‘shamiz
        portfolio_list.append({
            "file_id": file_id,
            "type": file_type,
            "link": portfolio_link or ""
        })
        await state.update_data(portfolio=portfolio_list)

        # ❓ Yana portfolio yuboradimi?
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
            "Yana portfolio faylini (rasm/video/havola) yuboring:",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()  # 🔹 Eski tugmalarni olib tashlaymiz
        )
        await state.set_state(MasterForm.portfolio_link)
    else:
        await message.answer(
            "💰 Endi <b>kutayotgan oylik maoshingizni</b> yozing.\n"
            "<b>(So‘mda yoki kelishilgan protsentda yozing)</b>",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()  # 🔹 Bu yerda ham tugmalarni yopamiz
        )
        await state.set_state(MasterForm.expected_salary_usta)

# --- 10. Kutayotgan oylik maosh (MasterForm) ---
@dp.message(MasterForm.expected_salary_usta)
async def master_expected_salary_handler(message: types.Message, state: FSMContext):
    await state.update_data(expected_salary_usta=message.text)
    await message.answer(
        "<b>Oldin lesada yoki baland joylarda ishlaganmisiz, ish sharoiti balandroq bo'lsa bunga tayyormisiz?</b>?\n"
        "<b>(Masalan: fasadda, lesada yoki narvonlarda)</b>",
        reply_markup=yes_no_buttons,
        parse_mode="HTML"
    )
    await state.set_state(MasterForm.hardworking_usta)


# --- 11. Baland joyda ishlash (MasterForm) ---
@dp.message(MasterForm.hardworking_usta)
async def master_hardworking_handler(message: types.Message, state: FSMContext):
    if message.text not in ["Ha", "Yo'q"]:
        await message.answer("Iltimos, faqat <b>Ha</b> yoki <b>Yo'q</b> tugmalaridan birini tanlang.", parse_mode="HTML")
        return

    await state.update_data(hardworking_usta=message.text)
    await message.answer(
        "<b>Qachondan ish boshlay olasiz</b>?\n"
        "<b>(Masalan: Ertadan / Bir haftada)</b>",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=CANCEL_BUTTON)]],
            resize_keyboard=True
        ),
        parse_mode="HTML"
    )
    await state.set_state(MasterForm.start_date_usta)


# --- 12. Ish boshlash (yakuniy bosqich) ---
@dp.message(MasterForm.start_date_usta)
async def master_start_date_handler(message: types.Message, state: FSMContext):
    await state.update_data(start_date_usta=message.text)
    data = await state.get_data()
    await state.set_state(MasterForm.submitting)

    full_address = f"{data.get('address_region', 'Kiritilmagan')} viloyati, {data.get('address_district', 'Kiritilmagan')}"

    # 🧩 Bir nechta portfolio havolalarini birlashtiramiz
    portfolio_list = data.get("portfolio", [])
    portfolio_links = "\n".join([str(p.get("link") or "") for p in portfolio_list]) or "Kiritilmagan"

    application_text = (
        f"👑 <b>YANGI USTA ANKETASI</b> 👑\n\n"
        f"<b>🆔 Foydalanuvchi ID:</b> <code>{message.from_user.id}</code>\n"
        f"<b>👤 Nomzod:</b> {data.get('name_surname', 'Kiritilmagan')}\n"
        f"<b>🎂 Yoshi:</b> {data.get('age', 'Kiritilmagan')}\n"
        f"<b>📱 Telefon:</b> <code>{data.get('phone', 'Kiritilmagan')}</code>\n"
        f"<b>🏠 Manzil:</b> {full_address}\n"
        f"--- Kasbiy ma'lumot ---\n"
        f"<b>🔨 Mutaxassislik:</b> {data.get('specialty', 'Kiritilmagan')}\n"
        f"<b>🗓 Tajriba (yil):</b> {data.get('experience_years', 'Kiritilmagan')}\n"
        f"<b>👨‍💼 Jamoa boshqargan:</b> {data.get('team_management', 'Kiritilmagan')}\n"
        f"<b>🔗 Portfolio:</b>\n{portfolio_links}\n"
        f"<b>💰 Kutayotgan maosh:</b> {data.get('expected_salary_usta', 'Kiritilmagan')}\n"
        f"<b>💪 Baland joyda ishlash:</b> {data.get('hardworking_usta', 'Kiritilmagan')}\n"
        f"<b>📅 Ish boshlash:</b> {data.get('start_date_usta', 'Kiritilmagan')}\n"
        f"<b>Vakansiya:</b> Usta"
    )

    # --- Google Sheets uchun ---
    sheets_data = {
        "Sana": str(datetime.now()),
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

    # 1️⃣ Sheets ga yuborish
    sheets_success = await send_data_to_sheets(sheets_data, "Usta")

    # 2️⃣ Barcha adminlarga yuborish
    admin_success = False
    for group_id in Config.GROUP_IDS:
        try:
            await bot.send_message(
                chat_id=group_id,
                text=application_text,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            admin_success = True
        except Exception as e:
            logging.error(f"Admin {group_id} ga yuborishda xatolik: {e}")

    # ✅ Javob
    if sheets_success and admin_success:
        await message.answer("✅ Arizangiz muvaffaqiyatli yuborildi!", reply_markup=main_menu)
    else:
        await message.answer("⚠️ Yuborishda xatolik yuz berdi, keyinroq urinib ko‘ring.", reply_markup=main_menu)

    await state.clear()

# --- Botni ishga tushirish ---
async def main():
    logging.info("Bot ishga tushmoqda...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot to‘xtatildi.")