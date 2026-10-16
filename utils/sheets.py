import logging
import aiohttp
from config import Config

async def send_data_to_sheets(data: dict, sheet_name: str) -> bool:
    """
    Ma'lumotlarni Google Sheets ga yuboradi (Apps Script Web App orqali).
    Faqat 200 status keldi va 'success' bo'lsa True qaytaradi.
    """
    if not Config.SHEETS_API_URL or not Config.SHEETS_API_TOKEN:
        logging.warning("⚠️ Config.SHEETS_API_URL yoki Config.SHEETS_API_TOKEN belgilanmagan. Sheets ga yuborish o'tkazib yuborildi.")
        return False

    payload = {
        "token": Config.SHEETS_API_TOKEN,
        "sheet": sheet_name,
        "data": data
    }

    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(Config.SHEETS_API_URL, json=payload) as response:
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