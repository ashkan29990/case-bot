from flask import Flask
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import json
import time

app = Flask(__name__)

TOKEN = "8844006048:AAEw1FTdziMIrcWjUKu77YN2CjHvpr9JopQ"
bot = telebot.TeleBot(TOKEN)

# ------------------------- API: پرونده‌ها -------------------------
def search_cases(query, page=1):
    url = "https://edaalat.org/request/cases"
    params = {"q": query, "page": page}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

# ------------------------- START -------------------------
@bot.message_handler(commands=["start"])
def start(message):
    markup = InlineKeyboardMarkup(row_width=1)
    btn_case = InlineKeyboardButton("🔎 جستجوی پرونده", callback_data="search_case")
    markup.add(btn_case)
    
    bot.send_message(
        message.chat.id,
        "سلام 👋 به ربات استعلام سوء سابقه خوش اومدی!\n\n"
        "از دکمه زیر برای جستجو استفاده کن توجه داشته باش که به علت نقض حریم خصوصی نمیتوانیم اطلاعات کامل پرونده رو در اختیار شما قرار دهیم همچنان شما میتوانید با نام فرد مورد نظر یا موضوع پرونده اطلاعات را به دست بیاورید:",
        reply_markup=markup
    )

# ------------------------- بخش پرونده‌ها -------------------------
@bot.callback_query_handler(func=lambda call: call.data == "search_case")
def ask_query(call):
    bot.edit_message_text(
        "🔍 نام فرد مورد نظر یا موضوع پرونده را وارد کن:",
        call.message.chat.id,
        call.message.message_id
    )
    bot.register_next_step_handler(call.message, process_case)

def process_case(message):
    query = message.text.strip()
    if not query:
        bot.send_message(message.chat.id, "❌ لطفاً یک متن معتبر وارد کن.")
        return
    
    msg = bot.send_message(message.chat.id, "⏳ در حال جستجو...")
    try:
        data = search_cases(query)
        cases = data.get("cases", [])
        
        if not cases:
            bot.edit_message_text(
                "❌ هیچ پرونده‌ای با این عبارت پیدا نشد.",
                message.chat.id,
                msg.message_id
            )
            return
        
        # ذخیره در کش
        if not hasattr(bot, 'cases_cache'):
            bot.cases_cache = {}
        bot.cases_cache[query] = cases
        
        show_results(message.chat.id, msg.message_id, cases, query, page=1)
        
    except Exception as e:
        bot.edit_message_text(
            f"⚠️ خطا: {str(e)}",
            message.chat.id,
            msg.message_id
        )

def show_results(chat_id, msg_id, cases, query, page=1):
    per_page = 5
    total_pages = (len(cases) + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    page_cases = cases[start:end]
    
    text = f"📋 <b>نتایج جستجوی</b> «{query}»\n"
    text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"📊 {len(cases)} پرونده | صفحه {page} از {total_pages}\n\n"
    
    for idx, case in enumerate(page_cases, start=start+1):
        # گزینه 1: نمایش کامل JSON هر پرونده (فعلاً برای دیباگ)
        # اون لاینی که کامنته رو می‌تونی فعال کنی تا ببینی اصل داده چیه
        
        # گزینه 2: نمایش تمام فیلدهای موجود
        case_data = case.get("data", {})
        
        text += f"<b>{idx}.</b>\n"
        
        # نمایش همه کلیدهایی که مقدار دارند
        if case_data:
            for key, value in case_data.items():
                if value and str(value).strip():
                    # محدود کردن طول هر مقدار
                    value_str = str(value)[:60]
                    text += f"   • <b>{key}</b>: {value_str}\n"
        else:
            # اگر data خالی بود، خود case رو نمایش بده
            for key, value in case.items():
                if value and str(value).strip() and key != 'data':
                    value_str = str(value)[:60]
                    text += f"   • <b>{key}</b>: {value_str}\n"
        
        text += f"   ━━━━━━━━━━━━━━━━━━━━\n"
    
    # دکمه دیباگ برای دیدن JSON خام (می‌تونی بعداً حذف کنی)
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = []
    
    if page > 1:
        buttons.append(InlineKeyboardButton("◀️ قبلی", callback_data=f"page_{query}_{page-1}"))
    if page < total_pages:
        buttons.append(InlineKeyboardButton("بعدی ▶️", callback_data=f"page_{query}_{page+1}"))
    
    buttons.append(InlineKeyboardButton("🔄 جستجوی جدید", callback_data="search_case"))
    buttons.append(InlineKeyboardButton("🔧 دیباگ", callback_data=f"debug_{query}_{start}"))
    
    markup.add(*buttons)
    
    try:
        bot.edit_message_text(
            text,
            chat_id,
            msg_id,
            parse_mode="HTML",
            reply_markup=markup
        )
    except:
        bot.send_message(
            chat_id,
            text,
            parse_mode="HTML",
            reply_markup=markup
        )

# ------------------------- دیباگ: نمایش JSON خام -------------------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("debug_"))
def debug_json(call):
    _, query, start = call.data.split("_")
    start = int(start)
    
    cases = getattr(bot, 'cases_cache', {}).get(query, [])
    if not cases or start >= len(cases):
        bot.answer_callback_query(call.id, "خطا")
        return
    
    case = cases[start]
    
    # نمایش JSON خام با فرمت زیبا
    json_text = json.dumps(case, indent=2, ensure_ascii=False)
    
    # تلگرام محدودیت 4096 کاراکتر داره
    if len(json_text) > 4000:
        json_text = json_text[:4000] + "\n... (ادامه حذف شد)"
    
    bot.send_message(
        call.message.chat.id,
        f"<pre>{json_text}</pre>",
        parse_mode="HTML"
    )
    bot.answer_callback_query(call.id)

# ------------------------- صفحه‌بندی -------------------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("page_"))
def paginate(call):
    _, query, page = call.data.split("_", 2)
    page = int(page)
    
    cases = getattr(bot, 'cases_cache', {}).get(query, [])
    if not cases:
        bot.answer_callback_query(call.id, "خطا")
        return
    
    per_page = 5
    total_pages = (len(cases) + per_page - 1) // per_page
    
    if page < 1 or page > total_pages:
        bot.answer_callback_query(call.id, "صفحه نامعتبر")
        return
    
    show_results(call.message.chat.id, call.message.message_id, cases, query, page)
    bot.answer_callback_query(call.id)

# ------------------------- اجرای ربات در ترد جداگانه -------------------------
def run_bot():
    print("🤖 BOT RUNNING...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"خطا در ربات: {e}")
            time.sleep(5)

@app.route('/')
def home():
    return "ربات فعال است"

@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    # اجرای ربات در ترد جداگانه
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # اجرای وب سرور
    app.run(host='0.0.0.0', port=8080)
