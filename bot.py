import os
import sys

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import logging
import io
import re
from datetime import datetime
import time
import uuid
import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CopyTextButton,
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChat,
    MenuButtonCommands
)

import config
import database
import authenticator
import name_generator
import qr_scanner
import user_agents
import stylish_fonts
import fb_tools

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Render Health Check Server (to bind $PORT for 24/7 Render Web Service)
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class RenderHealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Prime Multi-Tool Bot is Live and Healthy on Render!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

    def log_message(self, format, *args):
        pass

def start_render_health_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        server = HTTPServer(("0.0.0.0", port), RenderHealthHandler)
        logger.info(f"Render Health Server listening on 0.0.0.0:{port}")
        server.serve_forever()
    except Exception as e:
        logger.warning(f"Health server failed on port {port}: {e}")

# Start health check server immediately at import time so Render's port detection never times out
health_thread = threading.Thread(target=start_render_health_server, daemon=True)
health_thread.start()

# Initialize database
database.init_db()

# Telegram Bot Token validation
TOKEN = (config.BOT_TOKEN or "").strip()
is_token_configured = bool(TOKEN and ":" in TOKEN and TOKEN != "YOUR_BOT_TOKEN_HERE")

if is_token_configured:
    bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
else:
    # Dummy placeholder token to prevent telebot validation crash during import
    bot = telebot.TeleBot("123456789:AAPlaceholderTokenForRenderBootstrapping", parse_mode="HTML")

# In-memory user states and cache
user_states = {}
user_cache_storage = {}


# ==================== REPLY KEYBOARDS (95% OF UI) ====================

def get_main_reply_keyboard():
    """Builds the main menu ReplyKeyboardMarkup with clean styled buttons."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_fake = types.KeyboardButton("Fake Name")
    btn_2fa = types.KeyboardButton("Get 2FA")
    btn_fblite = types.KeyboardButton("FB Lite UID")
    btn_font = types.KeyboardButton("Stylish Font")
    btn_ua = types.KeyboardButton("User-Agent")
    btn_history = types.KeyboardButton("History")
    
    markup.add(btn_fake, btn_2fa)
    markup.add(btn_fblite, btn_font)
    markup.add(btn_ua, btn_history)
    return markup


def get_fake_name_reply_keyboard():
    """Reply Keyboard for Fake Name actions."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("Next Name"), types.KeyboardButton("Random"))
    markup.add(types.KeyboardButton("Male"), types.KeyboardButton("Female"))
    markup.add(types.KeyboardButton("Back to Main Menu"))
    return markup


def get_2fa_reply_keyboard():
    """Reply Keyboard for 2FA actions."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("Refresh 2FA"), types.KeyboardButton("Get 2FA"))
    markup.add(types.KeyboardButton("Back to Main Menu"))
    return markup


def get_fb_lite_reply_keyboard():
    """Reply Keyboard for FB Lite UID actions."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("Check Another UID"))
    markup.add(types.KeyboardButton("Back to Main Menu"))
    return markup


def get_font_reply_keyboard():
    """Reply Keyboard for Stylish Font actions."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("Try Another Text"))
    markup.add(types.KeyboardButton("Back to Main Menu"))
    return markup


def get_user_agent_reply_keyboard():
    """Reply Keyboard for User-Agent actions."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("Random UA"), types.KeyboardButton("Next UA"))
    markup.add(types.KeyboardButton("iPhone"), types.KeyboardButton("Android"))
    markup.add(types.KeyboardButton("Windows"), types.KeyboardButton("Mac"))
    markup.add(types.KeyboardButton("Back to Main Menu"))
    return markup


def get_history_reply_keyboard():
    """Reply Keyboard for History actions."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("Refresh History"), types.KeyboardButton("Clear History"))
    markup.add(types.KeyboardButton("Clear Cache"), types.KeyboardButton("Back to Main Menu"))
    return markup


# ==================== MINIMAL INLINE KEYBOARDS (1-Click Copy / URL Only) ====================

def create_fake_name_markup(first_name, last_name, full_name):
    """Inline keyboard for Fake Name - 1-click native copy buttons only."""
    markup = InlineKeyboardMarkup(row_width=2)
    btn_copy_first = InlineKeyboardButton(text=f"First: {first_name}", copy_text=CopyTextButton(text=first_name))
    btn_copy_last = InlineKeyboardButton(text=f"Last: {last_name}", copy_text=CopyTextButton(text=last_name))
    markup.add(btn_copy_first, btn_copy_last)
    
    btn_copy_full = InlineKeyboardButton(text=f"Copy: {full_name}", copy_text=CopyTextButton(text=full_name))
    markup.add(btn_copy_full)
    return markup


def create_2fa_output_markup(otp_code, secret_key=None):
    """Inline copy button for 2FA: ONLY the 6-digit code, NO emoji!"""
    markup = InlineKeyboardMarkup(row_width=1)
    # EXACT 6-digit code on the button, NO emoji! Clicking it copies the code!
    btn_otp = InlineKeyboardButton(text=f"{otp_code}", copy_text=CopyTextButton(text=otp_code))
    markup.add(btn_otp)
    return markup


def create_fb_lite_markup(uid):
    """Inline copy and profile open buttons for FB Lite."""
    markup = InlineKeyboardMarkup(row_width=2)
    btn_copy_uid = InlineKeyboardButton(text=f"Copy UID: {uid}", copy_text=CopyTextButton(text=uid))
    clean_url = f"https://facebook.com/{uid}"
    btn_open = InlineKeyboardButton(text="Open Clean Profile", url=clean_url)
    markup.add(btn_copy_uid, btn_open)
    return markup


def create_stylish_font_markup(best_font):
    """Inline copy button for stylish font."""
    markup = InlineKeyboardMarkup()
    btn_copy = InlineKeyboardButton(text="Copy Bold Font", copy_text=CopyTextButton(text=best_font))
    markup.add(btn_copy)
    return markup


def create_user_agent_markup(ua_string):
    """Inline copy button for User-Agent."""
    markup = InlineKeyboardMarkup()
    btn_copy = InlineKeyboardButton(text="Copy User-Agent", copy_text=CopyTextButton(text=ua_string))
    markup.add(btn_copy)
    return markup


# ==================== MESSAGE FORMATTERS ====================

def format_fake_name_message(identity):
    """Generates premium formatted USA identity text."""
    msg = (
        "🇺🇸 <b>USA IDENTITY GENERATOR</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Full Name:</b> <code>{identity['full_name']}</code>\n"
        f"🏷 <b>First Name:</b> <code>{identity['first_name']}</code>\n"
        f"🏷 <b>Last Name:</b> <code>{identity['last_name']}</code>\n"
        f"⚧ <b>Gender:</b> <code>{identity['gender']}</code>\n"
        f"🎂 <b>Age / DOB:</b> <code>{identity['age']} Yrs</code> (<code>{identity['dob']}</code>)\n"
        f"📧 <b>Email:</b> <code>{identity['email']}</code>\n"
        f"📱 <b>Phone:</b> <code>{identity['phone']}</code>\n"
        f"🏙 <b>City / State:</b> <code>{identity['city']}, {identity['state']}</code>\n"
        f"📮 <b>Zip Code:</b> <code>{identity['zip_code']}</code>\n"
        f"🏠 <b>Address:</b> <code>{identity['address']}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>💡 Click on First Name or Last Name to copy instantly!</i>"
    )
    return msg


def format_2fa_output(bulk_results, is_qr=False):
    """Formats 2FA result output with countdown progress bar."""
    if len(bulk_results) == 1 and bulk_results[0]["valid"]:
        r = bulk_results[0]
        bar_text = authenticator.get_progress_bar(r.get("remaining", 30))
        title = "📷 <b>QR CODE 2FA OTP</b>" if is_qr else "🔑 <b>2FA AUTHENTICATOR (LIVE OTP)</b>"
        lines = [
            title,
            "━━━━━━━━━━━━━━━━━━━━━━",
            f"🔢 <b>2FA Code:</b> <code>{r['otp']}</code>",
            f"   └ {bar_text}",
            "━━━━━━━━━━━━━━━━━━━━━━",
            f"🔐 <b>Secret Key:</b> <code>{r['secret']}</code>",
            f"⏱ <b>Generated At:</b> {r['time']}",
            "━━━━━━━━━━━━━━━━━━━━━━",
            "<i>💡 Tap on the 6-digit code above or click the button below to copy!</i>"
        ]
        return "\n".join(lines)

    title = "📷 <b>QR Code 2FA Output</b>" if is_qr else "🔑 <b>2FA Authenticator Output</b>"
    lines = [
        title,
        "━━━━━━━━━━━━━━━━━━━━━━"
    ]
    for r in bulk_results:
        if r["valid"]:
            bar_text = authenticator.get_progress_bar(r.get("remaining", 30))
            lines.append(f"<b>{r['index']}.</b> <code>{r['otp']}</code>  |  <code>{r['secret']}</code>")
            lines.append(f"   └ {bar_text}")
        else:
            lines.append(f"<b>{r['index']}.</b> ❌ <i>{r['raw']} (Error: {r['error']})</i>")
            
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("<i>💡 Tap any 6-digit code to copy instantly!</i>")
    return "\n".join(lines)


def format_history_message(user_name, records, total_count):
    """Formats 2FA history display."""
    now_str = datetime.now().strftime("%I:%M %p")
    header = (
        "📜 <b>2FA & ACTIVITY HISTORY</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>User:</b> {user_name}\n"
        f"💾 <b>Stored Cache Records:</b> <b>{total_count}</b> entries\n"
        f"⏱ <b>Cache Status:</b> 🟢 <b>Active & Synced</b> ({now_str})\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    if not records:
        body = (
            "📭 <b>No 2FA history found!</b>\n\n"
            "<i>Whenever you generate 2FA codes, your recent history will appear here.</i>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        return header + body
        
    body_items = ["<b>Recent 2FA Generations:</b>\n"]
    for idx, r in enumerate(records, 1):
        body_items.append(
            f"<b>{idx}.</b> 🔑 <code>{r['secret_key']}</code>\n"
            f"   └ 📋 Code: <code>{r['otp_code']}</code> | 📅 <i>{r['created_at']}</i>\n"
        )
        
    footer = (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>💡 Tap any code or secret to copy. Use buttons below to manage cache & history.</i>"
    )
    return header + "".join(body_items) + footer


def format_user_agent_message(ua_obj):
    """Formats Real Device User-Agent display."""
    msg = (
        "📱 <b>REAL DEVICE USER-AGENT</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷 <b>Device:</b> <b>{ua_obj['name']}</b>\n"
        f"💻 <b>OS:</b> <code>{ua_obj['os']}</code>\n"
        f"🌐 <b>Browser:</b> <code>{ua_obj['browser']}</code>\n"
        f"📁 <b>Category:</b> {ua_obj['category']}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<code>{ua_obj['ua']}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>💡 Tap on the code above or click the button below to copy!</i>"
    )
    return msg


def format_fb_lite_output(uid, live_status):
    """Formats FB Lite UID Extractor output."""
    clean_link = f"https://facebook.com/{uid}"
    msg = (
        "🆔 <b>FB UID & REALTIME STATUS CHECKER</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Numeric UID:</b> <code>{uid}</code>\n"
        f"🔗 <b>Clean Link:</b> <code>{clean_link}</code>\n"
        f"📡 <b>Account Status:</b> <b>{live_status}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>💡 Tap on the UID code above or click the button below to copy!</i>"
    )
    return msg


def format_stylish_font_output(original_text, styles):
    """Formats Stylish Font generator output with 12 styles."""
    lines = [
        "✍️ <b>STYLISH FONT RESULTS</b>",
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"🎯 <b>Original:</b> <code>{original_text}</code>",
        "━━━━━━━━━━━━━━━━━━━━━━"
    ]
    for idx, s in enumerate(styles, 1):
        lines.append(f"<b>{idx}. {s['name']}:</b>\n<code>{s['font']}</code>\n")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("<i>💡 Tap any style above to copy instantly!</i>")
    return "\n".join(lines)


# ==================== HANDLERS (REPLY KEYBOARDS & ACTIONS) ====================

@bot.message_handler(commands=["restart"])
def handle_restart(message):
    """Handles /restart command, resets session and shows fresh menu."""
    user_id = message.from_user.id
    user_states[user_id] = "idle"
    user_cache_storage.pop(user_id, None)
    
    restart_text = (
        "🔄 <b>Bot Restarted!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Go Ahead Buddy ❤️\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 <b>Select an option below:</b>"
    )
    bot.send_message(message.chat.id, restart_text, reply_markup=get_main_reply_keyboard())


@bot.message_handler(commands=["start", "menu"])
def send_welcome(message):
    """Handles /start command and displays main Reply Keyboard."""
    user_id = message.from_user.id
    user_states[user_id] = "idle"
    
    try:
        bot.set_chat_menu_button(chat_id=message.chat.id, menu_button=MenuButtonCommands(type="commands"))
        bot.set_my_commands([BotCommand("start", "Start / Restart Bot")], scope=BotCommandScopeChat(chat_id=message.chat.id))
    except Exception as e:
        logger.warning(f"Error setting menu button for chat {message.chat.id}: {e}")
    
    welcome_text = (
        "👋 <b>Welcome to Multi-Tool Bot!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Go Ahead Buddy ❤️\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 <b>Select an option below:</b>"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_reply_keyboard())


@bot.message_handler(func=lambda msg: msg.text and msg.text.strip().lower() in ["back to main menu", "main menu", "menu", "back", "/menu"])
def handle_back_to_main_menu(message):
    """Returns to the main menu with primary reply keyboard."""
    user_id = message.from_user.id
    user_states[user_id] = "idle"
    welcome_text = (
        "👋 <b>Welcome to Multi-Tool Bot!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Go Ahead Buddy ❤️\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 <b>Select an option below:</b>"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_reply_keyboard())


@bot.message_handler(func=lambda msg: msg.text and msg.text.strip().lower() in ["fake name", "fakename", "next name", "random", "male", "female"])
def handle_fake_name_command(message):
    """Generates and sends realistic USA Fake Name with Reply Keyboard controls."""
    user_id = message.from_user.id
    user_states[user_id] = "idle"
    cmd = message.text.strip().lower()
    
    gender = None
    if cmd == "male":
        gender = "Male"
    elif cmd == "female":
        gender = "Female"
    elif cmd in ["random", "next name"]:
        gender = None
        
    identity = name_generator.get_fake_name(gender=gender)
    database.update_user_cache(user_id, "fake_name", identity["full_name"])
    user_cache_storage[user_id] = identity
    
    text = format_fake_name_message(identity)
    markup = create_fake_name_markup(identity["first_name"], identity["last_name"], identity["full_name"])
    
    if cmd in ["fake name", "fakename"]:
        bot.send_message(message.chat.id, "👤 <b>Fake Name Options:</b>", reply_markup=get_fake_name_reply_keyboard())
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(func=lambda msg: msg.text and msg.text.strip().lower() in ["get 2fa", "2fa", "/2fa", "🔑 get 2fa"])
def handle_get_2fa_prompt(message):
    """Prompts user to send 2FA secret key or photo, sets 2FA Reply Keyboard."""
    user_id = message.from_user.id
    user_states[user_id] = "waiting_2fa"
    
    prompt_text = (
        "🔑 <b>2FA Authenticator (2FA.CN Mode)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Please send your <b>2FA Secret Key</b> or <b>QR Code Screenshot</b>:\n\n"
        "📝 <i>Example:</i> <code>30FC RA5M D2O2 PRU2</code>\n\n"
        "<i>(Supports text keys and 📷 QR code photos!)</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ <i>Tip: You can paste your 2FA key anytime directly!</i>"
    )
    bot.send_message(message.chat.id, prompt_text, reply_markup=get_2fa_reply_keyboard())


@bot.message_handler(func=lambda msg: msg.text and msg.text.strip().lower() in ["refresh 2fa", "refresh", "ref"])
def handle_refresh_2fa_button(message):
    """Instant 2FA refresh via Reply Keyboard button."""
    user_id = message.from_user.id
    secret = user_cache_storage.get(f"2fa_{user_id}") or user_cache_storage.get(user_id)
    if not secret:
        history = database.get_user_history(user_id, limit=1)
        if history:
            secret = history[0]["secret_key"]
            
    if not secret:
        bot.send_message(message.chat.id, "❌ <i>No 2FA key in memory. Please send your 2FA key or QR photo first.</i>", reply_markup=get_2fa_reply_keyboard())
        return
        
    cand, code, remaining, err = authenticator.sanitize_and_generate(secret)
    if code:
        res = [{
            "index": 1,
            "secret": cand,
            "otp": code,
            "remaining": remaining,
            "time": datetime.now().strftime("%I:%M %p"),
            "valid": True
        }]
        text = format_2fa_output(res)
        markup = create_2fa_output_markup(code, cand)
        bot.send_message(message.chat.id, text, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "❌ <i>Unable to generate 2FA code. Please re-send the key.</i>", reply_markup=get_2fa_reply_keyboard())


@bot.message_handler(func=lambda msg: msg.text and any(term in msg.text.lower() for term in ["fb lite", "lite uid", "check another uid", "extract another"]))
def handle_fb_lite_prompt(message):
    """Prompts user to send FB Lite Profile Link or direct numeric UID."""
    user_id = message.from_user.id
    user_states[user_id] = "waiting_fb_lite"
    
    prompt_text = (
        "🆔 <b>FB LITE UID & LIVE CHECKER</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Please send your <b>Numeric UID</b> or <b>Facebook Profile Link</b>:\n\n"
        "📝 <b>Supported Formats:</b>\n"
        "• <code>100084729104821</code> <i>(Direct Numeric UID)</i>\n"
        "• <code>https://www.facebook.com/profile.php?id=...</code>\n"
        "• <code>https://lite.facebook.com/...</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ <i>The bot will extract the UID and check in realtime whether the ID is 🟢 Live or 🔴 Dead / Checkpoint (Human)!</i>"
    )
    bot.send_message(message.chat.id, prompt_text, reply_markup=get_fb_lite_reply_keyboard())


@bot.message_handler(func=lambda msg: msg.text and any(term in msg.text.lower() for term in ["stylish font", "fonts", "try another text"]))
def handle_stylish_font_prompt(message):
    """Prompts user for text to convert to Stylish Fonts."""
    user_id = message.from_user.id
    user_states[user_id] = "waiting_font"
    
    prompt_text = (
        "✍️ <b>STYLISH FONT & BIO GENERATOR</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Please send the text you want to convert into stylish fonts:\n\n"
        "📝 <i>Example:</i> <code>Prime Tools</code> or <code>Your Name</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Generates 12+ aesthetic fonts with instant one-tap copy!</i>"
    )
    bot.send_message(message.chat.id, prompt_text, reply_markup=get_font_reply_keyboard())


@bot.message_handler(func=lambda msg: msg.text and any(term in msg.text.lower() for term in ["user-agent", "useragent", "ua", "random ua", "next ua", "iphone", "android", "windows", "mac"]))
def handle_user_agent_command(message):
    """Generates real device user-agent with Reply Keyboard categories."""
    user_id = message.from_user.id
    user_states[user_id] = "idle"
    cmd = message.text.strip().lower()
    
    cat = None
    if "iphone" in cmd:
        cat = "iphone"
    elif "android" in cmd:
        cat = "android"
    elif "windows" in cmd:
        cat = "windows"
    elif "mac" in cmd:
        cat = "mac"
        
    ua_obj = user_agents.get_user_agent(cat)
    text = format_user_agent_message(ua_obj)
    markup = create_user_agent_markup(ua_obj["ua"])
    
    if cmd in ["user-agent", "useragent", "/ua"]:
        bot.send_message(message.chat.id, "📱 <b>User-Agent Categories:</b>", reply_markup=get_user_agent_reply_keyboard())
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(func=lambda msg: msg.text and any(term in msg.text.lower() for term in ["history", "refresh history", "clear history", "clear cache"]))
def handle_history_command(message):
    """Displays user's 2FA generation history with Reply Keyboard management."""
    user_id = message.from_user.id
    user_states[user_id] = "idle"
    cmd = message.text.strip().lower()
    
    if "clear history" in cmd:
        database.clear_user_history(user_id)
        bot.send_message(message.chat.id, "🗑 <b>2FA History cleared successfully!</b>", reply_markup=get_history_reply_keyboard())
        return
    elif "clear cache" in cmd:
        database.clear_user_cache(user_id)
        user_cache_storage.pop(user_id, None)
        user_cache_storage.pop(f"2fa_{user_id}", None)
        bot.send_message(message.chat.id, "🧹 <b>Bot cache & session data cleared successfully!</b>", reply_markup=get_history_reply_keyboard())
        return
        
    records = database.get_user_history(user_id, limit=10)
    total_count = database.get_user_history_count(user_id)
    user_name = message.from_user.first_name or "User"
    
    text = format_history_message(user_name, records, total_count)
    bot.send_message(message.chat.id, text, reply_markup=get_history_reply_keyboard())


# ==================== PHOTO HANDLER (QR CODE SCANNER) ====================

@bot.message_handler(content_types=["photo"])
def handle_photo_qr_scan(message):
    """Scans sent photos/screenshots for 2FA QR codes."""
    user_id = message.from_user.id
    status_msg = bot.send_message(message.chat.id, "🔍 <i>Scanning image for 2FA QR Code...</i>")
    
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        secret, decoded_text, err = qr_scanner.scan_qr_from_bytes(downloaded)
        
        if not secret:
            err_text = (
                "📷 <b>No 2FA QR Code Detected</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Could not find a valid 2FA QR code in this image.\n\n"
                "💡 <i>Make sure the QR code is clearly visible and not cropped!</i>"
            )
            bot.edit_message_text(err_text, message.chat.id, status_msg.message_id)
            return
            
        cand, code, remaining, auth_err = authenticator.sanitize_and_generate(secret)
        if not code:
            bot.edit_message_text(f"❌ Decoded QR text: <code>{decoded_text}</code>, but could not parse valid 2FA secret.", message.chat.id, status_msg.message_id)
            return
            
        time_str = datetime.now().strftime("%I:%M %p")
        database.add_history_record(user_id, cand, code)
        
        res = [{
            "index": 1,
            "secret": cand,
            "otp": code,
            "remaining": remaining,
            "time": time_str,
            "valid": True
        }]
        
        output_text = format_2fa_output(res, is_qr=True)
        markup = create_2fa_output_markup(code, cand)
        user_cache_storage[f"2fa_{user_id}"] = cand
        try:
            bot.delete_message(message.chat.id, status_msg.message_id)
        except Exception:
            pass
        bot.send_message(message.chat.id, output_text, reply_markup=markup)
        
    except Exception as e:
        logger.error(f"Error handling photo QR: {e}")
        bot.edit_message_text("❌ An error occurred while processing the image. Please try again.", message.chat.id, status_msg.message_id)


# ==================== UNIVERSAL TEXT HANDLER ====================

@bot.message_handler(content_types=["text"])
def handle_all_text(message):
    """
    Universal text handler:
    1. FB Lite Profile URL -> Extracts numeric UID
    2. Stylish Font input
    3. 2FA Secret Key input
    """
    user_id = message.from_user.id
    text = message.text.strip()
    
    # 1. Check if user is sending FB Lite link, waiting_fb_lite state, or sent a direct numeric UID (e.g. 1000..., 6155...)
    is_numeric_uid = text.isdigit() and (8 <= len(text) <= 20)
    if user_states.get(user_id) == "waiting_fb_lite" or "facebook.com" in text or "fb://" in text or is_numeric_uid:
        uid = fb_tools.extract_fb_lite_uid(text)
        if uid:
            status_msg = bot.send_message(message.chat.id, "🔍 <i>Checking Facebook server for Live vs Checkpoint (Human)...</i>")
            is_live, status_desc = fb_tools.check_fb_uid_live(uid)
            out_msg = format_fb_lite_output(uid, status_desc)
            markup = create_fb_lite_markup(uid)
            try:
                bot.delete_message(message.chat.id, status_msg.message_id)
            except Exception:
                pass
            bot.send_message(message.chat.id, out_msg, reply_markup=markup)
            user_states[user_id] = "idle"
            return
        elif user_states.get(user_id) == "waiting_fb_lite":
            bot.send_message(message.chat.id, "❌ <i>Could not extract numeric UID. Please send a valid numeric UID or FB link.</i>")
            return

    # 2. Check if user is waiting to generate Stylish Fonts
    if user_states.get(user_id) == "waiting_font":
        styles = stylish_fonts.generate_all_styles(text)
        out_msg = format_stylish_font_output(text, styles)
        best_font = styles[0]["font"]
        markup = create_stylish_font_markup(best_font)
        bot.send_message(message.chat.id, out_msg, reply_markup=markup)
        user_states[user_id] = "idle"
        return

    # 3. Check if input is a 2FA Secret Key (supports direct key, 'BUMK FZ5I OR2K 6O3M', combos like 'uid|pass|2fakey', etc.)
    bulk_results = authenticator.parse_and_generate_bulk(text)
    valid_results = [r for r in bulk_results if r["valid"]]
    
    # Fallback: direct sanitization on full text
    if not valid_results:
        cand, code, remaining, err = authenticator.sanitize_and_generate(text)
        if code:
            valid_results = [{
                "index": 1,
                "raw": text,
                "secret": cand,
                "otp": code,
                "remaining": remaining,
                "time": datetime.now().strftime("%I:%M %p"),
                "valid": True
            }]
            bulk_results = valid_results
    
    if valid_results:
        for r in valid_results:
            database.add_history_record(user_id, r["secret"], r["otp"])
            database.update_user_cache(user_id, "2fa_gen", r["secret"])
            user_cache_storage[f"2fa_{user_id}"] = r["secret"]
            logger.info(f"User {user_id} generated 2FA OTP for secret: {r['secret'][:4]}****")
            
        output_text = format_2fa_output(bulk_results)
        
        if len(valid_results) == 1:
            first_valid = valid_results[0]
            markup = create_2fa_output_markup(first_valid["otp"], first_valid["secret"])
            bot.send_message(message.chat.id, output_text, reply_markup=markup)
        else:
            markup = InlineKeyboardMarkup(row_width=2)
            row = []
            for r in valid_results[:4]:
                row.append(InlineKeyboardButton(text=f"{r['otp']}", copy_text=CopyTextButton(text=r['otp'])))
                if len(row) == 2:
                    markup.add(*row)
                    row = []
            if row:
                markup.add(*row)
            bot.send_message(message.chat.id, output_text, reply_markup=markup)
        user_states[user_id] = "idle"
        return
    elif user_states.get(user_id) == "waiting_2fa":
        err_msg = (
            "❌ <b>Invalid 2FA Secret Key</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "The key provided does not appear to be a valid Base32 secret.\n\n"
            "📝 <i>Example:</i> <code>30FC RA5M D2O2 PRU2</code>\n"
            "Or upload a 📷 <b>QR Code screenshot</b>!"
        )
        bot.send_message(message.chat.id, err_msg)
        return

    # 4. Fallback response
    default_text = (
        "❓ <b>Unrecognized input</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Please select an option from the menu buttons below, send an FB Lite Link, 2FA Key, or QR photo."
    )
    bot.send_message(message.chat.id, default_text, reply_markup=get_main_reply_keyboard())


# ==================== CALLBACK QUERY HANDLERS ====================

@bot.callback_query_handler(func=lambda call: call.data == "menu:main")
def callback_back_to_main(call):
    """Returns to main menu."""
    active_2fa_sessions.pop(call.message.chat.id, None)
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    text = (
        "👋 <b>Welcome to Multi-Tool Bot!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Go Ahead Buddy ❤️\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 <b>Select an option below:</b>"
    )
    bot.send_message(call.message.chat.id, text, reply_markup=get_main_reply_keyboard())


@bot.callback_query_handler(func=lambda call: call.data.startswith("fn:"))
def callback_fake_name(call):
    """Handles Fake Name generation via inline buttons."""
    action = call.data.split(":")[1]
    gender = None if action in ["next", "Random"] else action
    
    identity = name_generator.get_fake_name(gender=gender)
    user_id = call.from_user.id
    database.update_user_cache(user_id, "fake_name", identity["full_name"])
    user_cache_storage[user_id] = identity
    
    text = format_fake_name_message(identity)
    markup = create_fake_name_markup(identity["first_name"], identity["last_name"], identity["full_name"])
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
        bot.answer_callback_query(call.id, "✅ Generated new USA Identity!")
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("2fa_refresh:"))
def callback_refresh_2fa(call):
    """Refreshes the TOTP code for a secret key."""
    secret = call.data.split(":", 1)[1]
    cand, code, remaining, err = authenticator.sanitize_and_generate(secret)
    
    if code:
        time_str = datetime.now().strftime("%I:%M %p")
        res = [{
            "index": 1,
            "secret": cand,
            "otp": code,
            "remaining": remaining,
            "time": time_str,
            "valid": True
        }]
        text = format_2fa_output(res)
        markup = create_2fa_output_markup(code, cand)
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
            bot.answer_callback_query(call.id, f"Refreshed: {code}")
        except Exception:
            bot.answer_callback_query(call.id, f"{code}")
    else:
        bot.answer_callback_query(call.id, "Unable to refresh.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("ua:"))
def callback_user_agent(call):
    """Handles category filtering for User-Agents."""
    category = call.data.split(":")[1]
    cat_arg = None if category == "random" else category
    
    ua_obj = user_agents.get_user_agent(cat_arg)
    text = format_user_agent_message(ua_obj)
    markup = create_user_agent_markup(ua_obj["ua"])
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
        bot.answer_callback_query(call.id, f"✅ Loaded {ua_obj['category']} User-Agent!")
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "fblite:try")
def callback_fblite_try(call):
    """Prompts for new FB Lite link."""
    user_id = call.from_user.id
    user_states[user_id] = "waiting_fb_lite"
    bot.send_message(call.message.chat.id, "🆔 Send the new FB Lite link you want to extract UID from:")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data == "font:try")
def callback_font_try(call):
    """Prompts for new text in font generator."""
    user_id = call.from_user.id
    user_states[user_id] = "waiting_font"
    bot.send_message(call.message.chat.id, "✍️ Send the new text you want to stylize:")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data == "hist:clear")
def callback_clear_history(call):
    """Clears all 2FA history for the user."""
    user_id = call.from_user.id
    database.clear_user_history(user_id)
    try:
        bot.answer_callback_query(call.id, "🗑 History cleared successfully!", show_alert=True)
    except Exception:
        pass
        
    cleared_text = (
        "✅ <b>History Cleared Successfully!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "All your 2FA generation records have been permanently wiped from the database.\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )
    try:
        bot.edit_message_text(cleared_text, call.message.chat.id, call.message.message_id)
    except Exception:
        bot.send_message(call.message.chat.id, cleared_text, reply_markup=get_history_reply_keyboard())


@bot.callback_query_handler(func=lambda call: call.data == "hist:clearcache")
def callback_clear_cache(call):
    """Clears cache and session storage for the user."""
    user_id = call.from_user.id
    database.clear_user_cache(user_id)
    user_cache_storage.pop(user_id, None)
    user_cache_storage.pop(f"2fa_{user_id}", None)
    try:
        bot.answer_callback_query(call.id, "🧹 Bot cache & session data cleared successfully!", show_alert=True)
    except Exception:
        pass
        
    records = database.get_user_history(user_id, limit=10)
    total_count = database.get_user_history_count(user_id)
    user_name = call.from_user.first_name or "User"
    
    text = format_history_message(user_name, records, total_count)
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data == "hist:refresh")
def callback_refresh_history(call):
    """Refreshes the history view."""
    user_id = call.from_user.id
    records = database.get_user_history(user_id, limit=10)
    total_count = database.get_user_history_count(user_id)
    user_name = call.from_user.first_name or "User"
    
    text = format_history_message(user_name, records, total_count)
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "🔄 History refreshed!")
    except Exception:
        bot.answer_callback_query(call.id, "History is up-to-date.")


# ==================== MAIN RUNNER ====================

if __name__ == "__main__":
    if not is_token_configured:
        logger.critical("=" * 65)
        logger.critical("❌ CRITICAL: Telegram BOT_TOKEN is missing or not configured!")
        logger.critical("Render Web Service started successfully and health check is PASSING.")
        logger.critical("However, the Telegram bot cannot start without a valid token.")
        logger.critical("")
        logger.critical("👉 HOW TO FIX ON RENDER:")
        logger.critical("1. Go to your Render Dashboard (https://dashboard.render.com)")
        logger.critical("2. Select this Web Service -> Click 'Environment' tab")
        logger.critical("3. Add Environment Variable:")
        logger.critical("      Key:   BOT_TOKEN")
        logger.critical("      Value: <Your Telegram Bot Token from @BotFather>")
        logger.critical("4. Click 'Save Changes' (Render will automatically re-deploy)")
        logger.critical("=" * 65)
        print("\n[!] BOT_TOKEN missing. Health server running to prevent deploy failure. Waiting for token in Render Environment...", flush=True)
        while True:
            time.sleep(3600)
            
    print("=" * 55)
    print("🚀 Prime Multi-Tool Bot is running...")
    print("👤 Features:")
    print("  • 👤 USA Fake Name Generator")
    print("  • 🔑 2FA Authenticator (with Live Progress Bar)")
    print("  • 🆔 FB Lite UID Extractor")
    print("  • ✍️ Stylish Font & Bio Generator")
    print("  • 📷 2FA QR Code Scanner")
    print("  • 📱 Real Device User-Agent Generator")
    print("  • 📜 History & Cache Management")
    print("=" * 55)
    
    # Clear any lingering webhook to prevent getUpdates conflict
    try:
        bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook cleared successfully.")
    except Exception as e:
        logger.warning(f"Failed to clear webhook: {e}")
        
    try:
        cmds = [BotCommand("start", "Start / Restart Bot")]
        bot.set_my_commands(cmds, scope=BotCommandScopeDefault())
        bot.set_my_commands(cmds, scope=BotCommandScopeAllPrivateChats())
        bot.set_chat_menu_button(menu_button=MenuButtonCommands(type="commands"))
    except Exception as e:
        logger.warning(f"Failed to set bot commands: {e}")
    
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)
        except ApiTelegramException as e:
            if getattr(e, "error_code", None) == 409 or "409" in str(e):
                logger.warning("Conflict 409 detected (rolling deploy handover). Retrying in 5s...")
                time.sleep(5)
            else:
                logger.error(f"Telegram API Exception: {e}. Retrying in 5s...")
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user.")
            break
        except Exception as e:
            logger.error(f"Unexpected polling error: {e}. Retrying in 5s...")
            time.sleep(5)
