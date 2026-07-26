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
user_vouches = {}
custom_welcomes = {}
tracked_groups = set()  
username_to_id = {}  
approved_users = set()

# BAD WORDS LIST FOR AUTO-WARN
bad_words = ['madarchod', 'bhenchod', 'chutiya', 'bhosdike', 'mc', 'bc', 'randi', 'gandu', 'suar', 'kutta', 'scam', 'scammer', 'bsdk', 'bawal']

# ==========================================
# ADMIN CHECKER
# ==========================================
def is_admin(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except:
        return False

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
# 1. HELP & START COMMANDS
# ==========================================
@bot.message_handler(commands=['start'])
def start_handler(message):
    if message.chat.type != 'private': 
        tracked_groups.add(message.chat.id)
        return
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("➕ Add To Group", url=f"https://t.me/{bot.get_me().username}?startgroup=true"))
    bot.send_message(message.chat.id, "🛡️ <b>GAMERS CALL ESCROW BOT</b> 🛡️\n\nOfficial group assistant bot for <b>GAMERS CALL ESCROW SERVICE</b>.", parse_mode='html', reply_markup=markup)

@bot.message_handler(commands=['help'])
def help_command(message):
    if message.chat.type == 'private': return
    tracked_groups.add(message.chat.id)
    help_text = (
        "🛡️ <b>GAMERS CALL ESCROW BOT COMMANDS</b> 🛡️\n\n"
        "<b>👮‍♂️ Moderation (No Clash with Rose):</b>\n"
        "<code>/id</code> - Check user profile & action buttons\n"
        "<code>/cunwarn</code> - Remove all warnings from a user\n"
        "<code>/cban</code> - Ban a user\n"
        "<code>/cunban</code> - Unban a user\n"
        "<code>/cunmute</code> - Unmute a user\n\n"
        "<b>📌 Group Management:</b>\n"
        "<code>/cpin</code> - Pin a message (Loud/Silent options)\n"
        "<code>/cunpin</code> - Unpin a message\n"
        "<code>/clock</code> - Lock group (Admins only)\n"
        "<code>/cunlock</code> - Unlock group\n\n"
        "<b>🤝 Trust System:</b>\n"
        "<code>/vouch [amount]</code> - Add vouches\n\n"
        "<b>👋 Welcome System:</b>\n"
        "<code>/addwelcome [text]</code> - Reply to a photo to set custom welcome.\n"
        "<code>/testwelcome</code> - Test the welcome message manually."
    )
    bot.reply_to(message, help_text, parse_mode='html')

# ==========================================
# 2. ESCROW RULES PANEL
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
# 3. ID / PROFILE COMMAND
# ==========================================
@bot.message_handler(commands=['id', 'profile'])
def id_handler(message):
    if message.chat.type == 'private': return
    tracked_groups.add(message.chat.id)
    
    args = message.text.split()
    target_user = None
    
    if len(args) > 1 and args[1].startswith('@'):
        username = args[1].lower()
        if username in username_to_id:
            uid = username_to_id[username]
            try:
                chat_member = bot.get_chat_member(message.chat.id, uid)
                target_user = chat_member.user
            except: pass
        if not target_user:
             return bot.reply_to(message, "⚠️ <b>User not found in memory!</b>\nMake sure they have sent at least one message here.", parse_mode='html')
    elif message.reply_to_message:
        target_user = message.reply_to_message.from_user
    else:
        target_user = message.from_user
        
    uid, first_name = target_user.id, target_user.first_name
    username = f"@{target_user.username}" if target_user.username else "None"
    
    if target_user.username:
        username_to_id['@' + target_user.username.lower()] = uid
        
    try:
        member = bot.get_chat_member(message.chat.id, uid)
        status = 'Owner' if member.status.capitalize() == 'Creator' else member.status.capitalize()
    except: status = 'Member'
        
    warns, vouches = user_warns.get(uid, 0), user_vouches.get(uid, 0)
    
    info_text = (f"<b>GAMERS CALL SECURITY BOT</b>\n\n🆔 <b>ID:</b> <code>{uid}</code> <a href='tg://user?id={uid}'>#id{uid}</a>\n👦 <b>Name:</b> {first_name}\n🌐 <b>Username:</b> {username}\n👀 <b>Situation:</b> {status}\n❕ <b>Warns:</b> {warns}/5\n🤝 <b>Vouches:</b> {vouches}\n🔄 <b>Join:</b> System Not Tracked")
    
    markup = InlineKeyboardMarkup()
    if not is_admin(message.chat.id, uid):
        markup.row(InlineKeyboardButton("❕ Warn", callback_data=f"warnbtn_{uid}"))
        markup.row(InlineKeyboardButton("🔇 Mute", callback_data=f"mutebtn_{uid}"), InlineKeyboardButton("🚫 Ban", callback_data=f"banbtn_{uid}"))
    
    bot.reply_to(message, info_text, parse_mode='html', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith(('warnbtn_', 'mutebtn_', 'banbtn_')))
def info_buttons_callback(call):
    if call.from_user.id != ADMIN_ID: return bot.answer_callback_query(call.id, "⚠️ Only Escrow Owners can use these buttons!", show_alert=True)
    action, uid = call.data.split('_')
    uid = int(uid)
    
    if is_admin(call.message.chat.id, uid): return bot.answer_callback_query(call.id, "⚠️ Cannot perform this action on an Admin!", show_alert=True)
    
    if action == 'warnbtn':
        user_warns[uid] = user_warns.get(uid, 0) + 1
        if user_warns[uid] >= 5:
            try:
                bot.ban_chat_member(call.message.chat.id, uid)
                bot.send_message(call.message.chat.id, f"🚨 <b>User BANNED!</b> (5/5 Warnings)\n👤 ID: <code>{uid}</code>", parse_mode='html')
                user_warns[uid] = 0
            except: pass
        else: bot.send_message(call.message.chat.id, f"⚠️ <b>User Warned!</b> ({user_warns[uid]}/5)\n👤 ID: <code>{uid}</code>", parse_mode='html')
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
# 4. CUSTOM PHOTO WELCOME MESSAGE
# ==========================================
@bot.message_handler(commands=['addwelcome'])
def add_welcome_handler(message):
    if message.from_user.id != ADMIN_ID: return
    
    welcome_text = message.text.replace('/addwelcome', '').strip()
    media_id = None
    media_type = None
    
    if message.reply_to_message:
        if message.reply_to_message.photo:
            media_id = message.reply_to_message.photo[-1].file_id
            media_type = 'photo'
        elif message.reply_to_message.animation:
            media_id = message.reply_to_message.animation.file_id
            media_type = 'animation'
        elif message.reply_to_message.video:
            media_id = message.reply_to_message.video.file_id
            media_type = 'video'
            
        if not welcome_text and message.reply_to_message.caption:
            welcome_text = message.reply_to_message.caption
            
    if not welcome_text:
        welcome_text = "👋 Welcome {name} to <b>GAMERS CALL ESCROW SERVICE!</b> 🎀🫂\nPlease check /rules before trading."
        
    custom_welcomes[message.chat.id] = {
        'text': welcome_text,
        'media': media_id,
        'type': media_type
    }
    
    bot.reply_to(message, "✅ <b>Custom Welcome Saved!</b>\n\n<i>Your bot will now send this message (with the photo if attached) to new members!</i>", parse_mode='html')

@bot.message_handler(commands=['testwelcome'])
def test_welcome(message):
    w_data = custom_welcomes.get(message.chat.id, {
        'text': "👋 Welcome {name} to <b>GAMERS CALL ESCROW SERVICE!</b> 🎀🫂\nPlease check /rules before trading.",
        'media': None,
        'type': None
    })
    
    user_mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
    final_msg = w_data['text'].replace('{name}', user_mention)
    
    try:
        if w_data['media']:
            if w_data['type'] == 'photo': bot.send_photo(message.chat.id, w_data['media'], caption=final_msg, parse_mode='html')
            elif w_data['type'] == 'animation': bot.send_animation(message.chat.id, w_data['media'], caption=final_msg, parse_mode='html')
            elif w_data['type'] == 'video': bot.send_video(message.chat.id, w_data['media'], caption=final_msg, parse_mode='html')
        else: bot.reply_to(message, final_msg, parse_mode='html')
    except: pass
    
    bot.send_message(message.chat.id, "<i>(This is how the automatic welcome message will look when a new member joins!)</i>", parse_mode='html')

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    tracked_groups.add(message.chat.id)
    w_data = custom_welcomes.get(message.chat.id, {
        'text': "👋 Welcome {name} to <b>GAMERS CALL ESCROW SERVICE!</b> 🎀🫂\nPlease check /rules before trading.",
        'media': None,
        'type': None
    })
    
    for user in message.new_chat_members:
        if not user.is_bot:
            if user.username:
                username_to_id['@' + user.username.lower()] = user.id
            
            user_mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
            final_msg = w_data['text'].replace('{name}', user_mention)
            
            try:
                if w_data['media']:
                    if w_data['type'] == 'photo': bot.send_photo(message.chat.id, w_data['media'], caption=final_msg, parse_mode='html')
                    elif w_data['type'] == 'animation': bot.send_animation(message.chat.id, w_data['media'], caption=final_msg, parse_mode='html')
                    elif w_data['type'] == 'video': bot.send_video(message.chat.id, w_data['media'], caption=final_msg, parse_mode='html')
                else: bot.send_message(message.chat.id, final_msg, parse_mode='html')
            except: pass

# ==========================================
# 5. LOCK & UNLOCK
# ==========================================
@bot.message_handler(commands=['clock'])
def lock_chat(message):
    if message.from_user.id != ADMIN_ID: return
    tracked_groups.add(message.chat.id)
    bot.set_chat_permissions(message.chat.id, ChatPermissions(can_send_messages=False))
    bot.reply_to(message, "🔒 <b>Group Locked!</b> Only Admins can message now.", parse_mode='html')

@bot.message_handler(commands=['cunlock'])
def unlock_chat(message):
    if message.from_user.id != ADMIN_ID: return
    tracked_groups.add(message.chat.id)
    bot.set_chat_permissions(message.chat.id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
    bot.reply_to(message, "🔓 <b>Group Unlocked!</b> Everyone can message now.", parse_mode='html')

# ==========================================
# 6. VOUCH
# ==========================================
@bot.message_handler(commands=['vouch'])
def vouch_handler(message):
    if message.from_user.id != ADMIN_ID: return
    
    args = message.text.split()
    uid = None
    amount = 1 
    
    if message.reply_to_message:
        uid = message.reply_to_message.from_user.id
        if len(args) > 1:
            try: amount = int(args[1])
            except: pass
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
# 7. MODERATION
# ==========================================
@bot.message_handler(commands=['cpin'])
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

@bot.message_handler(commands=['cunpin'])
def unpin_handler(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message: return bot.reply_to(message, "⚠️ Reply to a pinned message to unpin it.")
    try:
        bot.unpin_chat_message(message.chat.id, message.reply_to_message.message_id)
        bot.reply_to(message, "📌 <b>Message Unpinned!</b>", parse_mode='html')
    except: pass

@bot.message_handler(commands=['cban'])
def ban_handler(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    if is_admin(message.chat.id, uid): return bot.reply_to(message, "⚠️ Cannot ban an Admin!")
    try:
        bot.ban_chat_member(message.chat.id, uid)
        bot.reply_to(message, f"🔨 <b>Banned!</b>\n👤 ID: <code>{uid}</code>", parse_mode='html')
    except: pass

@bot.message_handler(commands=['cunban', 'cunmute'])
def unban_mute_handler(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    try:
        bot.restrict_chat_member(message.chat.id, uid, can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True)
        bot.reply_to(message, f"✅ <b>Restrictions Removed!</b>", parse_mode='html')
    except: pass

@bot.message_handler(commands=['cunwarn'])
def unwarn_handler(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    if uid in user_warns:
        user_warns[uid] = 0
        bot.reply_to(message, "✅ <b>User warnings reset to 0!</b>", parse_mode='html')
    else:
        bot.reply_to(message, "✅ User already has 0 warnings.", parse_mode='html')

# ==========================================
# 8. ANTI-SPAM (APPROVE COMMAND)
# ==========================================
@bot.message_handler(commands=['approve'])
def approve_handler(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    approved_users.add(uid)
    bot.reply_to(message, "✅ <b>User Approved!</b> (Can send links & forwards now)", parse_mode='html')

# ==========================================
# 9. MAIN MESSAGE HANDLER (SILENT FILTERS + GALI BAN)
# ==========================================
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'video', 'document', 'animation'])
def main_chat_handler(message):
    if message.chat.type == 'private': return
    tracked_groups.add(message.chat.id)
    
    uid = message.from_user.id
    if message.from_user.username:
        username_to_id['@' + message.from_user.username.lower()] = uid

    # Admins and approved users bypass all filters
    if is_admin(message.chat.id, uid) or uid in approved_users: return

    # --- 1. ANTI-FORWARD (SILENT DELETE) ---
    if message.forward_date:
        try:
            bot.delete_message(message.chat.id, message.message_id)
            return
        except: pass

    text = (message.text or message.caption or "").lower()

    # --- 2. ANTI-LINK (SILENT DELETE) ---
    has_link = False
    link_keywords = ["http://", "https://", "t.me/", ".com", ".in", "www."]
    if any(keyword in text for keyword in link_keywords):
        has_link = True
    
    if not has_link and (message.entities or message.caption_entities):
        entities = message.entities if message.entities else message.caption_entities
        if any(ent.type in ['url', 'text_link'] for ent in entities):
            has_link = True
            
    if has_link:
        try:
            bot.delete_message(message.chat.id, message.message_id)
            return
        except: pass

    # --- 3. ANTI-ABUSE (GALI) SYSTEM (WARNS & BANS) ---
    for word in bad_words:
        if f" {word} " in f" {text} " or text == word:
            try:
                bot.delete_message(message.chat.id, message.message_id)
                user_warns[uid] = user_warns.get(uid, 0) + 1
                
                if user_warns[uid] >= 5:
                    bot.ban_chat_member(message.chat.id, uid)
                    bot.send_message(message.chat.id, f"🚨 <b>User BANNED!</b> (5/5 Warnings for abusive language)\n👤 ID: <code>{uid}</code>", parse_mode='html')
                    user_warns[uid] = 0
                else:
                    bot.send_message(message.chat.id, f"🤬 <b>Language Warning!</b> ({user_warns[uid]}/5)\n<a href='tg://user?id={uid}'>{message.from_user.first_name}</a>, please do not use abusive words.", parse_mode='html')
                return
            except: pass

print("GAMERS CALL ESCROW BOT IS FULLY ACTIVE...")
bot.infinity_polling()
