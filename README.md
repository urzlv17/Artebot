# Mini Shop Telegram Bot

Telegram bot for mini shop with automatic TNG payment integration.

## Features

- 🛒 Product browsing by categories
- 📦 Shopping cart with quantity management
- 💳 Automatic TNG payment integration
- 🧾 Order history and tracking
- 👤 User profile management
- 📊 Payment history

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

3. Run the bot:
```bash
python bot.py
```

## Bot Structure

- Main menu with 4 sections
- Product categories: Drinks, Sweets, Chips, Noodles, Cookies
- Automatic payment via TNG
- Order confirmation with receipt
