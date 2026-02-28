import logging
import asyncio
import json
import time
from functools import wraps
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, filters, MessageHandler
from telegram.constants import ParseMode
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ------------------- CONFIG -------------------
BOT_TOKEN = "8048502116:AAEj_2vWIok8BjJ5P8d27NlYUg_Rn0VseJ4"  # Apna token daal
CHANNEL_USERNAME = "@anubis_backup"  # Channel ka username (with @)
CHANNEL_LINK = "https://t.me/anubis_backup"  # Channel link
API_URL_TEMPLATE = "https://usesir.gt.tc/illfuvkyourpussy?sex={}"
# ------------------------------------------------

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ------------------- SELENIUM SETUP -------------------
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# Global driver with initialization
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver_lock = asyncio.Lock()

def selenium_fetch(url):
    """Selenium se data fetch karo"""
    global driver
    try:
        driver.get(url)
        time.sleep(5)  # Wait for JS execution
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        pre_tag = soup.find('pre')
        if pre_tag:
            data = json.loads(pre_tag.text)
            if data.get('success') and data.get('result'):
                return data['result']
        return None
    except Exception as e:
        logger.error(f"Selenium error: {e}")
        return None

async def fetch_data_from_api(number: str):
    """Async wrapper for selenium fetch"""
    url = API_URL_TEMPLATE.format(number)
    loop = asyncio.get_event_loop()
    async with driver_lock:  # Ensure only one request at a time
        return await loop.run_in_executor(None, selenium_fetch, url)

# ------------------- MEMBERSHIP CHECK DECORATOR -------------------
def force_join_channel(func):
    """Decorator to check channel membership before command execution"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not user:
            return
        
        try:
            # Check if user is member
            member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user.id)
            if member.status in ['left', 'kicked']:
                # Not a member
                keyboard = [[InlineKeyboardButton("🔔 Join Channel", url=CHANNEL_LINK)]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"❌ <b>Access Denied!</b>\n\n"
                    f"Bot use karne ke liye pehle hamara channel join karo:\n"
                    f"{CHANNEL_LINK}\n\n"
                    f"Join karne ke baad /num command dobara bhejo.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
                return
            else:
                # Member, proceed to command
                return await func(update, context, *args, **kwargs)
        except Exception as e:
            logger.error(f"Membership check error: {e}")
            # Agar error aaye to bhi allow karo (bot admin nahi ho sakta)
            return await func(update, context, *args, **kwargs)
    
    return wrapper

# ------------------- COMMAND HANDLERS -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    await update.message.reply_text(
        f"👋 <b>Welcome!</b>\n\n"
        f"Bot use karne ke liye pehle hamare channel ko join karo:\n"
        f"{CHANNEL_LINK}\n\n"
        f"Phir /num command se data prapt karo.\n\n"
        f"<b>Usage:</b> <code>/num 9741720881</code>\n"
        f"<b>Example:</b> <code>/num 9741720881</code>",
        parse_mode=ParseMode.HTML
    )

@force_join_channel
async def num_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/num command handler with force join"""
    user = update.effective_user
    chat = update.effective_chat
    
    # Check if number provided
    if not context.args:
        await update.message.reply_text(
            "❌ <b>Wrong Usage!</b>\n\n"
            "Sahi format: <code>/num &lt;mobile_number&gt;</code>\n"
            "Example: <code>/num 9741720881</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    number = context.args[0].strip()
    if not number.isdigit():
        await update.message.reply_text(
            "❌ Sirf digits daal bhai.\n"
            "Example: <code>9741720881</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Let user know we're fetching
    status_msg = await update.message.reply_text(
        "🔍 <b> Getting Data...</b>\n"
        "⏱️ Please Wait For Details",
        parse_mode=ParseMode.HTML
    )
    
    # Fetch data
    result_list = await fetch_data_from_api(number)
    
    if not result_list:
        await status_msg.edit_text(
            "❌ <b>Data Not Found</b>\n\n"
            "The number Is incorrect or Server down.",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Format response for multiple records
    output = f"📱 <b>Number:</b> <code>{number}</code>\n"
    output += f"✅ <b>Total Records:</b> {len(result_list)}\n\n"
    
    for idx, record in enumerate(result_list, 1):
        output += f"━━━━━━━━━━━━━━━\n"
        output += f"<b>Record #{idx}</b>\n"
        output += f"👤 <b>Name:</b> {record.get('name', 'N/A')}\n"
        output += f"👨 <b>Father:</b> {record.get('father_name', 'N/A')}\n"
        
        address = record.get('address', 'N/A').replace('!', ', ')
        output += f"🏠 <b>Address:</b> {address}\n"
        
        circle = record.get('circle/sim', 'N/A')
        output += f"📡 <b>Circle/Sim:</b> {circle}\n"
        output += f"📞 <b>Mobile:</b> {record.get('mobile', 'N/A')}\n"
        
        alt = record.get('alternative_mobile', 'N/A')
        if alt and alt != 'N/A':
            output += f"📞 <b>Alt Mobile:</b> {alt}\n"
        
        aadhar = record.get('aadhar_number', 'N/A')
        if aadhar and aadhar != 'N/A':
            output += f"🆔 <b>Aadhaar:</b> {aadhar}\n"
        
        email = record.get('email', 'N/A')
        if email and email != 'N/A':
            output += f"📧 <b>Email:</b> {email}\n"
        
        output += f"━━━━━━━━━━━━━━━\n\n"
    
    # Add footer
    output += f"🔍 <b>Searched by:</b> {user.first_name}\n"
    output += f"🤖 <b>Bot:</b> @{context.bot.username}"
    
    # Send in chunks if too long
    if len(output) > 4096:
        # Split into multiple messages
        for x in range(0, len(output), 4096):
            await update.message.reply_text(output[x:x+4096], parse_mode=ParseMode.HTML)
    else:
        await status_msg.edit_text(output, parse_mode=ParseMode.HTML)

# ------------------- GROUP MESSAGE HANDLER -------------------
async def group_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages in groups - ignore non-command messages"""
    # Do nothing for normal messages, only commands work
    pass

# ------------------- MAIN -------------------
async def post_init(application: Application):
    """Set bot commands after initialization"""
    commands = [
        BotCommand("start", "Bot ko start karo"),
        BotCommand("num", "Number se data prapt karo (e.g., /num 9741720881)"),
    ]
    await application.bot.set_my_commands(commands)

def main():
    """Main function"""
    # Create application
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("num", num_command))
    
    # Ignore non-command messages in groups
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, group_message_handler))
    
    # Error handler
    async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Update {update} caused error {context.error}")
        try:
            if update and update.message:
                await update.message.reply_text(
                    "❌ <b>Internal Error!</b>\n"
                    "Kuch technical problem hui hai. Dobara try karo.",
                    parse_mode=ParseMode.HTML
                )
        except:
            pass
    
    app.add_error_handler(error_handler)
    
    # Cleanup on exit
    import atexit
    def cleanup():
        driver.quit()
    atexit.register(cleanup)
    
    # Start bot
    logger.info("🤖 Bot starting...")
    print("🤖 Bot chal raha hai...")
    app.run_polling()

if __name__ == "__main__":
    main()