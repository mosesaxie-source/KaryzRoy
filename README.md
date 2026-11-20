# KaryzRoy Telegram Chatbot

A simple Telegram chatbot powered by OpenAI. It keeps a short conversation history in memory for each chat and supports `/start`, `/help`, and `/reset`.

## Requirements

- Python 3.10 or newer
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- An OpenAI API key from the [OpenAI platform](https://platform.openai.com/api-keys)

## Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set the required environment variables. Copy `.env.example` as a reference, then set the variables in your shell (the application does not automatically load `.env` files):

   ```bash
   export TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
   export OPENAI_API_KEY="your-openai-api-key"
   export OPENAI_MODEL="gpt-4o-mini"  # Optional
   ```

   On Windows PowerShell, use `$env:TELEGRAM_BOT_TOKEN="..."` and `$env:OPENAI_API_KEY="..."`.

4. Run the bot:

   ```bash
   python bot.py
   ```

Keep your API keys private and never commit them to the repository. Conversation history is held in memory and is cleared when the process restarts; `/reset` clears the current chat's history.
