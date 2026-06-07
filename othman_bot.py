import requests
import time
import asyncio
import os
from datetime import datetime
from telegram import Bot

# ========== إعداداتك الشخصية ==========
# ضعي رمز البوت من @BotFather فقط
TELEGRAM_TOKEN = "8932925426:AAHh3RWwa4ZwkVBJQeoMhYGFmO5nEgWMJpw"
# =====================================

bot = Bot(token=TELEGRAM_TOKEN)

# متغير لتخزين الـ CHAT_ID بعد جلبه تلقائياً
MY_CHAT_ID = None

SYMBOLS = {
    "XAUUSD": "الذهب (XAU/USD)",
    "XAGUSD": "الفضة (XAG/USD)"
}

QOS_BASE_URL = "https://quote.qos.hk"

def get_chat_id_automatically():
    """تجلب الـ CHAT_ID تلقائياً من آخر تحديث للبوت"""
    global MY_CHAT_ID
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("ok") and data.get("result"):
            # نأخذ الـ chat_id من آخر رسالة أو أمر /start
            last_update = data["result"][-1]
            MY_CHAT_ID = last_update["message"]["chat"]["id"]
            print(f"✅ تم جلب Chat ID تلقائياً: {MY_CHAT_ID}")
            return True
        else:
            print("⚠️ لا توجد رسائل بعد. أرسل /start للبوت ثم أعد التشغيل.")
            return False
    except Exception as e:
        print(f"❌ خطأ في جلب Chat ID: {e}")
        return False

def get_price_qos(symbol):
    """جلب السعر من QOS API"""
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
        print(f"⚠️ خطأ في جلب سعر {symbol}: {e}")
        return None

def get_kline_data(symbol, interval="5min", limit=50):
    """جلب بيانات الشموع"""
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
        print(f"⚠️ خطأ في بيانات الشموع لـ {symbol}: {e}")
        return []

def calculate_ema(prices, period=12):
    """حساب EMA"""
    if len(prices) < period:
        return prices[-1] if prices else 0
    multiplier = 2 / (period + 1)
    ema = prices[0]
    for price in prices[1:]:
        ema = (price - ema) * multiplier + ema
    return ema

def calculate_rsi(prices, period=14):
    """حساب RSI"""
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
    """توليد الإشارة"""
    if not kline_data or len(kline_data) < 20:
        return "انتظار", 0, "بيانات غير كافية"
    
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
        return "انتظار", 0, f"بيانات غير كافية ({len(closes)} شمعة)"
    
    ema_fast = calculate_ema(closes, 9)
    ema_slow = calculate_ema(closes, 21)
    rsi = calculate_rsi(closes, 14)
    
    signal = "انتظار"
    confidence = 50
    reasons = []
    
    if ema_fast > ema_slow and closes[-2] <= ema_slow:
        signal = "شراء 🟢"
        confidence = 70
        reasons.append("تقاطع EMA صاعد")
    elif ema_fast < ema_slow and closes[-2] >= ema_slow:
        signal = "بيع 🔴"
        confidence = 70
        reasons.append("تقاطع EMA هابط")
    
    if signal == "انتظار":
        if rsi < 30 and ema_fast > ema_slow:
            signal = "شراء 🟢"
            confidence = 65
            reasons.append(f"RSI {rsi:.1f} مع اتجاه صاعد")
        elif rsi > 70 and ema_fast < ema_slow:
            signal = "بيع 🔴"
            confidence = 65
            reasons.append(f"RSI {rsi:.1f} مع اتجاه هابط")
    
    if signal == "انتظار":
        if rsi < 25:
            signal = "شراء 🟢"
            confidence = 55
            reasons.append(f"RSI في ذروة بيع ({rsi:.1f})")
        elif rsi > 80:
            signal = "بيع 🔴"
            confidence = 55
            reasons.append(f"RSI في ذروة شراء ({rsi:.1f})")
    
    if signal == "انتظار":
        reasons.append(f"RSI {rsi:.1f} في منطقة محايدة")
    
    return signal, confidence, "\n• ".join(reasons)

async def send_signal():
    """إرسال الإشارة"""
    global MY_CHAT_ID
    if not MY_CHAT_ID:
        print("⚠️ لا يمكن الإرسال: لم يتم جلب Chat ID بعد")
        return
    
    for symbol, name in SYMBOLS.items():
        price = get_price_qos(symbol)
        if not price:
            continue
        
        kline_data = get_kline_data(symbol)
        signal, confidence, reason = generate_signal(name, kline_data)
        
        icon = "🟢💰" if "شراء" in signal else "🔴📉" if "بيع" in signal else "⏳📊"
        stars = "⭐" * min(5, confidence // 15)
        
        message = f"""
{icon} *{name}* {icon}

💰 *السعر الحالي:* `${price:.2f}`

🎯 *الإشارة:* *{signal}*
📈 *نسبة الثقة:* {confidence}% {stars}

📝 *التحليل:*
• {reason}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
⚠️ إشارة تحليل فني فقط - قرارك مسؤوليتك
"""
        try:
            await bot.send_message(chat_id=MY_CHAT_ID, text=message, parse_mode='Markdown')
            print(f"✅ تم إرسال إشارة {name}")
        except Exception as e:
            print(f"❌ فشل إرسال إشارة {name}: {e}")
        
        await asyncio.sleep(3)

async def main():
    """الحلقة الرئيسية"""
    print("🚀 بوت الإشارات شغال...")
    print("📡 جاري جلب Chat ID تلقائياً...")
    
    # جلب Chat ID تلقائياً
    if not get_chat_id_automatically():
        print("❌ لم يتم العثور على Chat ID.")
        print("💡 أرسل /start للبوت على تليجرام ثم أعد تشغيل السكربت.")
        return
    
    print(f"📊 متابع: {', '.join(SYMBOLS.values())}")
    print("-" * 50)
    
    while True:
        try:
            await send_signal()
            print(f"⏳ انتظار 5 دقائق... ({datetime.now().strftime('%H:%M:%S')})")
            await asyncio.sleep(300) # 5 دقائق
        except Exception as e:
            print(f"⚠️ خطأ: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main()
