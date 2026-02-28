import telebot
import requests
import os
from telebot import types

# ---------- CONFIG ----------
BOT_TOKEN = os.environ.get('8048502116:AAEj_2vWIok8BjJ5P8d27NlYUg_Rn0VseJ4')
API_KEY = os.environ.get("YOUR-PASSWORD")
CHANNEL_USERNAME = "@anubis_backup"  # Channel ka username (with @)
CHANNEL_LINK = "https://t.me/anubis_backup"
API_URL = "https://database-sigma-nine.vercel.app/number/{}?api_key={}"
# ----------------------------

bot = telebot.TeleBot(BOT_TOKEN)

# ---------- MEMBERSHIP CHECK FUNCTION ----------
def is_member(user_id):
    """Check if user is member of channel"""
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Membership check error: {e}")
        return False  # Agar error aaya to access deny karo

# ---------- FORCE JOIN DECORATOR ----------
def force_join(func):
    """Decorator to force channel join before command"""
    def wrapper(message):
        user_id = message.from_user.id
        if not is_member(user_id):
            # Channel join karne ka button bhejo
            markup = types.InlineKeyboardMarkup()
            btn = types.InlineKeyboardButton("🔔 Join Channel", url=CHANNEL_LINK)
            markup.add(btn)
            bot.reply_to(
                message,
                f"❌ *Access Denied!*\n\n"
                f"Bot use karne ke liye pehle hamara channel join karo:\n"
                f"{CHANNEL_LINK}\n\n"
                f"Join karne ke baad /num dobara bhejo.",
                parse_mode="Markdown",
                reply_markup=markup
            )
            return
        return func(message)
    return wrapper

# ---------- COMMAND HANDLERS ----------
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.reply_to(
        message,
        f"👋 *Welcome!*\n\n"
        f"Bot use karne ke liye pehle channel join karo:\n"
        f"{CHANNEL_LINK}\n\n"
        f"Phir /num <mobile> se data prapt karo.\n"
        f"Example: `/num 8840246357`",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['num'])
@force_join  # Force join check
def num_command(message):
    try:
        # Extract number
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Usage: /num <mobile_number>\nExample: `/num 8840246357`", parse_mode="Markdown")
            return
        
        number = parts[1].strip()
        if not number.isdigit():
            bot.reply_to(message, "❌ Sirf digits daal bhai.")
            return
        
        # Fetch data from API
        url = API_URL.format(number, API_KEY)
        r = requests.get(url, timeout=10)
        data = r.json()
        
        # Check response
        if data.get("Status") == "success" and data.get("Count", 0) > 0:
            results = data["Results"]
            total = len(results)
            
            # Prepare output
            output = f"📱 *Number:* {number}\n"
            output += f"✅ *Total Records:* {total}\n\n"
            
            for idx, record in enumerate(results, 1):
                output += f"━━━━━━━━━━━━━━━\n"
                output += f"*Record #{idx}*\n"
                output += f"👤 *Name:* {record.get('name', 'N/A')}\n"
                output += f"👨 *Father:* {record.get('fname', 'N/A')}\n"
                output += f"🏠 *Address:* {record.get('address', 'N/A')}\n"
                output += f"📞 *Mobile:* {record.get('mobile', 'N/A')}\n"
                output += f"📞 *Alt:* {record.get('alt', 'N/A')}\n"
                output += f"📡 *Circle:* {record.get('circle', 'N/A')}\n"
                output += f"🆔 *ID:* {record.get('id', 'N/A')}\n"
                output += f"📧 *Email:* {record.get('email', 'N/A')}\n"
                output += f"━━━━━━━━━━━━━━━\n\n"
            
            # Send in chunks if too long
            if len(output) > 4000:
                for x in range(0, len(output), 4000):
                    bot.reply_to(message, output[x:x+4000], parse_mode="Markdown")
            else:
                bot.reply_to(message, output, parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ Number nahi mila ya API error.")
            
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {str(e)}")

# ---------- START BOT ----------
print("Bot chal raha hai...")
bot.polling(none_stop=True)