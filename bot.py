import os
import json
import logging
from typing import Dict
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Konfiguratsiya ---
# Tokenni muhit o'zgaruvchisida saqlang: BOT_TOKEN
TOKEN = os.getenv("BOT_TOKEN", "8439269270:AAGbCPsRgBrYaPmuZgnc2uJdXZhIA9U_YzM")

# Public kanal username (masalan: @kanal_nomi)
CHANNEL_ID = "@kinolaruzbot1"

# Kino kodi -> fayl yo'li xaritasi
DATA_FILE = "films.json"

# films.json namuna:
# {
#   "A123": "films/film1.mp4",
#   "B999": "films/film2.mp4"
# }

# --- Fayldan ma'lumot yuklash ---
def load_data() -> Dict[str, str]:
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"{DATA_FILE} topilmadi. Bo'sh lug'at qaytarildi.")
        return {}
    except Exception as e:
        logger.exception("Ma'lumotni yuklashda xatolik:")
        return {}

# --- Kanal obunasini tekshirish ---
async def check_subscriber(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception as e:
        # Agar bot kanalga admin bo'lmasa yoki boshqa xato bo'lsa, xatolik yoziladi
        logger.exception("Obuna tekshirish xatosi:")
        return False

# --- /start buyrug'i ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Kanalga obuna bo‘lish", url=f"https://t.me/{CHANNEL_ID.lstrip('@')}")],
        [InlineKeyboardButton("♻️ Tekshirish", callback_data="check")],
    ])

    await update.message.reply_text(
        "Assalomu alaykum! Botdan foydalanish uchun iltimos kanalga obuna bo'ling:",
        reply_markup=keyboard,
    )

# --- Callback tugmalarini ishlash ---
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data != "check":
        return

    user_id = query.from_user.id
    is_member = await check_subscriber(user_id, context)

    if not is_member:
        await query.answer("Obuna bo‘lmagansiz. Iltimos kanalga obuna bo'ling.", show_alert=True)
        return

    # Agarda obuna bo'lsa, xabarni tahrirlash va qo'shimcha ko'rsatma berish
    await query.edit_message_text("Obuna tasdiqlandi ✔️\nEndi kino kodini yuboring (masalan: A123).")

# --- Kino kodini qabul qilish va video yuborish ---
async def get_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # Tekshirish
    if not await check_subscriber(user_id, context):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Kanalga obuna bo‘lish", url=f"https://t.me/{CHANNEL_ID.lstrip('@')}")],
            [InlineKeyboardButton("♻️ Tekshirish", callback_data="check")],
        ])
        return await update.message.reply_text(
            "❗ Avval kanalga obuna bo'ling.", reply_markup=keyboard
        )

    code = update.message.text.strip()
    data = load_data()

    # Kod tekshiruvi (katta-kichik harfga sezgir)
    if code not in data:
        return await update.message.reply_text("❌ Bunday kod topilmadi. Iltimos kodni tekshirib qayta yuboring.")

    video_path = data[code]

    if not os.path.isfile(video_path):
        logger.error(f"Video fayli mavjud emas: {video_path}")
        return await update.message.reply_text("❗ Kino fayli serverda topilmadi. Administrator bilan bog'laning.")

    try:
        # Faylni kontekst menejeri bilan ochib yuborish
        with open(video_path, "rb") as video_file:
            await update.message.reply_video(video=video_file)
    except Exception as e:
        logger.exception("Video yuborishda xato:")
        await update.message.reply_text("❗ Kino faylini yuborishda xatolik yuz berdi.")

# --- Botni ishga tushirish ---
def main():
   

    app = ApplicationBuilder().token(TOKEN).build()

    # Handlerlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_code))

    logger.info("Bot ishga tushmoqda...")
    app.run_polling()


if __name__ == "__main__":
    main()