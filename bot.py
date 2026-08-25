import os
import asyncio
import schedule
from datetime import datetime, time
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from dotenv import load_dotenv
from products import PRODUCTS, get_product_info, format_price, CURRENCY
from openpyxl import Workbook

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]

# Button labels
BTN_BUY = "🛒 Mahsulot sotib olish"
BTN_ORDERS = "📦 Mening xaridlarim"
BTN_PAYMENTS = "💳 To'lovlar tarixi"
BTN_PROFILE = "👤 Mening profilim"
BTN_BACK = "⬅️ Orqaga"
BTN_PAY = "💳 To'lash"
BTN_MINUS = "➖"
BTN_PLUS = "➕"
BTN_CHECKOUT = "🟢 To'lash"
BTN_TNG = "📱 TNG QR"
BTN_CASH = "💵 Cash"
BTN_RECEIPT_SENT = "✅ Receipt yuborildi"
BTN_PHOTO_SENT = "✅ Rasm yuborildi"

# Admin button labels
BTN_ADMIN_ORDERS = "📦 Barcha buyurtmalar"
BTN_ADMIN_PENDING = "⏳ Kutilayotgan buyurtmalar"
BTN_ADMIN_PAYMENTS = "💳 Barcha to'lovlar"
BTN_ADMIN_USERS = "👤 Foydalanuvchilar"
BTN_ADMIN_STATS = "📊 Statistika"
BTN_ADMIN_BROADCAST = "📢 Xabar yuborish"
BTN_ADMIN_BACK = "⬅️ Orqaga"

# Storage for user data (in production, use a database)
user_carts = {}
user_orders = {}
user_profiles = {}
payment_history = {}
payment_reminders = {}
payment_proofs = {}
user_states = {}
order_counter = 152
broadcast_states = {}
product_edit_states = {}


def is_admin(user_id):
    return user_id in ADMIN_IDS


def get_user_name(user):
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    return f"{first_name} {last_name}".strip() or "Aziz"


def init_user(user_id, user_name=None):
    if user_id not in user_profiles:
        user_profiles[user_id] = {
            "name": user_name or "Aziz",
            "joined": datetime.now().isoformat(),
        }
    if user_id not in user_carts:
        user_carts[user_id] = {}
    if user_id not in user_orders:
        user_orders[user_id] = []
    if user_id not in payment_history:
        payment_history[user_id] = []
    if user_id not in user_states:
        user_states[user_id] = {"screen": "main"}


def set_state(user_id, screen, **extra):
    user_states[user_id] = {"screen": screen, **extra}


def category_label(category_id):
    category = PRODUCTS[category_id]
    return f"{category['emoji']} {category['name']}"


def product_label(category_id, product_id):
    product = get_product_info(category_id, product_id)
    if not product:
        return None
    return f"{product['emoji']} {product['name']} — {format_price(product['price'])}"


def find_category(text):
    for category_id, category in PRODUCTS.items():
        if text == category_label(category_id):
            return category_id
    return None


def find_product(text):
    for category_id, category in PRODUCTS.items():
        for product_id in category["items"]:
            if text == product_label(category_id, product_id):
                return category_id, product_id
    return None, None


def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(BTN_BUY)],
            [KeyboardButton(BTN_ORDERS), KeyboardButton(BTN_PAYMENTS)],
            [KeyboardButton(BTN_PROFILE)],
        ],
        resize_keyboard=True,
    )


def categories_keyboard():
    rows = [[KeyboardButton(category_label(cid))] for cid in PRODUCTS]
    rows.append([KeyboardButton(BTN_BACK)])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def products_keyboard(category_id):
    category = PRODUCTS.get(category_id)
    if not category:
        return categories_keyboard()
    rows = []
    for product_id in category["items"]:
        rows.append([KeyboardButton(product_label(category_id, product_id))])
    rows.append([KeyboardButton(BTN_BACK)])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def product_detail_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(BTN_MINUS), KeyboardButton(BTN_PLUS)],
            [KeyboardButton(BTN_CHECKOUT)],
            [KeyboardButton(BTN_BACK)],
        ],
        resize_keyboard=True,
    )


def checkout_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton(BTN_PAY)], [KeyboardButton(BTN_BACK)]],
        resize_keyboard=True,
    )


def payment_methods_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton(BTN_TNG), KeyboardButton(BTN_CASH)], [KeyboardButton(BTN_BACK)]],
        resize_keyboard=True,
    )


def tng_payment_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton(BTN_RECEIPT_SENT)], [KeyboardButton(BTN_BACK)]],
        resize_keyboard=True,
    )


def cash_payment_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton(BTN_PHOTO_SENT)], [KeyboardButton(BTN_BACK)]],
        resize_keyboard=True,
    )


def admin_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(BTN_ADMIN_ORDERS), KeyboardButton(BTN_ADMIN_PENDING)],
            [KeyboardButton(BTN_ADMIN_PAYMENTS), KeyboardButton(BTN_ADMIN_USERS)],
            [KeyboardButton(BTN_ADMIN_STATS), KeyboardButton(BTN_ADMIN_BROADCAST)],
            [KeyboardButton(BTN_ADMIN_BACK)],
        ],
        resize_keyboard=True,
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = get_user_name(update.effective_user)
    init_user(user_id, user_name)
    set_state(user_id, "main")

    await update.message.reply_text(
        f"🏪 MINI SHOP\n\n"
        f"Salom, {user_name}! 👋\n"
        f"Kerakli bo'limni tanlang:",
        reply_markup=main_menu_keyboard(),
    )


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text(
            "❌ Siz admin emassiz! Bu buyruq faqat adminlar uchun."
        )
        return
    
    set_state(user_id, "admin")
    await update.message.reply_text(
        "🔧 ADMIN PANEL\n\n"
        "Kerakli bo'limni tanlang:",
        reply_markup=admin_keyboard(),
    )


async def send_main_menu(message, user_id):
    user_name = user_profiles[user_id]["name"]
    set_state(user_id, "main")
    await message.reply_text(
        f"🏪 MINI SHOP\n\n"
        f"Salom, {user_name}! 👋\n"
        f"Kerakli bo'limni tanlang:",
        reply_markup=main_menu_keyboard(),
    )


async def send_categories(message, user_id):
    set_state(user_id, "categories")
    await message.reply_text(
        "🛒 Mahsulot sotib olish\n\nBo'limni tanlang:",
        reply_markup=categories_keyboard(),
    )


async def send_products(message, user_id, category_id):
    category = PRODUCTS.get(category_id)
    if not category:
        await send_categories(message, user_id)
        return

    set_state(user_id, "products", category_id=category_id)
    await message.reply_text(
        f"{category['emoji']} {category['name']}\n\nMahsulotni tanlang:",
        reply_markup=products_keyboard(category_id),
    )


async def send_product_details(message, user_id, category_id, product_id):
    product = get_product_info(category_id, product_id)
    if not product:
        await send_products(message, user_id, category_id)
        return

    set_state(user_id, "product_detail", category_id=category_id, product_id=product_id)
    cart_key = f"{category_id}_{product_id}"
    cart_quantity = user_carts[user_id].get(cart_key, 0)
    total_usd = product["price"] * cart_quantity
    formatted_price = format_price(product["price"])
    formatted_total = format_price(total_usd)

    text = (
        f"{product['emoji']} {product['name']}\n"
        f"{formatted_price} × {cart_quantity}\n\n"
        f"Jami: {formatted_total}"
    )
    keyboard = product_detail_keyboard()
    image_path = product.get("image")

    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as photo:
            await message.reply_photo(photo=photo, caption=text, reply_markup=keyboard)
    else:
        await message.reply_text(text, reply_markup=keyboard)


async def send_checkout(message, user_id):
    if not user_carts[user_id]:
        await send_categories(message, user_id)
        return

    set_state(user_id, "checkout")
    total_usd = 0
    items_text = ""
    for cart_key, quantity in user_carts[user_id].items():
        category_id, product_id = cart_key.split("_", 1)
        product = get_product_info(category_id, product_id)
        if product:
            total_usd += product["price"] * quantity
            items_text += f"{product['emoji']} {product['name']} ×{quantity}\n"

    formatted_total = format_price(total_usd)
    await message.reply_text(
        f"💳 To'lov\n\n{items_text}\nJami: {formatted_total}\n\n"
        f"\"{BTN_PAY}\" tugmasini bosing va to'lov usulini tanlang (TNG QR yoki Cash).",
        reply_markup=checkout_keyboard(),
    )


async def send_payment_methods(message, user_id):
    set_state(user_id, "payment_methods")
    await message.reply_text(
        "💳 To'lov usulini tanlang\n\nQaysi usul bilan to'laysiz?",
        reply_markup=payment_methods_keyboard(),
    )


def build_order(user_id):
    global order_counter
    total_usd = 0
    order_items = []

    for cart_key, quantity in user_carts[user_id].items():
        category_id, product_id = cart_key.split("_", 1)
        product = get_product_info(category_id, product_id)
        if product:
            total_usd += product["price"] * quantity
            order_items.append(
                {
                    "name": product["name"],
                    "quantity": quantity,
                    "price_usd": product["price"],
                    "total_usd": product["price"] * quantity,
                }
            )

    order_counter += 1
    order_id = order_counter
    order = {
        "id": order_id,
        "items": order_items,
        "total_usd": total_usd,
        "currency": CURRENCY,
        "date": datetime.now().isoformat(),
        "status": "pending",
    }
    return order


async def send_tng_qr_payment(message, user_id, context):
    order = build_order(user_id)
    order["payment_method"] = "TNG QR"
    user_orders[user_id].append(order)
    order_id = order["id"]

    payment_proofs[user_id] = {
        "order_id": order_id,
        "proof_sent": False,
        "proof_type": "receipt",
    }
    set_state(user_id, "tng_payment", order_id=order_id)

    formatted_total = format_price(order["total_usd"])
    await message.reply_text(
        f"📱 TNG QR To'lov\n\n"
        f"Quyidagi TNG QR kodiga pul o'tkazing:\n"
        f"[TNG QR Code]\n\n"
        f"Jami: {formatted_total}\n\n"
        f"To'lov tugagach, receipt (chek) rasmini shu chatga yuboring.\n"
        f"Receipt yuborilgach, \"{BTN_RECEIPT_SENT}\" tugmasini bosing.\n\n"
        f"⏰ Iltimos, receiptni tezroq yuboring!",
        reply_markup=tng_payment_keyboard(),
    )
    await start_reminder(context, message.chat_id, user_id, order_id, "receipt")


async def send_cash_payment(message, user_id, context):
    order = build_order(user_id)
    order["payment_method"] = "Cash"
    user_orders[user_id].append(order)
    order_id = order["id"]

    payment_proofs[user_id] = {
        "order_id": order_id,
        "proof_sent": False,
        "proof_type": "photo",
    }
    set_state(user_id, "cash_payment", order_id=order_id)

    formatted_total = format_price(order["total_usd"])
    await message.reply_text(
        f"💵 Cash To'lov\n\n"
        f"Jami: {formatted_total}\n\n"
        f"Iltimos, pul rasmini shu chatga yuboring.\n"
        f"Rasm yuborilgach, \"{BTN_PHOTO_SENT}\" tugmasini bosing.\n\n"
        f"⏰ Iltimos, pul rasmini tezroq yuboring!",
        reply_markup=cash_payment_keyboard(),
    )
    await start_reminder(context, message.chat_id, user_id, order_id, "cash photo")


async def complete_payment(message, user_id, order_id):
    order = None
    for o in user_orders[user_id]:
        if o["id"] == order_id and o["status"] == "pending":
            order = o
            break

    if not order:
        await send_main_menu(message, user_id)
        return

    proof = payment_proofs.get(user_id)
    if not proof or proof.get("order_id") != order_id or not proof.get("proof_sent"):
        proof_type = proof.get("proof_type") if proof else None
        if proof_type == "receipt":
            text = (
                "❌ To'lov tasdiqlanmadi!\n\n"
                "Iltimos, avval receipt (chek) rasmini shu chatga yuboring, "
                f"keyin \"{BTN_RECEIPT_SENT}\" tugmasini bosing."
            )
        else:
            text = (
                "❌ To'lov tasdiqlanmadi!\n\n"
                "Iltimos, avval pul rasmini shu chatga yuboring, "
                f"keyin \"{BTN_PHOTO_SENT}\" tugmasini bosing."
            )
        await message.reply_text(text)
        return

    if user_id in payment_reminders:
        payment_reminders[user_id]["cancelled"] = True

    order["status"] = "paid"
    payment_history[user_id].append(
        {
            "order_id": order_id,
            "amount_usd": order["total_usd"],
            "currency": order["currency"],
            "date": datetime.now().isoformat(),
            "method": order.get("payment_method", "Unknown"),
            "status": "success",
        }
    )
    user_carts[user_id] = {}

    items_text = ""
    for item in order["items"]:
        items_text += f"{item['name']} ×{item['quantity']}\n"

    formatted_total = format_price(order["total_usd"])
    if user_id in payment_proofs:
        del payment_proofs[user_id]

    set_state(user_id, "main")
    await message.reply_text(
        f"✅ To'lov muvaffaqiyatli!\n\n"
        f"{items_text}"
        f"💰 {formatted_total}\n\n"
        f"🧾 Chek №{order_id}\n\n"
        f"Mahsulotingizni olishingiz mumkin! 🛍️",
        reply_markup=main_menu_keyboard(),
    )


async def start_reminder(context, chat_id, user_id, order_id, reminder_type):
    payment_reminders[user_id] = {
        "order_id": order_id,
        "chat_id": chat_id,
        "reminder_type": reminder_type,
        "cancelled": False,
        "count": 0,
    }
    asyncio.create_task(send_reminders(context, user_id, order_id, reminder_type))


async def send_reminders(context, user_id, order_id, reminder_type):
    while user_id in payment_reminders and not payment_reminders[user_id]["cancelled"]:
        await asyncio.sleep(20)

        if user_id not in payment_reminders or payment_reminders[user_id]["cancelled"]:
            break

        payment_reminders[user_id]["count"] += 1
        count = payment_reminders[user_id]["count"]
        chat_id = payment_reminders[user_id]["chat_id"]

        if reminder_type == "receipt":
            text = f"⏰ Iltimos, receipt (chek) rasmini yuboring! ({count} marta eslatildi)"
        else:
            text = f"⏰ Iltimos, pul rasmini yuboring! ({count} marta eslatildi)"

        try:
            if context and context.bot:
                await context.bot.send_message(chat_id=chat_id, text=text)
            else:
                break
        except Exception:
            break


async def send_orders(message, user_id):
    set_state(user_id, "main")
    orders = user_orders.get(user_id, [])

    if not orders:
        await message.reply_text(
            "📦 Mening xaridlarim\n\nSiz hali xarid qilmagansiz.",
            reply_markup=main_menu_keyboard(),
        )
        return

    text = "📦 Mening xaridlarim\n\n"
    for order in reversed(orders[-5:]):
        formatted_total = format_price(order["total_usd"])
        text += f"🧾 Buyurtma №{order['id']}\n"
        text += f"💰 {formatted_total}\n"
        text += f"📅 {order['date'][:10]}\n"
        text += f"✅ {order['status']}\n\n"

    await message.reply_text(text, reply_markup=main_menu_keyboard())


async def send_payment_history(message, user_id):
    set_state(user_id, "main")
    payments = payment_history.get(user_id, [])

    if not payments:
        await message.reply_text(
            "💳 To'lovlar tarixi\n\nSiz hali to'lov qilmagansiz.",
            reply_markup=main_menu_keyboard(),
        )
        return

    text = "💳 To'lovlar tarixi\n\n"
    for payment in reversed(payments[-5:]):
        formatted_amount = format_price(payment["amount_usd"])
        text += f"🧾 Buyurtma №{payment['order_id']}\n"
        text += f"💰 {formatted_amount}\n"
        text += f"📅 {payment['date'][:10]}\n"
        text += f"💳 {payment['method']}\n"
        text += f"✅ {payment['status']}\n\n"

    await message.reply_text(text, reply_markup=main_menu_keyboard())


async def send_profile(message, user_id):
    set_state(user_id, "main")
    profile = user_profiles.get(user_id, {})
    orders = user_orders.get(user_id, [])
    total_spent_usd = sum(order["total_usd"] for order in orders)
    formatted_total = format_price(total_spent_usd)

    default_name = "Noma'lum"
    text = (
        f"👤 Mening profilim\n\n"
        f"👤 Ism: {profile.get('name', default_name)}\n"
        f"📅 Qo'shilgan: {profile.get('joined', default_name)[:10]}\n"
        f"📦 Jami buyurtmalar: {len(orders)}\n"
        f"💰 Jami sarflangan: {formatted_total}"
    )
    await message.reply_text(text, reply_markup=main_menu_keyboard())


async def admin_show_all_orders(message, user_id):
    if not is_admin(user_id):
        await send_main_menu(message, user_id)
        return
    
    set_state(user_id, "admin")
    text = "📦 BARCHA BUYURTMALAR\n\n"
    
    total_orders = 0
    for uid, orders in user_orders.items():
        for order in orders:
            total_orders += 1
            formatted_total = format_price(order["total_usd"])
            user_name = user_profiles.get(uid, {}).get("name", "Noma'lum")
            text += f"🧾 Buyurtma #{order['id']}\n"
            text += f"👤 Foydalanuvchi: {user_name} (ID: {uid})\n"
            text += f"💰 {formatted_total}\n"
            text += f"📅 {order['date'][:10]}\n"
            text += f"✅ {order['status']}\n"
            payment_method = order.get('payment_method', "Noma'lum")
            text += f"💳 {payment_method}\n\n"
    
    if total_orders == 0:
        text += "Hali buyurtmalar yo'q."
    
    await message.reply_text(text, reply_markup=admin_keyboard())


async def admin_show_all_payments(message, user_id):
    if not is_admin(user_id):
        await send_main_menu(message, user_id)
        return
    
    set_state(user_id, "admin")
    text = "💳 BARCHA TO'LOVLAR\n\n"
    
    total_payments = 0
    for uid, payments in payment_history.items():
        for payment in payments:
            total_payments += 1
            formatted_amount = format_price(payment["amount_usd"])
            user_name = user_profiles.get(uid, {}).get("name", "Noma'lum")
            text += f"🧾 Buyurtma #{payment['order_id']}\n"
            text += f"👤 Foydalanuvchi: {user_name} (ID: {uid})\n"
            text += f"💰 {formatted_amount}\n"
            text += f"📅 {payment['date'][:10]}\n"
            text += f"💳 {payment['method']}\n"
            text += f"✅ {payment['status']}\n\n"
    
    if total_payments == 0:
        text += "Hali to'lovlar yo'q."
    
    await message.reply_text(text, reply_markup=admin_keyboard())


async def admin_show_users(message, user_id):
    if not is_admin(user_id):
        await send_main_menu(message, user_id)
        return
    
    set_state(user_id, "admin")
    text = "👤 FOYDALANUVCHILAR\n\n"
    
    for uid, profile in user_profiles.items():
        orders = user_orders.get(uid, [])
        total_spent_usd = sum(order["total_usd"] for order in orders)
        formatted_total = format_price(total_spent_usd)
        
        name = profile.get('name', "Noma'lum")
        text += f"👤 Ism: {name}\n"
        text += f"🆔 ID: {uid}\n"
        joined = profile.get('joined', "Noma'lum")[:10]
        text += f"📅 Qo'shilgan: {joined}\n"
        text += f"📦 Buyurtmalar: {len(orders)}\n"
        text += f"💰 Sarflangan: {formatted_total}\n\n"
    
    if not user_profiles:
        text += "Hali foydalanuvchilar yo'q."
    
    await message.reply_text(text, reply_markup=admin_keyboard())


async def admin_show_stats(message, user_id):
    if not is_admin(user_id):
        await send_main_menu(message, user_id)
        return
    
    set_state(user_id, "admin")
    
    total_users = len(user_profiles)
    total_orders = sum(len(orders) for orders in user_orders.values())
    total_revenue_usd = sum(
        order["total_usd"] 
        for orders in user_orders.values() 
        for order in orders
    )
    total_payments = sum(len(payments) for payments in payment_history.values())
    formatted_revenue = format_price(total_revenue_usd)
    
    text = (
        "📊 STATISTIKA\n\n"
        f"👤 Jami foydalanuvchilar: {total_users}\n"
        f"📦 Jami buyurtmalar: {total_orders}\n"
        f"💳 Jami to'lovlar: {total_payments}\n"
        f"💰 Jami daromad: {formatted_revenue}"
    )
    
    await message.reply_text(text, reply_markup=admin_keyboard())


async def admin_show_pending_orders(message, user_id):
    if not is_admin(user_id):
        await send_main_menu(message, user_id)
        return
    
    set_state(user_id, "admin")
    text = "⏳ KUTILAYOTGAN BUYURTMALAR\n\n"
    
    total_pending = 0
    for uid, orders in user_orders.items():
        for order in orders:
            if order["status"] == "pending":
                total_pending += 1
                formatted_total = format_price(order["total_usd"])
                user_name = user_profiles.get(uid, {}).get("name", "Noma'lum")
                text += f"🧾 Buyurtma #{order['id']}\n"
                text += f"👤 Foydalanuvchi: {user_name} (ID: {uid})\n"
                text += f"💰 {formatted_total}\n"
                text += f"📅 {order['date'][:10]}\n"
                payment_method = order.get('payment_method', "Noma'lum")
            text += f"💳 {payment_method}\n\n"
    
    if total_pending == 0:
        text += "Hali kutilayotgan buyurtmalar yo'q."
    
    await message.reply_text(text, reply_markup=admin_keyboard())


async def admin_broadcast_start(message, user_id):
    if not is_admin(user_id):
        await send_main_menu(message, user_id)
        return
    
    set_state(user_id, "admin_broadcast")
    broadcast_states[user_id] = {"step": "waiting_message"}
    
    await message.reply_text(
        "📢 XABAR YUBORISH\n\n"
        "Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yozing:",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton(BTN_ADMIN_BACK)]], resize_keyboard=True),
    )


async def admin_broadcast_send(message, user_id, context, text):
    if not is_admin(user_id):
        await send_main_menu(message, user_id)
        return
    
    if not user_profiles:
        await message.reply_text(
            "❌ Foydalanuvchilar yo'q!",
            reply_markup=admin_keyboard(),
        )
        set_state(user_id, "admin")
        return
    
    success_count = 0
    fail_count = 0
    
    for uid in user_profiles.keys():
        try:
            await context.bot.send_message(chat_id=uid, text=text)
            success_count += 1
        except Exception:
            fail_count += 1
    
    set_state(user_id, "admin")
    await message.reply_text(
        f"📢 Xabar yuborildi!\n\n"
        f"✅ Muvaffaqiyatli: {success_count}\n"
        f"❌ Xato: {fail_count}",
        reply_markup=admin_keyboard(),
    )


async def generate_daily_report(context):
    """Generate daily report and send to admins"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Create Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Kunlik Hisobot"
    
    # Headers
    ws.append(["Buyurtma ID", "Foydalanuvchi", "Mahsulotlar", "Jami", "Valyuta", "To'lov usuli", "Sana", "Status"])
    
    # Add orders from today
    for uid, orders in user_orders.items():
        user_name = user_profiles.get(uid, {}).get("name", "Noma'lum")
        for order in orders:
            if order["date"].startswith(today):
                items = ", ".join([f"{item['name']}×{item['quantity']}" for item in order["items"]])
                ws.append([
                    order["id"],
                    f"{user_name} ({uid})",
                    items,
                    order["total_usd"],
                    order["currency"],
                    order.get("payment_method", "Noma'lum"),
                    order["date"],
                    order["status"]
                ])
    
    # Save Excel file
    filename = f"daily_report_{today}.xlsx"
    wb.save(filename)
    
    # Send to all admins
    for admin_id in ADMIN_IDS:
        try:
            with open(filename, "rb") as file:
                await context.bot.send_document(
                    chat_id=admin_id,
                    document=file,
                    caption=f"📈 Kunlik hisobot - {today}\n\nJami buyurtmalar: {ws.max_row - 1}"
                )
        except Exception as e:
            print(f"Error sending report to admin {admin_id}: {e}")
    
    # Clean up
    os.remove(filename)


async def schedule_daily_reports(application):
    """Schedule daily report at 23:00"""
    async def run_scheduler():
        while True:
            schedule.run_pending()
            await asyncio.sleep(60)
    
    async def scheduled_report():
        await generate_daily_report(application)
    
    schedule.every().day.at("23:00").do(scheduled_report)
    await run_scheduler()


async def add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start product addition process"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    
    set_state(user_id, "add_product_category")
    product_edit_states[user_id] = {"step": "category"}
    
    categories = "\n".join([f"- {cid}: {cat['name']}" for cid, cat in PRODUCTS.items()])
    await update.message.reply_text(
        "🆕 MAHSULOT QO'SHISH\n\n"
        f"Mavjud kategoriyalar:\n{categories}\n\n"
        "Kategoriya IDsini kiriting (masalan: drinks):",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton(BTN_ADMIN_BACK)]], resize_keyboard=True),
    )


async def edit_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start product editing process"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    
    set_state(user_id, "edit_product_select")
    product_edit_states[user_id] = {"step": "select"}
    
    # List all products
    text = "✏️ MAHSULOTNI O'ZGARTIRISH\n\n"
    for cat_id, category in PRODUCTS.items():
        text += f"📁 {category['name']} ({cat_id}):\n"
        for prod_id, product in category["items"].items():
            text += f"  - {prod_id}: {product['name']} ({format_price(product['price'])})\n"
        text += "\n"
    
    await update.message.reply_text(
        text + "O'zgartirmoqchi bo'lgan mahsulot IDsini kiriting (masalan: drinks_coca_cola):",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton(BTN_ADMIN_BACK)]], resize_keyboard=True),
    )


async def handle_back(message, user_id):
    state = user_states.get(user_id, {}).get("screen", "main")

    if state == "categories":
        await send_main_menu(message, user_id)
    elif state == "products":
        await send_categories(message, user_id)
    elif state == "product_detail":
        await send_products(message, user_id, user_states[user_id]["category_id"])
    elif state == "checkout":
        await send_categories(message, user_id)
    elif state == "payment_methods":
        await send_checkout(message, user_id)
    elif state in ("tng_payment", "cash_payment"):
        await send_payment_methods(message, user_id)
    elif state == "admin":
        await send_main_menu(message, user_id)
    else:
        await send_main_menu(message, user_id)


async def update_cart_quantity(message, user_id, category_id, product_id, change):
    cart_key = f"{category_id}_{product_id}"
    current_quantity = user_carts[user_id].get(cart_key, 0)
    new_quantity = max(0, current_quantity + change)

    if new_quantity == 0:
        user_carts[user_id].pop(cart_key, None)
    else:
        user_carts[user_id][cart_key] = new_quantity

    await send_product_details(message, user_id, category_id, product_id)


async def handle_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    init_user(user_id)

    # Handle product image upload
    state = user_states.get(user_id, {}).get("screen")
    if state == "add_product_image":
        if update.message.photo:
            # Get the largest photo
            photo = update.message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
            
            # Create images directory if not exists
            if not os.path.exists("images"):
                os.makedirs("images")
            
            # Save image
            category_id = product_edit_states[user_id]["category"]
            product_id = product_edit_states[user_id]["product_id"]
            image_path = f"images/{category_id}_{product_id}.jpg"
            
            await file.download_to_drive(image_path)
            
            # Add product with image
            PRODUCTS[category_id]["items"][product_id] = {
                "name": product_edit_states[user_id]["name"],
                "price": product_edit_states[user_id]["price"],
                "emoji": product_edit_states[user_id]["emoji"],
                "image": image_path
            }
            
            del product_edit_states[user_id]
            set_state(user_id, "admin")
            
            await update.message.reply_text(
                f"✅ Mahsulot qo'shildi!\n\n"
                f"📦 Kategoriya: {PRODUCTS[category_id]['name']}\n"
                f"🆔 ID: {product_id}\n"
                f"📝 Nomi: {PRODUCTS[category_id]['items'][product_id]['name']}\n"
                f"💰 Narxi: {format_price(PRODUCTS[category_id]['items'][product_id]['price'])}\n"
                f"🎨 Emoji: {product_edit_states.get('emoji', 'N/A')}\n"
                f"🖼️ Rasm: {image_path}",
                reply_markup=admin_keyboard(),
            )
        return
    
    if state == "edit_product_image":
        if update.message.photo:
            # Get the largest photo
            photo = update.message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
            
            # Create images directory if not exists
            if not os.path.exists("images"):
                os.makedirs("images")
            
            # Save image
            category_id = product_edit_states[user_id]["category"]
            product_id = product_edit_states[user_id]["product_id"]
            image_path = f"images/{category_id}_{product_id}.jpg"
            
            await file.download_to_drive(image_path)
            
            # Update product with new image
            PRODUCTS[category_id]["items"][product_id]["image"] = image_path
            
            del product_edit_states[user_id]
            set_state(user_id, "admin")
            
            await update.message.reply_text(
                f"✅ Mahsulot o'zgartirildi!\n\n"
                f"📦 Kategoriya: {PRODUCTS[category_id]['name']}\n"
                f"🆔 ID: {product_id}\n"
                f"📝 Nomi: {PRODUCTS[category_id]['items'][product_id]['name']}\n"
                f"💰 Narxi: {format_price(PRODUCTS[category_id]['items'][product_id]['price'])}\n"
                f"🎨 Emoji: {PRODUCTS[category_id]['items'][product_id]['emoji']}\n"
                f"🖼️ Rasm: {image_path}",
                reply_markup=admin_keyboard(),
            )
        return

    if user_id not in payment_proofs:
        return

    proof = payment_proofs[user_id]
    order_id = proof["order_id"]

    order_pending = any(
        o["id"] == order_id and o["status"] == "pending"
        for o in user_orders.get(user_id, [])
    )
    if not order_pending:
        return

    proof["proof_sent"] = True

    if proof["proof_type"] == "receipt":
        await update.message.reply_text(
            f"✅ Receipt qabul qilindi!\n\nEndi \"{BTN_RECEIPT_SENT}\" tugmasini bosing.",
            reply_markup=tng_payment_keyboard(),
        )
    else:
        await update.message.reply_text(
            f"✅ Rasm qabul qilindi!\n\nEndi \"{BTN_PHOTO_SENT}\" tugmasini bosing.",
            reply_markup=cash_payment_keyboard(),
        )


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    text = update.message.text.strip()
    init_user(user_id, get_user_name(update.effective_user))
    message = update.message

    # Handle broadcast message input
    state = user_states.get(user_id, {}).get("screen")
    if state == "admin_broadcast" and text != BTN_ADMIN_BACK:
        await admin_broadcast_send(message, user_id, context, text)
        return
    
    # Handle product addition steps
    if state == "add_product_category" and text != BTN_ADMIN_BACK:
        if text in PRODUCTS:
            product_edit_states[user_id]["category"] = text
            product_edit_states[user_id]["step"] = "product_id"
            set_state(user_id, "add_product_id")
            await message.reply_text(
                f"Kategoriya: {PRODUCTS[text]['name']}\n\n"
                "Mahsulot IDsini kiriting (masalan: new_drink):",
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton(BTN_ADMIN_BACK)]], resize_keyboard=True),
            )
        else:
            await message.reply_text("❌ Noto'g'ri kategoriya ID! Qaytadan kiriting:")
        return
    
    if state == "add_product_id" and text != BTN_ADMIN_BACK:
        product_edit_states[user_id]["product_id"] = text
        product_edit_states[user_id]["step"] = "name"
        set_state(user_id, "add_product_name")
        await message.reply_text(
            "Mahsulot nomini kiriting:",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton(BTN_ADMIN_BACK)]], resize_keyboard=True),
        )
        return
    
    if state == "add_product_name" and text != BTN_ADMIN_BACK:
        product_edit_states[user_id]["name"] = text
        product_edit_states[user_id]["step"] = "price"
        set_state(user_id, "add_product_price")
        await message.reply_text(
            "Mahsulot narxini RM da kiriting (masalan: 2.50):",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton(BTN_ADMIN_BACK)]], resize_keyboard=True),
        )
        return
    
    if state == "add_product_price" and text != BTN_ADMIN_BACK:
        try:
            price = float(text)
            # Convert RM to USD for storage
            price_usd = price / 4.75
            product_edit_states[user_id]["price"] = price_usd
            product_edit_states[user_id]["step"] = "emoji"
            set_state(user_id, "add_product_emoji")
            await message.reply_text(
                "Mahsulot emoji sini kiriting (masalan: 🥤):",
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton(BTN_ADMIN_BACK)]], resize_keyboard=True),
            )
        except ValueError:
            await message.reply_text("❌ Noto'g'ri narx! Raqam kiriting:")
        return
    
    if state == "add_product_emoji" and text != BTN_ADMIN_BACK:
        product_edit_states[user_id]["emoji"] = text
        product_edit_states[user_id]["step"] = "image"
        set_state(user_id, "add_product_image")
        await message.reply_text(
            "Mahsulot rasmini yuboring (yoki 'skip' deb yozing, rasm yo'q):",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("skip"), KeyboardButton(BTN_ADMIN_BACK)]], resize_keyboard=True),
        )
        return
    
    if state == "add_product_image" and text != BTN_ADMIN_BACK:
        if text.lower() == "skip":
            # Skip image, add product without image
            category_id = product_edit_states[user_id]["category"]
            product_id = product_edit_states[user_id]["product_id"]
            
            PRODUCTS[category_id]["items"][product_id] = {
                "name": product_edit_states[user_id]["name"],
                "price": product_edit_states[user_id]["price"],
                "emoji": product_edit_states[user_id]["emoji"]
            }
            
            del product_edit_states[user_id]
            set_state(user_id, "admin")
            
            await message.reply_text(
                f"✅ Mahsulot qo'shildi!\n\n"
                f"📦 Kategoriya: {PRODUCTS[category_id]['name']}\n"
                f"🆔 ID: {product_id}\n"
                f"📝 Nomi: {PRODUCTS[category_id]['items'][product_id]['name']}\n"
                f"💰 Narxi: {format_price(PRODUCTS[category_id]['items'][product_id]['price'])}\n"
                f"🎨 Emoji: {product_edit_states[user_id]['emoji']}",
                reply_markup=admin_keyboard(),
            )
        return
    
    # Handle edit_product_image skip option
    if state == "edit_product_image" and text != BTN_ADMIN_BACK:
        if text.lower() == "skip":
            category_id = product_edit_states[user_id]["category"]
            product_id = product_edit_states[user_id]["product_id"]
            
            # Remove image from product
            if "image" in PRODUCTS[category_id]["items"][product_id]:
                del PRODUCTS[category_id]["items"][product_id]["image"]
            
            del product_edit_states[user_id]
            set_state(user_id, "admin")
            
            await message.reply_text(
                f"✅ Mahsulot o'zgartirildi!\n\n"
                f"📦 Kategoriya: {PRODUCTS[category_id]['name']}\n"
                f"🆔 ID: {product_id}\n"
                f"📝 Nomi: {PRODUCTS[category_id]['items'][product_id]['name']}\n"
                f"💰 Narxi: {format_price(PRODUCTS[category_id]['items'][product_id]['price'])}\n"
                f"🎨 Emoji: {PRODUCTS[category_id]['items'][product_id]['emoji']}\n"
                f"🖼️ Rasm: O'chirildi",
                reply_markup=admin_keyboard(),
            )
        return
    
    # Handle product editing steps
    if state == "edit_product_select" and text != BTN_ADMIN_BACK:
        if "_" in text:
            parts = text.split("_", 1)
            if len(parts) == 2 and parts[0] in PRODUCTS and parts[1] in PRODUCTS[parts[0]]["items"]:
                product_edit_states[user_id]["category"] = parts[0]
                product_edit_states[user_id]["product_id"] = parts[1]
                product_edit_states[user_id]["step"] = "edit_field"
                set_state(user_id, "edit_product_field")
                
                product = PRODUCTS[parts[0]]["items"][parts[1]]
                await message.reply_text(
                    f"Mahsulot: {product['name']}\n\n"
                    "Qaysi maydonni o'zgartirmoqchisiz?\n\n"
                    "1. name - Nomi\n"
                    "2. price - Narxi\n"
                    "3. emoji - Emoji\n"
                    "4. image - Rasm",
                    reply_markup=ReplyKeyboardMarkup(
                        [
                            [KeyboardButton("name"), KeyboardButton("price"), KeyboardButton("emoji")],
                            [KeyboardButton("image"), KeyboardButton(BTN_ADMIN_BACK)]
                        ],
                        resize_keyboard=True,
                    ),
                )
            else:
                await message.reply_text("❌ Noto'g'ri mahsulot ID! Qaytadan kiriting:")
        else:
            await message.reply_text("❌ Noto'g'ri format! Masalan: drinks_coca_cola")
        return
    
    if state == "edit_product_field" and text != BTN_ADMIN_BACK:
        if text in ["name", "price", "emoji", "image"]:
            product_edit_states[user_id]["field"] = text
            
            if text == "image":
                product_edit_states[user_id]["step"] = "edit_image"
                set_state(user_id, "edit_product_image")
                await message.reply_text(
                    "Yangi rasmni yuboring (yoki 'skip' deb yozing, rasmni o'chirish):",
                    reply_markup=ReplyKeyboardMarkup([[KeyboardButton("skip"), KeyboardButton(BTN_ADMIN_BACK)]], resize_keyboard=True),
                )
            else:
                product_edit_states[user_id]["step"] = "edit_value"
                set_state(user_id, "edit_product_value")
                
                field_names = {"name": "nomi", "price": "narxi", "emoji": "emoji"}
                prompt_text = f"Yangi {field_names[text]}ni kiriting:"
                if text == "price":
                    prompt_text += " (RM da)"
                await message.reply_text(
                    prompt_text,
                    reply_markup=ReplyKeyboardMarkup([[KeyboardButton(BTN_ADMIN_BACK)]], resize_keyboard=True),
                )
        else:
            await message.reply_text("❌ Noto'g'ri maydon! name, price, emoji yoki image tanlang:")
        return
    
    if state == "edit_product_value" and text != BTN_ADMIN_BACK:
        category_id = product_edit_states[user_id]["category"]
        product_id = product_edit_states[user_id]["product_id"]
        field = product_edit_states[user_id]["field"]
        
        if field == "price":
            try:
                value = float(text)
                # Convert RM to USD for storage
                value_usd = value / 4.75
                PRODUCTS[category_id]["items"][product_id][field] = value_usd
            except ValueError:
                await message.reply_text("❌ Noto'g'ri narx! Raqam kiriting:")
                return
        else:
            PRODUCTS[category_id]["items"][product_id][field] = text
        
        del product_edit_states[user_id]
        set_state(user_id, "admin")
        
        await message.reply_text(
            f"✅ Mahsulot o'zgartirildi!\n\n"
            f"📦 Kategoriya: {PRODUCTS[category_id]['name']}\n"
            f"🆔 ID: {product_id}\n"
            f"📝 Nomi: {PRODUCTS[category_id]['items'][product_id]['name']}\n"
            f"💰 Narxi: {format_price(PRODUCTS[category_id]['items'][product_id]['price'])}\n"
            f"🎨 Emoji: {PRODUCTS[category_id]['items'][product_id]['emoji']}",
            reply_markup=admin_keyboard(),
        )
        return

    # Admin panel buttons
    if text == BTN_ADMIN_ORDERS:
        await admin_show_all_orders(message, user_id)
        return
    if text == BTN_ADMIN_PENDING:
        await admin_show_pending_orders(message, user_id)
        return
    if text == BTN_ADMIN_PAYMENTS:
        await admin_show_all_payments(message, user_id)
        return
    if text == BTN_ADMIN_USERS:
        await admin_show_users(message, user_id)
        return
    if text == BTN_ADMIN_STATS:
        await admin_show_stats(message, user_id)
        return
    if text == BTN_ADMIN_BROADCAST:
        await admin_broadcast_start(message, user_id)
        return
    if text == BTN_ADMIN_BACK:
        await handle_back(message, user_id)
        return

    # Regular user buttons
    if text == BTN_BUY:
        await send_categories(message, user_id)
        return
    if text == BTN_ORDERS:
        await send_orders(message, user_id)
        return
    if text == BTN_PAYMENTS:
        await send_payment_history(message, user_id)
        return
    if text == BTN_PROFILE:
        await send_profile(message, user_id)
        return
    if text == BTN_BACK:
        await handle_back(message, user_id)
        return
    if text == BTN_PAY:
        await send_payment_methods(message, user_id)
        return
    if text == BTN_CHECKOUT:
        await send_checkout(message, user_id)
        return
    if text == BTN_TNG:
        await send_tng_qr_payment(message, user_id, context)
        return
    if text == BTN_CASH:
        await send_cash_payment(message, user_id, context)
        return
    if text == BTN_RECEIPT_SENT:
        proof = payment_proofs.get(user_id)
        if proof:
            await complete_payment(message, user_id, proof["order_id"])
        return
    if text == BTN_PHOTO_SENT:
        proof = payment_proofs.get(user_id)
        if proof:
            await complete_payment(message, user_id, proof["order_id"])
        return
    if text == BTN_MINUS or text == BTN_PLUS:
        state = user_states.get(user_id, {})
        if state.get("screen") == "product_detail":
            change = 1 if text == BTN_PLUS else -1
            await update_cart_quantity(
                message, user_id, state["category_id"], state["product_id"], change
            )
        return

    category_id = find_category(text)
    if category_id:
        await send_products(message, user_id, category_id)
        return

    category_id, product_id = find_product(text)
    if category_id and product_id:
        await send_product_details(message, user_id, category_id, product_id)
        return


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("add_product", add_product_start))
    application.add_handler(CommandHandler("edit_product", edit_product_start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_payment_proof))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_payment_proof))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    # Start daily report scheduler as background task
    async def start_scheduler():
        await application.initialize()
        await application.start()
        asyncio.create_task(schedule_daily_reports(application))
        await application.updater.start_polling()

    print("Bot ishga tushdi...")
    application.run_polling()


if __name__ == "__main__":
    main()
