import os
import time
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions

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
# BOT SETUP
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
user_vouches = {}
custom_welcomes = {}
tracked_groups = set()  
username_to_id = {}  # Tracks usernames to allow /vouch @username

# ==========================================
# AUTO LOCK / UNLOCK SYSTEM (12 AM & 7 AM IST)
# ==========================================
def auto_lock_unlock():
    locked_today = False
    unlocked_today = False
    while True:
        try:
            now = datetime.utcnow() + timedelta(hours=5, minutes=30)
            if now.hour == 0 and now.minute == 0 and not locked_today:
                for cid in list(tracked_groups):
                    try:
                        bot.set_chat_permissions(cid, ChatPermissions(can_send_messages=False))
                        bot.send_message(cid, "🔒 <b>Group Auto-Locked!</b> (12:00 AM)\n\n<i>Admins only mode active till 7:00 AM.</i>", parse_mode='html')
                    except: pass
                locked_today = True
                unlocked_today = False
            elif now.hour == 7 and now.minute == 0 and not unlocked_today:
                for cid in list(tracked_groups):
                    try:
                        bot.set_chat_permissions(cid, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
                        bot.send_message(cid, "🔓 <b>Group Auto-Unlocked!</b> (7:00 AM)\n\n<i>Members can now send messages. Trade safely!</i>", parse_mode='html')
                    except: pass
                unlocked_today = True
                locked_today = False
            elif now.hour == 12:
                locked_today = False
                unlocked_today = False
        except Exception as e: pass
        time.sleep(30)

Thread(target=auto_lock_unlock, daemon=True).start()

# ==========================================
# 1. START COMMAND
# ==========================================
@bot.message_handler(commands=['start'])
def start_handler(message):
    if message.chat.type != 'private': 
        tracked_groups.add(message.chat.id)
        return
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("➕ Add To Group", url=f"https://t.me/{bot.get_me().username}?startgroup=true"))
    bot.send_message(message.chat.id, "🛡️ <b>GAMERS CALL ESCROW BOT</b> 🛡️\n\nOfficial group assistant bot for <b>GAMERS CALL ESCROW SERVICE</b>.", parse_mode='html', reply_markup=markup)

# ==========================================
# 2. ESCROW RULES PANEL (/rules)
# ==========================================
@bot.message_handler(commands=['rules'])
def rules_handler(message):
    if message.chat.type == 'private': return
    tracked_groups.add(message.chat.id)
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
def rules_callback_query(call):
    if call.data == 'terms': bot.answer_callback_query(call.id, "All deals must go through official group admins. No outside DM deals covered!", show_alert=True)
    elif call.data == 'admins': bot.answer_callback_query(call.id, "Only deal with admins listed in the group description!", show_alert=True)

# ==========================================
# 3. ADVANCED /INFO COMMAND
# ==========================================
@bot.message_handler(commands=['info'])
def info_handler(message):
    if message.chat.type == 'private': return
    tracked_groups.add(message.chat.id)
    
    target_user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    uid, first_name = target_user.id, target_user.first_name
    username = f"@{target_user.username}" if target_user.username else "None"
    
    if target_user.username:
        username_to_id['@' + target_user.username.lower()] = uid
        
    try:
        member = bot.get_chat_member(message.chat.id, uid)
        status = 'Owner' if member.status.capitalize() == 'Creator' else member.status.capitalize()
    except: status = 'Member'
        
    warns, vouches = user_warns.get(uid, 0), user_vouches.get(uid, 0)
    
    info_text = (f"<b>GAMERS CALL SECURITY BOT</b>\n\n🆔 <b>ID:</b> <code>{uid}</code> <a href='tg://user?id={uid}'>#id{uid}</a>\n👦 <b>Name:</b> {first_name}\n🌐 <b>Username:</b> {username}\n👀 <b>Situation:</b> {status}\n❕ <b>Warns:</b> {warns}/3\n🤝 <b>Vouches:</b> {vouches}\n🔄 <b>Join:</b> System Not Tracked")
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("❕ Warn", callback_data=f"warnbtn_{uid}"))
    markup.row(InlineKeyboardButton("🔇 Mute", callback_data=f"mutebtn_{uid}"), InlineKeyboardButton("🚫 Ban", callback_data=f"banbtn_{uid}"))
    
    bot.reply_to(message, info_text, parse_mode='html', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith(('warnbtn_', 'mutebtn_', 'banbtn_')))
def info_buttons_callback(call):
    if call.from_user.id != ADMIN_ID: return bot.answer_callback_query(call.id, "⚠️ Only Admins can use these buttons!", show_alert=True)
    action, uid = call.data.split('_')
    uid = int(uid)
    
    if action == 'warnbtn':
        user_warns[uid] = user_warns.get(uid, 0) + 1
        if user_warns[uid] >= 3:
            try:
                bot.ban_chat_member(call.message.chat.id, uid)
                bot.send_message(call.message.chat.id, f"🚨 <b>User BANNED!</b> (3/3 Warnings)\n👤 ID: <code>{uid}</code>", parse_mode='html')
                user_warns[uid] = 0
            except: pass
        else: bot.send_message(call.message.chat.id, f"⚠️ <b>User Warned!</b> ({user_warns[uid]}/3)\n👤 ID: <code>{uid}</code>", parse_mode='html')
        bot.answer_callback_query(call.id, "Action: User Warned")
    elif action == 'mutebtn':
        try:
            bot.restrict_chat_member(call.message.chat.id, uid, can_send_messages=False)
            bot.send_message(call.message.chat.id, f"🔇 <b>Muted!</b> User <code>{uid}</code> cannot send messages.", parse_mode='html')
        except: pass
        bot.answer_callback_query(call.id, "Action: User Muted")
    elif action == 'banbtn':
        try:
            bot.ban_chat_member(call.message.chat.id, uid)
            bot.send_message(call.message.chat.id, f"🔨 <b>Banned!</b> User <code>{uid}</code> has been removed.", parse_mode='html')
        except: pass
        bot.answer_callback_query(call.id, "Action: User Banned")

# ==========================================
# 4. CUSTOM WELCOME MESSAGE
# ==========================================
@bot.message_handler(commands=['setwelcome'])
def set_welcome_handler(message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        custom_welcomes[message.chat.id] = args[1]
        bot.reply_to(message, "✅ <b>Custom Welcome Message Set!</b>\n\n<i>Use {name} in your text to mention the user.</i>", parse_mode='html')
    else:
        bot.reply_to(message, "⚠️ <b>Usage:</b> `/setwelcome [message]`\nExample: `/setwelcome Hello {name}, welcome to our Escrow!`", parse_mode='html')

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    tracked_groups.add(message.chat.id)
    for user in message.new_chat_members:
        if not user.is_bot:
            if user.username:
                username_to_id['@' + user.username.lower()] = user.id
            default_w = "👋 Welcome {name} to <b>GAMERS CALL ESCROW SERVICE</b>!\n📌 Type <code>/rules</code> for safe trading rules."
            w_text = custom_welcomes.get(message.chat.id, default_w)
            user_mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
            final_msg = w_text.replace('{name}', user_mention)
            bot.reply_to(message, final_msg, parse_mode='html')

# ==========================================
# 5. MANUAL LOCK / UNLOCK
# ==========================================
@bot.message_handler(commands=['lock'])
def lock_chat(message):
    if message.from_user.id != ADMIN_ID: return
    tracked_groups.add(message.chat.id)
    bot.set_chat_permissions(message.chat.id, ChatPermissions(can_send_messages=False))
    bot.reply_to(message, "🔒 <b>Group Locked!</b> Only Admins can message now.", parse_mode='html')

@bot.message_handler(commands=['unlock'])
def unlock_chat(message):
    if message.from_user.id != ADMIN_ID: return
    bot.set_chat_permissions(message.chat.id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
    bot.reply_to(message, "🔓 <b>Group Unlocked!</b> Everyone can message now.", parse_mode='html')

# ==========================================
# 6. ADVANCED VOUCH COMMAND
# ==========================================
@bot.message_handler(commands=['vouch'])
def vouch_handler(message):
    if message.from_user.id != ADMIN_ID: return
    
    args = message.text.split()
    uid = None
    amount = 1 # Default
    
    # CASE 1: Reply to a user
    if message.reply_to_message:
        uid = message.reply_to_message.from_user.id
        if len(args) > 1:
            try: amount = int(args[1])
            except: pass
            
    # CASE 2: No reply, using ID or @username
    else:
        if len(args) >= 3:
            target = args[1]
            if target.isdigit(): uid = int(target)
            elif target.startswith('@'): uid = username_to_id.get(target.lower())
            try: amount = int(args[2])
            except: pass
            
        elif len(args) == 2:
            target = args[1]
            if target.isdigit(): uid = int(target)
            elif target.startswith('@'): uid = username_to_id.get(target.lower())
            
    if not uid:
        return bot.reply_to(message, "⚠️ <b>Usage:</b>\n1. Reply: `/vouch [amount]`\n2. Direct: `/vouch [User ID or @username] [amount]`", parse_mode='html')
        
    user_vouches[uid] = user_vouches.get(uid, 0) + amount
    bot.reply_to(message, f"✅ <b>Trust updated by {amount}!</b>\nUser <code>{uid}</code> now has {user_vouches[uid]} vouches.", parse_mode='html')

# ==========================================
# 7. PIN & OTHER MODERATION COMMANDS
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

@bot.message_handler(commands=['ban'])
def ban_handler(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    try:
        bot.ban_chat_member(message.chat.id, uid)
        bot.reply_to(message, f"🔨 <b>Banned!</b>\n👤 ID: <code>{uid}</code>", parse_mode='html')
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

@bot.message_handler(commands=['unwarn'])
def unwarn_handler(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    if uid in user_warns:
        user_warns[uid] = 0
        bot.reply_to(message, "✅ <b>User warnings reset to 0!</b>", parse_mode='html')

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
# 8. FILTERS & ANTI-SPAM
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
    tracked_groups.add(message.chat.id)
    text = (message.text or "").lower()
    
    # Store username mapping for /vouch @username
    if message.from_user.username:
        username_to_id['@' + message.from_user.username.lower()] = message.from_user.id
    
    for keyword, reply_text in group_filters.items():
        if keyword in text and not text.startswith('/'):
            bot.reply_to(message, reply_text)
            break 

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
            
