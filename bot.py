import os
import time
from flask import Flask
from threading import Thread
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==========================================
# FAKE WEB SERVER (RENDER 24/7 UPTIME)
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "GAMERS CALL ESCROW BOT IS RUNNING!"

def run_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host="0.0.0.0", port=port)

server_thread = Thread(target=run_server)
server_thread.start()

# ==========================================
# BOT SETUP (ONLY TOKEN NEEDED NOW)
# ==========================================
TOKEN = '8505811106:AAGJpuK7pEVBWSikf0RbdNX1BNvuLoKPpSM'
ADMIN_ID = 8931925905

bot = telebot.TeleBot(TOKEN)

# ==========================================
# DATABASES (IN-MEMORY)
# ==========================================
ban_reasons = {}
user_warns = {}
group_filters = {}
approved_users = set()

# ==========================================
# 1. START COMMAND
# ==========================================
@bot.message_handler(commands=['start'])
def start_handler(message):
    if message.chat.type != 'private': return
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("➕ Add To Group", url=f"https://t.me/{bot.get_me().username}?startgroup=true"))
    
    welcome_text = "🛡️ <b>GAMERS CALL ESCROW BOT</b> 🛡️\n\nOfficial group assistant bot for <b>GAMERS CALL ESCROW SERVICE</b>."
    bot.send_message(message.chat.id, welcome_text, parse_mode='html', reply_markup=markup)

# ==========================================
# 2. INFO / RULES PANEL
# ==========================================
@bot.message_handler(commands=['info'])
def info_handler(message):
    if message.chat.type == 'private': return
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📜 View Terms", callback_data="terms"), InlineKeyboardButton("👑 Official Admins", callback_data="admins"))
    
    info_text = (
        "🎮 <b>GAMERS CALL ESCROW SERVICE</b> 🎮\n\n"
        "📌 <b>Important Safety Rules:</b>\n"
        "1️⃣ Always verify the admin username before sending payment.\n"
        "2️⃣ Real admins <b>NEVER</b> message you first in DM.\n"
        "3️⃣ Keep all chat and screenshots inside this group.\n"
        "4️⃣ Fee details and middleman terms must be cleared before trading.\n\n"
        "🛡️ <i>Trade safely with trusted official middlemen!</i>"
    )
    bot.reply_to(message, info_text, parse_mode='html', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['terms', 'admins'])
def callback_query(call):
    if call.data == 'terms':
        bot.answer_callback_query(call.id, "All deals must go through official group admins. No outside DM deals covered!", show_alert=True)
    elif call.data == 'admins':
        bot.answer_callback_query(call.id, "Only deal with admins listed in the group description!", show_alert=True)

# ==========================================
# 3. AUTO-WELCOME
# ==========================================
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    for user in message.new_chat_members:
        if not user.is_bot:
            welcome_msg = f"👋 Welcome <a href='tg://user?id={user.id}'>{user.first_name}</a> to <b>GAMERS CALL ESCROW SERVICE</b>!\n📌 Type <code>/info</code> for safe trading rules."
            bot.reply_to(message, welcome_msg, parse_mode='html')

# ==========================================
# 4. WARNING SYSTEM
# ==========================================
@bot.message_handler(commands=['warn'])
def warn_handler(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message: return bot.reply_to(message, "⚠️ Reply to a user's message to warn them.")
    
    uid = message.reply_to_message.from_user.id
    user_warns[uid] = user_warns.get(uid, 0) + 1
    
    if user_warns[uid] >= 3:
        try:
            bot.ban_chat_member(message.chat.id, uid)
            bot.reply_to(message, f"🚨 <b>User reached 3 warnings and has been BANNED!</b>\n👤 ID: <code>{uid}</code>", parse_mode='html')
            user_warns[uid] = 0
        except: pass
    else:
        bot.reply_to(message, f"⚠️ <b>User Warned!</b> ({user_warns[uid]}/3 warnings)\n👤 ID: <code>{uid}</code>", parse_mode='html')

@bot.message_handler(commands=['unwarn'])
def unwarn_handler(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    if uid in user_warns:
        user_warns[uid] = 0
        bot.reply_to(message, "✅ <b>User warnings reset to 0!</b>", parse_mode='html')

# ==========================================
# 5. PIN WITH LOUD / SILENT
# ==========================================
@bot.message_handler(commands=['pin'])
def pin_prompt(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message: return bot.reply_to(message, "⚠️ Reply to a message to pin it.")
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🔊 Loud Pin", callback_data=f"pin_loud_{message.reply_to_message.message_id}"),
               InlineKeyboardButton("🔕 Silent Pin", callback_data=f"pin_silent_{message.reply_to_message.message_id}"))
    bot.reply_to(message, "📌 Choose pin notification mode:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('pin_'))
def pin_callback(call):
    data = call.data.split('_')
    mode, msg_id = data[1], int(data[2])
    notify = (mode == 'loud')
    try:
        bot.pin_chat_message(call.message.chat.id, msg_id, disable_notification=not notify)
        bot.edit_message_text(f"📌 <b>Message Pinned!</b> ({'Loud' if notify else 'Silent'})", call.message.chat.id, call.message.message_id, parse_mode='html')
    except: pass

@bot.message_handler(commands=['unpin'])
def unpin_handler(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message: return bot.reply_to(message, "⚠️ Reply to a pinned message to unpin it.")
    try:
        bot.unpin_chat_message(message.chat.id, message.reply_to_message.message_id)
        bot.reply_to(message, "📌 <b>Message Unpinned!</b>", parse_mode='html')
    except: pass

# ==========================================
# 6. MODERATION (BAN/MUTE)
# ==========================================
@bot.message_handler(commands=['ban'])
def ban_handler(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message: return
    
    args = message.text.split(maxsplit=1)
    reason = args[1] if len(args) > 1 else "No reason"
    uid = message.reply_to_message.from_user.id
    ban_reasons[uid] = reason
    try:
        bot.ban_chat_member(message.chat.id, uid)
        bot.reply_to(message, f"🔨 <b>Banned!</b>\n👤 ID: <code>{uid}</code>\n📝 Reason: {reason}", parse_mode='html')
    except: pass

@bot.message_handler(commands=['mute'])
def mute_handler(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    try:
        bot.restrict_chat_member(message.chat.id, uid, can_send_messages=False)
        bot.reply_to(message, f"🔇 <b>Muted!</b> User cannot send messages.", parse_mode='html')
    except: pass

@bot.message_handler(commands=['unban', 'unmute'])
def unban_mute_handler(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    try:
        bot.restrict_chat_member(message.chat.id, uid, can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True)
        bot.reply_to(message, f"✅ <b>Restrictions Removed!</b>", parse_mode='html')
    except: pass

# ==========================================
# 7. ADMIN PROMOTE / DEMOTE
# ==========================================
@bot.message_handler(commands=['promote'])
def promote_handler(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    try:
        bot.promote_chat_member(message.chat.id, uid, can_change_info=False, can_post_messages=True, can_edit_messages=True, can_delete_messages=True, can_invite_users=True, can_restrict_members=True, can_pin_messages=True, can_promote_members=False)
        bot.reply_to(message, f"👑 <b>Promoted to Admin!</b>", parse_mode='html')
    except: pass

@bot.message_handler(commands=['demote'])
def demote_handler(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    try:
        bot.promote_chat_member(message.chat.id, uid, can_change_info=False, can_post_messages=False, can_edit_messages=False, can_delete_messages=False, can_invite_users=False, can_restrict_members=False, can_pin_messages=False, can_promote_members=False)
        bot.reply_to(message, f"📉 <b>Demoted!</b>", parse_mode='html')
    except: pass

# ==========================================
# 8. FILTERS & ANTI-SPAM LINK SHIELD
# ==========================================
@bot.message_handler(commands=['approve'])
def approve_handler(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    approved_users.add(uid)
    bot.reply_to(message, "✅ <b>User Approved!</b> (Can send links now)", parse_mode='html')

@bot.message_handler(commands=['filter'])
def add_filter(message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split(maxsplit=2)
    if len(args) < 3: return bot.reply_to(message, "⚠️ Usage: `/filter [keyword] [reply text]`")
    group_filters[args[1].lower()] = args[2]
    bot.reply_to(message, f"✅ Filter added for: <code>{args[1]}</code>", parse_mode='html')

@bot.message_handler(func=lambda m: True)
def main_chat_handler(message):
    if message.chat.type == 'private': return
    text = (message.text or "").lower()
    
    # Check Filters
    for keyword, reply_text in group_filters.items():
        if keyword in text and not text.startswith('/'):
            bot.reply_to(message, reply_text)
            break 

    # Anti-Spam (Delete External Links)
    if message.from_user.id == ADMIN_ID or message.from_user.id in approved_users: return
    if "http://" in text or "https://" in text or "t.me/" in text:
        try:
            bot.delete_message(message.chat.id, message.message_id)
            warning = bot.send_message(message.chat.id, f"⚠️ External links are blocked here! Ask Admin to /approve you.")
            time.sleep(5)
            bot.delete_message(message.chat.id, warning.message_id)
        except: pass

print("GAMERS CALL ESCROW BOT IS FULLY ACTIVE...")
bot.infinity_polling()
                                 
