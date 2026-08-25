# To'lov Tizimi Integratsiyasi

## Bank Karta To'lovi (Credit/Debit Card)

### 1. Stripe (Xalqaro - Eng oson)
- **API:** https://stripe.com/docs/api
- **Qo'llab-quvvatlaydigan kartalar:** Visa, Mastercard, American Express, Discover
- **Jarayon:**
  1. Stripe account oching (https://dashboard.stripe.com/register)
  2. API key oling (Publishable key va Secret key)
  3. Stripe Checkout yoki Payment Intent ishlating
  4. Webhook orqali statusni tekshiring

**Integratsiya misoli:**
```python
import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_stripe_payment_link(amount_usd, currency, order_id):
    try:
        # Convert to local currency
        if currency == "UZS":
            amount = int(amount_usd * 12900)  # UZS
        elif currency == "RM":
            amount = int(amount_usd * 4.75 * 100)  # RM (in cents)
        else:
            amount = int(amount_usd * 100)  # USD (in cents)
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': currency.lower(),
                    'product_data': {
                        'name': f'Order #{order_id}',
                    },
                    'unit_amount': amount,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='https://your-bot.com/success',
            cancel_url='https://your-bot.com/cancel',
            metadata={'order_id': str(order_id)}
        )
        
        return session.url
    except Exception as e:
        print(f"Stripe error: {e}")
        return None
```

### 2. PayPal (Xalqiko)
- **API:** https://developer.paypal.com/docs/api/
- **Qo'llab-quvvatlaydigan kartalar:** Visa, Mastercard, American Express, Discover
- **Jarayon:**
  1. PayPal Developer account oching
  2. Client ID va Secret oling
  3. PayPal API orqali payment yaratish

### 3. O'zbekistonda Bank Karta To'lovi

#### Uzum Bank (Uzum)
- **API:** https://uzum.uz/developers
- **Qo'llab-quvvatlaydigan kartalar:** Uzum, Humo, Uzcard
- **Jarayon:**
  1. Uzum merchant account oching
  2. API integration

#### Click (Card Payment)
- **API:** https://click.uz/developers
- **Qo'llab-quvvatlaydigan kartalar:** Uzcard, Humo, Visa, Mastercard
- **Jarayon:**
  1. Click merchant account oching
  2. Card payment API ishlating

#### Payme (Card Payment)
- **API:** https://payme.uz/developers
- **Qo'llab-quvvatlaydigan kartalar:** Uzcard, Humo, Visa, Mastercard
- **Jarayon:**
  1. Payme merchant account oching
  2. Card payment API ishlating

## Malayziya uchun to'lov tizimlari

### 1. Touch 'n Go (TNG) Digital
- **API:** https://www.tngdigital.com.my/developers
- **Jarayon:**
  1. TNG Digital Merchant account ochish
  2. API key olish
  3. Payment link yaratish
  4. Webhook orqali statusni tekshirish

### 2. FPX (Online Banking)
- **API:** Banklar orqali
- **Jarayon:**
  1. Payment gateway (iPay88, SenangPay) orqali
  2. Bank tanlash
  3. Direct debit

### 3. Stripe (Xalqaro)
- **API:** https://stripe.com/docs/api
- **Jarayon:**
  1. Stripe account ochish
  2. API key olish
  3. Stripe Checkout link yaratish
  4. Webhook bilan statusni tekshirish

## O'zbekiston uchun to'lov tizimlari

### 1. Click
- **API:** https://click.uz/developers
- **Jarayon:**
  1. Click merchant account ochish
  2. API key olish
  3. Payment link yaratish
  4. Webhook orqali statusni tekshirish

### 2. Payme
- **API:** https://payme.uz/developers
- **Jarayon:**
  1. Payme merchant account ochish
  2. API key olish
  3. Payment link yaratish
  4. Webhook orqali statusni tekshirish

### 3. Uzum
- **API:** https://uzum.uz/developers
- **Jarayon:**
  1. Uzum merchant account ochish
  2. API integration

## Botga integratsiya qilish

### 1. .env fayliga qo'shing:
```
CLICK_MERCHANT_ID=your_click_merchant_id
CLICK_SECRET_KEY=your_click_secret_key
PAYME_MERCHANT_ID=your_payme_merchant_id
PAYME_SECRET_KEY=your_payme_secret_key
STRIPE_API_KEY=your_stripe_api_key
```

### 2. bot.py da process_payment funksiyasini yangilang:
```python
async def process_payment(query, user_id):
    global order_counter
    
    if not user_carts[user_id]:
        await show_categories(query, user_id)
        return
    
    currency = user_currencies[user_id]
    total_usd = 0
    items_text = ""
    order_items = []
    
    for cart_key, quantity in user_carts[user_id].items():
        category_id, product_id = cart_key.split("_", 1)
        product = get_product_info(category_id, product_id)
        if product:
            item_total_usd = product["price"] * quantity
            total_usd += item_total_usd
            items_text += f"{product['emoji']} {product['name']} ×{quantity}\n"
            order_items.append({
                "name": product["name"],
                "quantity": quantity,
                "price_usd": product["price"],
                "total_usd": item_total_usd
            })
    
    # Payment link yaratish (misol: Click)
    payment_link = create_click_payment_link(total_usd, currency, order_id)
    
    # Payment link yuborish
    await query.edit_message_text(
        f"💳 To'lov\n\n"
        f"{items_text}\n"
        f"Jami: {format_price(total_usd, currency)}\n\n"
        f"To'lov uchun quyidagi linkni bosing:\n"
        f"{payment_link}\n\n"
        f"To'lov tugagach, botga qaytiring.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 To'lov qilish", url=payment_link)],
            [InlineKeyboardButton("✅ To'lov tugadi", callback_data="payment_completed")]
        ])
    )
```

### 3. Payment link yaratish funksiyasi (Click misoli):
```python
def create_click_payment_link(amount_usd, currency, order_id):
    import requests
    
    # Convert to local currency
    if currency == "UZS":
        amount = int(amount_usd * 12900)
    elif currency == "RM":
        amount = amount_usd * 4.75
    else:
        amount = amount_usd
    
    # Click API call
    merchant_id = os.getenv("CLICK_MERCHANT_ID")
    secret_key = os.getenv("CLICK_SECRET_KEY")
    
    # Create payment request
    params = {
        "merchant_id": merchant_id,
        "amount": amount,
        "currency": currency,
        "order_id": order_id
    }
    
    # API call (misol)
    response = requests.post("https://click.uz/api/payment", json=params)
    return response.json().get("payment_link")
```

### 4. Webhook endpoint qo'shish:
```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/webhook/payment', methods=['POST'])
def payment_webhook():
    data = request.json
    
    if data['status'] == 'success':
        order_id = data['order_id']
        # Update order status
        # Send notification to user
    
    return {"status": "ok"}
```

## Test qilish

1. Sandbox environment muvaffaqiyatli ishlashini tekshiring
2. Kichik summa bilan test qiling
3. Webhook ishlashini tekshiring
4. Productionga o'tishdan oldin barcha testlarni bajaring
