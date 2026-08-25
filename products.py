# Base prices in USD
PRODUCTS = {
    "drinks": {
        "emoji": "🥤",
        "name": "Ichimliklar",
        "items": {
            "coca_cola": {"name": "Coca-Cola", "price": 0.50, "emoji": "🥤", "image": "images/coca_cola.jpg"},
            "pepsi": {"name": "Pepsi", "price": 0.50, "emoji": "🥤"},
            "fanta": {"name": "Fanta", "price": 0.45, "emoji": "🥤"},
            "sprite": {"name": "Sprite", "price": 0.45, "emoji": "🥤"}
        }
    },
    "sweets": {
        "emoji": "🍫",
        "name": "Shirinliklar",
        "items": {
            "chocolate_bar": {"name": "Chocolate Bar", "price": 0.80, "emoji": "🍫"},
            "candy": {"name": "Candy", "price": 0.30, "emoji": "🍬"},
            "gummies": {"name": "Gummies", "price": 0.45, "emoji": "🍬"},
            "wafers": {"name": "Wafers", "price": 0.40, "emoji": "🍪"}
        }
    },
    "chips": {
        "emoji": "🥔",
        "name": "Chipslar",
        "items": {
            "lays": {"name": "Lays", "price": 0.60, "emoji": "🥔"},
            "pringles": {"name": "Pringles", "price": 1.50, "emoji": "🥔"},
            "doritos": {"name": "Doritos", "price": 0.90, "emoji": "🥔"},
            "estrella": {"name": "Estrella", "price": 0.55, "emoji": "🥔"}
        }
    },
    "noodles": {
        "emoji": "🍜",
        "name": "Lapsha",
        "items": {
            "maggi": {"name": "Maggi", "price": 0.35, "emoji": "🍜"},
            "indomie": {"name": "Indomie", "price": 0.40, "emoji": "🍜"},
            "rollton": {"name": "Rollton", "price": 0.38, "emoji": "🍜"},
            "doshirak": {"name": "Doshirak", "price": 0.32, "emoji": "🍜"}
        }
    },
    "cookies": {
        "emoji": "🍪",
        "name": "Pechenye",
        "items": {
            "oreo": {"name": "Oreo", "price": 0.75, "emoji": "🍪"},
            "chips_ahoy": {"name": "Chips Ahoy", "price": 0.90, "emoji": "🍪"},
            "digestive": {"name": "Digestive", "price": 0.60, "emoji": "🍪"},
            "tuc": {"name": "TUC", "price": 0.50, "emoji": "🍪"}
        }
    }
}

# Currency (fixed: Malaysian Ringgit)
CURRENCY = "RM"
EXCHANGE_RATES = {
    "RM": {"rate": 4.75, "symbol": "RM", "name": "Malaysian Ringgit"}
}

def get_category_emoji(category_id):
    return PRODUCTS.get(category_id, {}).get("emoji", "📦")

def get_category_name(category_id):
    return PRODUCTS.get(category_id, {}).get("name", "Unknown")

def get_product_info(category_id, product_id):
    category = PRODUCTS.get(category_id, {})
    items = category.get("items", {})
    return items.get(product_id)

def get_all_categories():
    return PRODUCTS.keys()

def convert_price(price_usd, currency_code=CURRENCY):
    """Convert USD price to RM"""
    rate = EXCHANGE_RATES[CURRENCY]["rate"]
    return round(price_usd * rate, 2)

def format_price(price_usd, currency_code=CURRENCY):
    """Format price with RM symbol"""
    converted_price = convert_price(price_usd)
    symbol = EXCHANGE_RATES[CURRENCY]["symbol"]
    return f"{symbol}{converted_price}"
