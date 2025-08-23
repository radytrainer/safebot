import os
import logging
from dotenv import load_dotenv
from typing import Dict, List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ── Setup ──────────────────────────────────────────────────────────────
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("security-bot")

ASSETS_IMG = "assets/images"
ASSETS_VOICE = "assets/voice"

# ── Knowledge base ──────────────────────────────────────────────────────
TOPICS: Dict[str, Dict] = {
    "2fa": {
        "keywords": ["2fa", "two factor", "authenticator", "otp", "code"],
        "text": "🛡️ Enable Two-Factor Authentication (2FA):\n• Use authenticator apps (Google Authenticator, Authy) instead of SMS.\n• Store backup codes securely.\n• Turn on login alerts.\n• For Facebook/Google: Settings > Security > 2FA.",
        "image": f"{ASSETS_IMG}/2fa.jpg",
        "voice": f"{ASSETS_VOICE}/2fa.ogg",
    },
    "phishing": {
        "keywords": ["phish", "phishing", "scam", "link", "fake"],
        "text": "🎣 Avoid Phishing:\n• Don’t click suspicious links.\n• Always check sender email/URL carefully.\n• Enable alerts for new logins.\n• If you clicked: change password & scan your device.",
        "image": f"{ASSETS_IMG}/phishing.jpg",
        "voice": f"{ASSETS_VOICE}/phishing.ogg",
    },
    "password": {
        "keywords": ["password", "passcode", "credential"],
        "text": "🔐 Password Tips:\n• Use a password manager.\n• Make them long (14+ chars).\n• Don’t reuse passwords.\n• Combine with 2FA.",
        "image": f"{ASSETS_IMG}/password.jpg",
        "voice": f"{ASSETS_VOICE}/password.ogg",
    },
    "sim-swap": {
        "keywords": ["sim", "swap", "phone number", "sms hijack"],
        "text": "📶 SIM-swap defense:\n• Use app-based 2FA (not SMS).\n• Add a transfer PIN/lock at your carrier.\n• If suspected: contact carrier immediately, lock accounts, change passwords.",
        "image": f"{ASSETS_IMG}/sim-swap.jpg",
        "voice": f"{ASSETS_VOICE}/sim-swap.ogg",
    },
    "lost-phone": {
        "keywords": ["lost phone", "stolen", "device", "find my", "erase"],
        "text": "📱 Lost/stolen phone:\n• Use Find My Device/iPhone to locate or erase.\n• Change passwords for email, bank, social; revoke sessions.\n• Inform your carrier; consider SIM block.\n• Enable screen lock + biometric on new device.",
        "image": f"{ASSETS_IMG}/lost-phone.jpg",
        "voice": f"{ASSETS_VOICE}/lost-phone.ogg",
    },
    "bank": {
        "keywords": ["bank", "card", "transaction", "money", "fraud"],
        "text": "🏦 Bank Security:\n• Turn on transaction alerts.\n• Never share OTPs or PINs.\n• Use a separate email for banking.\n• If compromised: call bank immediately.",
        "image": f"{ASSETS_IMG}/bank.jpg",
        "voice": f"{ASSETS_VOICE}/bank.ogg",
    },
}

TOPIC_ORDER: List[str] = ["2fa", "phishing", "password", "sim-swap", "lost-phone", "bank"]

# ── Helper Functions ─────────────────────────────────────────────────────
def build_main_menu() -> InlineKeyboardMarkup:
    rows = []
    row: List[InlineKeyboardButton] = []
    for key in TOPIC_ORDER:
        label = {
            "2fa": "Enable 2FA",
            "phishing": "Avoid Phishing",
            "password": "Strong Passwords",
            "sim-swap": "SIM-Swap Defense",
            "lost-phone": "Lost Phone",
            "bank": "Bank Security",
        }[key]
        row.append(InlineKeyboardButton(text=label, callback_data=f"topic:{key}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def find_best_topic(user_text: str) -> str | None:
    t = user_text.lower()
    best_key, best_hits = None, 0
    for key, data in TOPICS.items():
        hits = sum(1 for kw in data["keywords"] if kw in t)
        if hits > best_hits:
            best_hits = hits
            best_key = key
    return best_key if best_hits > 0 else None


async def send_topic_reply(origin, context: ContextTypes.DEFAULT_TYPE, key: str):
    topic = TOPICS.get(key)
    if not topic:
        await origin.message.reply_text("Sorry, that topic is not available.")
        return

    chat_id = origin.message.chat_id

    # 1) Text
    await context.bot.send_message(chat_id=chat_id, text=topic["text"], reply_markup=build_main_menu())

    # 2) Image
    if topic.get("image") and os.path.exists(topic["image"]):
        await context.bot.send_photo(chat_id=chat_id, photo=topic["image"])

    # 3) Voice
    if topic.get("voice") and os.path.exists(topic["voice"]):
        await context.bot.send_voice(chat_id=chat_id, voice=topic["voice"])




# ── Handlers ─────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! I’m your Security Assistant 🤖🔒\nAsk me about social media, mobile apps, or banking security—or tap a topic below.",
        reply_markup=build_main_menu(),
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Try messages like:\n• 'Enable 2FA on Facebook?'\n• 'Is this link phishing?'\n• 'Protect my bank account'\n• 'My phone got stolen'",
        reply_markup=build_main_menu(),
    )


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    if data.startswith("topic:"):
        key = data.split(":", 1)[1]
        await send_topic_reply(query, context, key)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text or ""
    key = find_best_topic(msg)
    if key:
        await send_topic_reply(update, context, key)
    else:
        await update.message.reply_text(
            "I’m not fully sure yet. General advice:\n1) Change your password and enable 2FA.\n2) Revoke unknown logins.\n3) Turn on login alerts.\n4) Call your bank if needed.\nTap a topic below for more.",
            reply_markup=build_main_menu(),
        )


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "I cannot verify images. Describe your issue in text (without sensitive info), and I’ll help."
    )


async def on_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "I cannot process voice messages yet. Please type your question instead."
    )


# ── Main ────────────────────────────────────────────────────────────────
def main():
    if not TOKEN:
        raise RuntimeError("Missing TELEGRAM_TOKEN in .env")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))
    app.add_handler(MessageHandler(filters.VOICE, on_voice))
    app.add_handler(CallbackQueryHandler(on_callback))

    logger.info("Security bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
