"""Telegram chatbot backed by the OpenAI API."""

import logging
import os
from collections import defaultdict, deque

from openai import AsyncOpenAI
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT", "You are a helpful, friendly assistant."
)
MAX_HISTORY_MESSAGES = 20  # 10 user/assistant turns per chat
TELEGRAM_MESSAGE_LIMIT = 4000  # Below Telegram's 4096-character limit

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("Set the TELEGRAM_BOT_TOKEN environment variable.")
if not OPENAI_API_KEY:
    raise RuntimeError("Set the OPENAI_API_KEY environment variable.")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)
chat_histories: dict[int, deque[dict[str, str]]] = defaultdict(
    lambda: deque(maxlen=MAX_HISTORY_MESSAGES)
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome the user and explain how to use the bot."""
    if update.message:
        await update.message.reply_text(
            "Hi! I'm an AI assistant. Send me a message to chat, or use /reset "
            "to clear our conversation."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show available commands."""
    if update.message:
        await update.message.reply_text(
            "Just send a text message and I'll reply.\n"
            "/start — Start the bot\n"
            "/reset — Clear conversation history\n"
            "/help — Show this help"
        )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear this chat's in-memory conversation history."""
    if update.effective_chat:
        chat_histories.pop(update.effective_chat.id, None)
    if update.message:
        await update.message.reply_text("Conversation history cleared.")


def split_message(text: str, limit: int = TELEGRAM_MESSAGE_LIMIT) -> list[str]:
    """Split long replies at word boundaries where possible."""
    chunks: list[str] = []
    while len(text) > limit:
        split_at = text.rfind("\n", 0, limit)
        if split_at < limit // 2:
            split_at = text.rfind(" ", 0, limit)
        if split_at < limit // 2:
            split_at = limit
        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()
    if text:
        chunks.append(text)
    return chunks


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message to OpenAI and reply with the generated answer."""
    if not update.message or not update.effective_chat or not update.message.text:
        return

    chat_id = update.effective_chat.id
    history = chat_histories[chat_id]
    user_text = update.message.text
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history,
        {"role": "user", "content": user_text},
    ]

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
        )
        answer = response.choices[0].message.content
        if not answer:
            answer = "I couldn't generate a response. Please try again."
    except Exception:
        logger.exception("OpenAI request failed for chat %s", chat_id)
        await update.message.reply_text(
            "Sorry, I couldn't get a response right now. Please try again later."
        )
        return

    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": answer})
    for chunk in split_message(answer):
        await update.message.reply_text(chunk)


def main() -> None:
    """Start polling Telegram for updates."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    logger.info("Starting Telegram bot with model %s", OPENAI_MODEL)
    application.run_polling()


if __name__ == "__main__":
    main()
