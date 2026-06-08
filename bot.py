import requests
import time
import asyncio
import os
from datetime import datetime
from telegram import Bot

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

bot = None

# ┘à╪¬╪║┘è╪▒ ┘ä╪¬╪«╪▓┘è┘å ╪º┘ä┘Ç CHAT_ID ╪¿╪╣╪» ╪¼┘ä╪¿┘ç ╪¬┘ä┘é╪º╪ª┘è╪º┘ï
MY_CHAT_ID = None

SYMBOLS = {
    "XAUUSD": "╪º┘ä╪░┘ç╪¿ (XAU/USD)",
    "XAGUSD": "╪º┘ä┘ü╪╢╪⌐ (XAG/USD)"
}

QOS_BASE_URL = "https://quote.qos.hk"

def get_chat_id_automatically():
    """╪¬╪¼┘ä╪¿ ╪º┘ä┘Ç CHAT_ID ╪¬┘ä┘é╪º╪ª┘è╪º┘ï ┘à┘å ╪ó╪«╪▒ ╪¬╪¡╪»┘è╪½ ┘ä┘ä╪¿┘ê╪¬"""
    global MY_CHAT_ID
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("ok") and data.get("result"):
            # ┘å╪ú╪«╪░ ╪º┘ä┘Ç chat_id ┘à┘å ╪ó╪«╪▒ ╪▒╪│╪º┘ä╪⌐ ╪ú┘ê ╪ú┘à╪▒ /start
            last_update = data["result"][-1]
            MY_CHAT_ID = last_update["message"]["chat"]["id"]
            print(f"Γ£à ╪¬┘à ╪¼┘ä╪¿ Chat ID ╪¬┘ä┘é╪º╪ª┘è╪º┘ï: {MY_CHAT_ID}")
            return True
        else:
            print("ΓÜá∩╕Å ┘ä╪º ╪¬┘ê╪¼╪» ╪▒╪│╪º╪ª┘ä ╪¿╪╣╪». ╪ú╪▒╪│┘ä /start ┘ä┘ä╪¿┘ê╪¬ ╪½┘à ╪ú╪╣╪» ╪º┘ä╪¬╪┤╪║┘è┘ä.")
            return False
    except Exception as e:
        print(f"Γ¥î ╪«╪╖╪ú ┘ü┘è ╪¼┘ä╪¿ Chat ID: {e}")
        return False

def get_price_qos(symbol):
    """╪¼┘ä╪¿ ╪º┘ä╪│╪╣╪▒ ┘à┘å QOS API"""
    try:
        url = f"{QOS_BASE_URL}/api/quote?symbol={symbol}"
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            price = data.get('price') or data.get('last') or data.get('c')
            if price:
                return float(price)
        return None
    except Exception as e:
        print(f"ΓÜá∩╕Å ╪«╪╖╪ú ┘ü┘è ╪¼┘ä╪¿ ╪│╪╣╪▒ {symbol}: {e}")
        return None

def get_kline_data(symbol, interval="5min", limit=50):
    """╪¼┘ä╪¿ ╪¿┘è╪º┘å╪º╪¬ ╪º┘ä╪┤┘à┘ê╪╣"""
    try:
        url = f"{QOS_BASE_URL}/api/kline"
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                return data['data']
            elif isinstance(data, list):
                return data
        return []
    except Exception as e:
        print(f"ΓÜá∩╕Å ╪«╪╖╪ú ┘ü┘è ╪¿┘è╪º┘å╪º╪¬ ╪º┘ä╪┤┘à┘ê╪╣ ┘ä┘Ç {symbol}: {e}")
        return []

async def start_health_server():
    """Start a simple HTTP health server for Render port binding."""
    port = int(os.environ.get("PORT", "8000"))

    async def handle_client(reader, writer):
        await reader.read(1024)
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain\r\n"
            "Content-Length: 13\r\n"
            "Connection: close\r\n"
            "\r\n"
            "Bot is alive\n"
        )
        writer.write(response.encode())
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle_client, "0.0.0.0", port)
    addr = server.sockets[0].getsockname()
    print(f"≡ƒîÉ Health server listening on http://{addr[0]}:{addr[1]}")
    return server


def validate_bot_token():
    """Validate bot token by checking the Telegram bot account."""
    try:
        me = bot.get_me()
        print(f"≡ƒôî ╪º╪│╪¬╪«╪»┘à Bot @{me.username} connected successfully.")
        return True
    except Exception as e:
        print(f"Γ¥î ╪«╪╖╪ú: invalid TELEGRAM_TOKEN or Telegram API error: {e}")
        return False


def calculate_ema(prices, period=12):
    """╪¡╪│╪º╪¿ EMA"""
    if len(prices) < period:
        return prices[-1] if prices else 0
    multiplier = 2 / (period + 1)
    ema = prices[0]
    for price in prices[1:]:
        ema = (price - ema) * multiplier + ema
    return ema

def calculate_rsi(prices, period=14):
    """╪¡╪│╪º╪¿ RSI"""
    if len(prices) < period + 1:
        return 50
    gains, losses = [], []
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        if diff > 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))
    avg_gain = sum(gains[-period:]) / period if gains else 0
    avg_loss = sum(losses[-period:]) / period if losses else 0
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def generate_signal(symbol_name, kline_data):
    """╪¬┘ê┘ä┘è╪» ╪º┘ä╪Ñ╪┤╪º╪▒╪⌐"""
    if not kline_data or len(kline_data) < 20:
        return "╪º┘å╪¬╪╕╪º╪▒", 0, "╪¿┘è╪º┘å╪º╪¬ ╪║┘è╪▒ ┘â╪º┘ü┘è╪⌐"
    
    closes = []
    for item in kline_data:
        if isinstance(item, dict):
            close = item.get('close') or item.get('c')
        elif isinstance(item, (list, tuple)) and len(item) >= 5:
            close = item[4]
        else:
            continue
        if close:
            try:
                closes.append(float(close))
            except:
                pass
    
    if len(closes) < 15:
        return "╪º┘å╪¬╪╕╪º╪▒", 0, f"╪¿┘è╪º┘å╪º╪¬ ╪║┘è╪▒ ┘â╪º┘ü┘è╪⌐ ({len(closes)} ╪┤┘à╪╣╪⌐)"
    
    ema_fast = calculate_ema(closes, 9)
    ema_slow = calculate_ema(closes, 21)
    rsi = calculate_rsi(closes, 14)
    
    signal = "╪º┘å╪¬╪╕╪º╪▒"
    confidence = 50
    reasons = []
    
    if ema_fast > ema_slow and closes[-2] <= ema_slow:
        signal = "╪┤╪▒╪º╪í ≡ƒƒó"
        confidence = 70
        reasons.append("╪¬┘é╪º╪╖╪╣ EMA ╪╡╪º╪╣╪»")
    elif ema_fast < ema_slow and closes[-2] >= ema_slow:
        signal = "╪¿┘è╪╣ ≡ƒö┤"
        confidence = 70
        reasons.append("╪¬┘é╪º╪╖╪╣ EMA ┘ç╪º╪¿╪╖")
    
    if signal == "╪º┘å╪¬╪╕╪º╪▒":
        if rsi < 30 and ema_fast > ema_slow:
            signal = "╪┤╪▒╪º╪í ≡ƒƒó"
            confidence = 65
            reasons.append(f"RSI {rsi:.1f} ┘à╪╣ ╪º╪¬╪¼╪º┘ç ╪╡╪º╪╣╪»")
        elif rsi > 70 and ema_fast < ema_slow:
            signal = "╪¿┘è╪╣ ≡ƒö┤"
            confidence = 65
            reasons.append(f"RSI {rsi:.1f} ┘à╪╣ ╪º╪¬╪¼╪º┘ç ┘ç╪º╪¿╪╖")
    
    if signal == "╪º┘å╪¬╪╕╪º╪▒":
        if rsi < 25:
            signal = "╪┤╪▒╪º╪í ≡ƒƒó"
            confidence = 55
            reasons.append(f"RSI ┘ü┘è ╪░╪▒┘ê╪⌐ ╪¿┘è╪╣ ({rsi:.1f})")
        elif rsi > 80:
            signal = "╪¿┘è╪╣ ≡ƒö┤"
            confidence = 55
            reasons.append(f"RSI ┘ü┘è ╪░╪▒┘ê╪⌐ ╪┤╪▒╪º╪í ({rsi:.1f})")
    
    if signal == "╪º┘å╪¬╪╕╪º╪▒":
        reasons.append(f"RSI {rsi:.1f} ┘ü┘è ┘à┘å╪╖┘é╪⌐ ┘à╪¡╪º┘è╪»╪⌐")
    
    return signal, confidence, "\nΓÇó ".join(reasons)

async def send_signal():
    """╪Ñ╪▒╪│╪º┘ä ╪º┘ä╪Ñ╪┤╪º╪▒╪⌐"""
    global MY_CHAT_ID
    if not MY_CHAT_ID:
        print("ΓÜá∩╕Å ┘ä╪º ┘è┘à┘â┘å ╪º┘ä╪Ñ╪▒╪│╪º┘ä: ┘ä┘à ┘è╪¬┘à ╪¼┘ä╪¿ Chat ID ╪¿╪╣╪»")
        return
    
    for symbol, name in SYMBOLS.items():
        price = get_price_qos(symbol)
        if not price:
            continue
        
        kline_data = get_kline_data(symbol)
        signal, confidence, reason = generate_signal(name, kline_data)
        
        icon = "≡ƒƒó≡ƒÆ░" if "╪┤╪▒╪º╪í" in signal else "≡ƒö┤≡ƒôë" if "╪¿┘è╪╣" in signal else "ΓÅ│≡ƒôè"
        stars = "Γ¡É" * min(5, confidence // 15)
        
        message = f"""
{icon} *{name}* {icon}

≡ƒÆ░ *╪º┘ä╪│╪╣╪▒ ╪º┘ä╪¡╪º┘ä┘è:* `${price:.2f}`

≡ƒÄ» *╪º┘ä╪Ñ╪┤╪º╪▒╪⌐:* *{signal}*
≡ƒôê *┘å╪│╪¿╪⌐ ╪º┘ä╪½┘é╪⌐:* {confidence}% {stars}

≡ƒô¥ *╪º┘ä╪¬╪¡┘ä┘è┘ä:*
ΓÇó {reason}

ΓÅ░ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
ΓÜá∩╕Å ╪Ñ╪┤╪º╪▒╪⌐ ╪¬╪¡┘ä┘è┘ä ┘ü┘å┘è ┘ü┘é╪╖ - ┘é╪▒╪º╪▒┘â ┘à╪│╪ñ┘ê┘ä┘è╪¬┘â
"""
        try:
            await bot.send_message(chat_id=MY_CHAT_ID, text=message, parse_mode='Markdown')
            print(f"Γ£à ╪¬┘à ╪Ñ╪▒╪│╪º┘ä ╪Ñ╪┤╪º╪▒╪⌐ {name}")
        except Exception as e:
            print(f"Γ¥î ┘ü╪┤┘ä ╪Ñ╪▒╪│╪º┘ä ╪Ñ╪┤╪º╪▒╪⌐ {name}: {e}")
        
        await asyncio.sleep(3)

async def main():
    """╪º┘ä╪¡┘ä┘é╪⌐ ╪º┘ä╪▒╪ª┘è╪│┘è╪⌐"""
    print("≡ƒÜÇ ╪¿┘ê╪¬ ╪º┘ä╪Ñ╪┤╪º╪▒╪º╪¬ ╪┤╪║╪º┘ä...")
    print("≡ƒôí ╪¼╪º╪▒┘è ╪Ñ╪╣╪»╪º╪» ╪º┘ä╪«╪»┘à╪⌐...")

    if not TELEGRAM_TOKEN:
        print("Γ¥î ╪«╪╖╪ú: TELEGRAM_TOKEN ╪║┘è╪▒ ┘à╪╢╪¿┘ê╪╖. ╪º╪╢╪¿╪╖ ╪º┘ä┘à╪¬╪║┘è╪▒ ╪º┘ä╪¿┘è╪ª┘è TELEGRAM_TOKEN.")
        return

    global bot
    bot = Bot(token=TELEGRAM_TOKEN)

    if not validate_bot_token():
        return

    server = await start_health_server()

    global MY_CHAT_ID
    if TELEGRAM_CHAT_ID:
        try:
            MY_CHAT_ID = int(TELEGRAM_CHAT_ID)
            print(f"≡ƒôî ╪º╪│╪¬╪«╪»┘à TELEGRAM_CHAT_ID ┘à┘å ╪º┘ä╪¿┘è╪ª╪⌐: {MY_CHAT_ID}")
        except ValueError:
            print("ΓÜá∩╕Å TELEGRAM_CHAT_ID ╪║┘è╪▒ ╪╡╪º┘ä╪¡╪î ╪º╪│╪¬╪«╪»┘à ┘é┘è┘à╪⌐ ╪▒┘é┘à┘è╪⌐ ╪╡╪¡┘è╪¡╪⌐.")

    if MY_CHAT_ID:
        try:
            bot.send_message(chat_id=MY_CHAT_ID, text="✅ Test message: bot is deployed and can send to this chat.")
            print("≡ƒôî ╪º╪│╪¿╪«╪»┘à ╪º┘ä╪¿┘è╪ª╪⌐ ┘ä╪¬╪¹╪¡╪º: test message sent.")
        except Exception as e:
            print(f"Γ¥î ╪«╪╖╪ú: failed to send test message to TELEGRAM_CHAT_ID: {e}")
            server.close()
            await server.wait_closed()
            return

    if not MY_CHAT_ID:
        print("≡ƒôí ╪¼╪º╪▒┘è ╪¼┘ä╪¿ Chat ID ╪¬┘ä┘é╪º╪ª┘è╪º┘ï...")
        if not get_chat_id_automatically():
            print("Γ¥î ┘ä┘à ┘è╪¬┘à ╪º┘ä╪╣╪½┘ê╪▒ ╪╣┘ä┘ë Chat ID.")
            print("≡ƒÆí ╪ú╪▒╪│┘ä /start ┘ä┘ä╪¿┘ê╪¬ ╪╣┘ä┘ë ╪¬┘ä┘è╪¼╪▒╪º┘à ╪½┘à ╪ú╪╣╪» ╪¬╪┤╪║┘è┘ä ╪º┘ä╪│┘â╪▒╪¿╪¬.")
            server.close()
            await server.wait_closed()
            return

    print(f"≡ƒôè ┘à╪¬╪º╪¿╪╣: {', '.join(SYMBOLS.values())}")
    print("-" * 50)

    try:
        while True:
            try:
                await send_signal()
                print(f"ΓÅ│ ╪º┘å╪¬╪╕╪º╪▒ 5 ╪»┘é╪º╪ª┘é... ({datetime.now().strftime('%H:%M:%S')})")
                await asyncio.sleep(300) # 5 ╪»┘é╪º╪ª┘é
            except Exception as e:
                print(f"ΓÜá∩╕Å ╪«╪╖╪ú: {e}")
                await asyncio.sleep(60)
    finally:
        server.close()
        await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
