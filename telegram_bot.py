from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import requests
import urllib.parse

# ============================================
# تنظیمات اصلی
# ============================================
BOT_TOKEN = "8698852401:AAEZRnEamEE4tlZwAigg5qflJKaJ9bpQnEY"

# مدل AI (openai, mistral, llama, qwen, deepseek)
AI_MODEL = "openai"

# حافظه مکالمه
conversation_history = {}
MAX_HISTORY = 10

# ============================================
# تابع AI با Pollinations
# ============================================
def get_ai_response(user_id: int, user_message: str) -> str:
    try:
        if user_id not in conversation_history:
            conversation_history[user_id] = []
        
        conversation_history[user_id].append(f"کاربر: {user_message}")
        
        if len(conversation_history[user_id]) > MAX_HISTORY * 2:
            conversation_history[user_id] = conversation_history[user_id][-(MAX_HISTORY * 2):]
        
        full_prompt = "تو یک دستیار هوشمند فارسی‌زبان هستی. پاسخ‌هایت را به فارسی، کوتاه، مفید و دوستانه بده. از ایموجی استفاده کن.\n\n" + "\n".join(conversation_history[user_id])
        
        encoded_prompt = urllib.parse.quote(full_prompt)
        url = f"https://text.pollinations.ai/{encoded_prompt}?model={AI_MODEL}"
        response = requests.get(url, timeout=60)
        
        if response.status_code == 200:
            ai_response = response.text.strip()
            conversation_history[user_id].append(f"دستیار: {ai_response}")
            return ai_response
        else:
            return f"❌ خطا در ارتباط با هوش مصنوعی (کد: {response.status_code})"
    
    except requests.exceptions.Timeout:
        return "❌ زمان پاسخ‌دهی طولانی شد. دوباره امتحان کن."
    except Exception as e:
        return f"❌ خطا: {str(e)}"

# ============================================
# دستور /start
# ============================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💬 گفتگوی آزاد", callback_data='chat')],
        [InlineKeyboardButton("🌐 ترجمه متن", callback_data='translate')],
        [InlineKeyboardButton("📝 خلاصه‌سازی", callback_data='summary')],
        [InlineKeyboardButton("💻 کمک کدنویسی", callback_data='code')],
        [InlineKeyboardButton("🎨 ایده‌پردازی", callback_data='idea')],
        [InlineKeyboardButton("🗑️ پاک کردن حافظه", callback_data='clear')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🤖 *به دستیار هوشمند سینا خوش آمدید!*\n\n"
        "🧠 من یه هوش مصنوعی قدرتمند هستم که می‌تونم:\n\n"
        "💬 باهات گفتگو کنم\n"
        "🌐 متن ترجمه کنم\n"
        "📝 متن‌های طولانی رو خلاصه کنم\n"
        "💻 در کدنویسی کمکت کنم\n"
        "🎨 ایده‌های خلاقانه بدم\n\n"
        "✨ یکی از گزینه‌ها رو انتخاب کن یا مستقیم سوالت رو بپرس!",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ============================================
# دکمه‌ها
# ============================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'chat':
        await query.edit_message_text("💬 *حالت گفتگوی آزاد*\n\nهر سوالی داری بپرس!", parse_mode='Markdown')
        context.user_data['mode'] = 'chat'
    
    elif query.data == 'translate':
        await query.edit_message_text("🌐 *حالت ترجمه*\n\nمتنت رو بفرست تا ترجمه کنم.", parse_mode='Markdown')
        context.user_data['mode'] = 'translate'
    
    elif query.data == 'summary':
        await query.edit_message_text("📝 *حالت خلاصه‌سازی*\n\nمتن طولانی رو بفرست.", parse_mode='Markdown')
        context.user_data['mode'] = 'summary'
    
    elif query.data == 'code':
        await query.edit_message_text("💻 *حالت کدنویسی*\n\nسوالت رو بپرس.", parse_mode='Markdown')
        context.user_data['mode'] = 'code'
    
    elif query.data == 'idea':
        await query.edit_message_text("🎨 *حالت ایده‌پردازی*\n\nموضوع رو بگو تا ایده بدم.", parse_mode='Markdown')
        context.user_data['mode'] = 'idea'
    
    elif query.data == 'clear':
        user_id = query.from_user.id
        if user_id in conversation_history:
            conversation_history[user_id] = []
        await query.edit_message_text("✅ *حافظه پاک شد!*", parse_mode='Markdown')

# ============================================
# پیام‌های متنی
# ============================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_message = update.message.text
    mode = context.user_data.get('mode', 'chat')
    
    if mode == 'translate':
        prompt = f"این متن رو ترجمه کن. اگه فارسیه به انگلیسی، اگه انگلیسیه به فارسی. فقط ترجمه:\n\n{user_message}"
    elif mode == 'summary':
        prompt = f"این متن رو خلاصه کن (۲۰٪ متن اصلی). نکات کلیدی با بولت:\n\n{user_message}"
    elif mode == 'code':
        prompt = f"در مورد این سوال کدنویسی کمک کن. کد کامل با توضیح فارسی:\n\n{user_message}"
    elif mode == 'idea':
        prompt = f"۵ ایده خلاقانه بده برای: {user_message}. هر ایده با یه خط توضیح."
    else:
        prompt = user_message
    
    response = get_ai_response(user_id, prompt)
    
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            await update.message.reply_text(response[i:i+4000])
    else:
        await update.message.reply_text(response)

# ============================================
# اجرای اصلی
# ============================================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 چت‌بات هوشمند در حال اجراست...")
    print("✅ ربات: @SinaSmartAI_bot")
    print("برای توقف: Ctrl + C")
    app.run_polling()

if __name__ == '__main__':
    main()