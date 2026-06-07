import requests
import time
import asyncio
import json
from datetime import datetime
from telegram import Bot, ParseMode

# ========== إعداداتك الشخصية (عدليها قبل التشغيل) ==========
TELEGRAM_TOKEN = "8932925426:AAHh3RWwa4ZwkVBJQeoMhYGFmO5nEgWMJpw"
CHAT_ID = "ضع_معرفك_هنا"
# ===========================================================

bot = Bot(token=TELEGRAM_TOKEN)

# الأسواق اللي هنتابعها
SYMBOLS = {
    "XAUUSD": "الذهب (XAU/USD)",
    "XAGUSD": "الفضة (XAG/USD)"
}

# BASE URL لـ QOS API
QOS_BASE_URL = "https://quote.qos.hk"

def get_price_qos(symbol):
    """جلب سعر الذهب/الفضة من QOS API"""
    try:
        # QOS API تستخدم رمز XAUUSD و XAGUSD
        url = f"{QOS_BASE_URL}/api/quote?symbol={symbol}"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # حسب الـ API documentation، السعر في حقل price أو last
            price = data.get('price') or data.get('last') or data.get('c')
            if price:
                return float(price)
        
        # لو فشل، نجرب endpoint تاني
        url2 = f"{QOS_BASE_URL}/quote/{symbol}"
        response2 = requests.get(url2, headers=headers, timeout=10)
        if response2.status_code == 200:
            data2 = response2.json()
            price = data2.get('price') or data2.get('last')
            if price:
                return float(price)
        
        return None
        
    except Exception as e:
        print(f"⚠️ خطأ في جلب سعر {symbol}: {e}")
        return None

def get_kline_data(symbol, interval="1min", limit=30):
    """جلب بيانات الشموع (K-line) من QOS API"""
    try:
        url = f"{QOS_BASE_URL}/api/kline"
        params = {
            "symbol": symbol,
            "interval": interval, # 1min, 5min, 15min, 1hour, 1day
            "limit": limit
        }
        headers = {"User-Agent": "Mozilla/5.0"}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # حسب الـ API، البيانات قد تكون في data.items أو data['data']
            if 'data' in data:
                return data['data']
            elif isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # بعض الأحيان البيانات تكون في list من الـ klines
                for key in ['klines', 'items', 'list']:
                    if key in data:
                        return data[key]
                return [data] # لو كانت البيانات مفردة
        
        return []
        
    except Exception as e:
        print(f"⚠️ خطأ في جلب بيانات الشموع لـ {symbol}: {e}")
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
    
    gains = []
    losses = []
    
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
    rsi = 100 - (100 / (1 + rs))
    return rsi

def generate_signal(symbol_name, current_price, kline_data):
    """توليد إشارة Buy/Sell بناءً على التحليل"""
    if not kline_data or len(kline_data) < 20:
        return "انتظار", 0, "بيانات غير كافية للتحليل"
    
    # استخراج أسعار الإغلاق من بيانات الشموع
    closes = []
    for item in kline_data:
        # حسب تنسيق QOS API، السعر في حقل close
        if isinstance(item, dict):
            close = item.get('close') or item.get('c') or item.get('price')
        elif isinstance(item, (list, tuple)) and len(item) >= 5:
            # بعض الأحيان البيانات تكون [time, open, high, low, close, volume]
            close = item[4]
        else:
            continue
        
        if close:
            try:
                closes.append(float(close))
            except:
                pass
    
    if len(closes) < 15:
        return "انتظار", 0, f"بيانات غير كافية (متوفر {len(closes)} شمعة فقط)"
    
    # حساب المؤشرات
    ema_fast = calculate_ema(closes, 9)
    ema_slow = calculate_ema(closes, 21)
    rsi = calculate_rsi(closes, 14)
    last_price = closes[-1]
    
    # توليد الإشارة
    signal = "انتظار"
    confidence = 50
    reasons = []
    
    # 1. تقاطع EMA
    if ema_fast > ema_slow and closes[-2] <= ema_slow:
        signal = "شراء 🟢"
        confidence = 70
        reasons.append("تقاطع EMA صاعد (Golden Cross)")
    elif ema_fast < ema_slow and closes[-2] >= ema_slow:
        signal = "بيع 🔴"
        confidence = 70
        reasons.append("تقاطع EMA هابط (Death Cross)")
    
    # 2. RSI مع تقاطع EMA
    if signal == "انتظار":
        if rsi < 30 and ema_fast > ema_slow:
            signal = "شراء 🟢"
            confidence = 65
            reasons.append(f"RSI في منطقة ذروة البيع ({rsi:.1f}) مع اتجاه صاعد")
        elif rsi > 70 and ema_fast < ema_slow:
            signal = "بيع 🔴"
            confidence = 65
            reasons.append(f"RSI في منطقة ذروة الشراء ({rsi:.1f}) مع اتجاه هابط")
    
    # 3. RSI فقط
    if signal == "انتظار":
        if rsi < 25:
            signal = "شراء 🟢"
            confidence = 55
            reasons.append(f"RSI في ذروة بيع شديدة ({rsi:.1f})")
        elif rsi > 80:
            signal = "بيع 🔴"
            confidence = 55
            reasons.append(f"RSI في ذروة شراء شديدة ({rsi:.1f})")
    
    if signal == "انتظار":
        reasons.append(f"RSI {rsi:.1f} في المنطقة المحايدة")
        reasons.append(f"EMA Fast {ema_fast:.2f} | Slow {ema_slow:.2f}")
    
    reason_text = "\n• ".join(reasons)
    return signal, confidence, reason_text

async def send_signal():
    """إرسال الإشارة إلى تليجرام"""
    for symbol, name in SYMBOLS.items():
        print(f"🔄 جاري تحليل {name}...")
        
        # 1. جلب السعر الحالي
        price = get_price_qos(symbol)
        if not price:
            await bot.send_message(
                chat_id=CHAT_ID,
                text=f"⚠️ *{name}* - تعذر جلب السعر من QOS API",
                parse_mode='Markdown'
            )
            continue
        
        # 2. جلب بيانات الشموع
        kline_data = get_kline_data(symbol, interval="5min", limit=50)
        
        # 3. توليد الإشارة
        signal, confidence, reason = generate_signal(name, price, kline_data)
        
        # 4. تنسيق الرسالة
        if "شراء" in signal:
            icon = "🟢💰"
        elif "بيع" in signal:
            icon = "🔴📉"
        else:
            icon = "⏳📊"
        
        confidence_stars = "⭐" * min(5, confidence // 15)
        if confidence < 40:
            confidence_stars = "✨" + confidence_stars
        
        message = f"""
{icon} *{name}* {icon}

💰 *السعر الحالي:* `${price:.2f}`

🎯 *الإشارة:* *{signal}*
📈 *نسبة الثقة:* {confidence}% {confidence_stars}

📝 *التحليل:*
• {reason}

⏰ *آخر تحديث:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
⚠️ هذه إشارة تحليل فني فقط
📌 قرار البيع والشراء مسؤوليتك الشخصية
"""
        
        try:
            await bot.send_message(
                chat_id=CHAT_ID,
                text=message,
                parse_mode='Markdown'
            )
            print(f"✅ تم إرسال إشارة {name}: {signal}")
        except Exception as e:
            print(f"❌ فشل إرسال إشارة {name}: {e}")
        
        # انتظار بين الرموز عشان ما نضربش Rate Limit
        await asyncio.sleep(3)

async def main():
    """الحلقة الرئيسية"""
    print("""
╔════════════════════════════════════════════════╗
║ 🥇 بوت إشارات الذهب والفضة - QOS API ║
╚════════════════════════════════════════════════╝
    """)
    print("✅ البوت شغال...")
    print(f"📊 متابع: {', '.join(SYMBOLS.values())}")
    print("📡 مصدر البيانات: QOS Quote API")
    print("-" * 50)
    
    while True:
        try:
            await send_signal()
            
            # انتظر 3 دقائق قبل التحليل التالي
            wait_minutes = 3
            print(f"⏳ انتظار {wait_minutes} دقائق حتى التحليل التالي...")
            await asyncio.sleep(wait_minutes * 60)
            
        except Exception as e:
            print(f"⚠️ خطأ في الحلقة الرئيسية: {e}")
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
