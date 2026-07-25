import os
import asyncio
from flask import Flask
from threading import Thread
from telethon import TelegramClient, events, Button
from telethon.tl.types import ChatAdminRights

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
# CONFIGURATION
# ==========================================
API_ID = 31958928
API_HASH = '36135355d9df1aff72cde811ee9c01f2'
BOT_TOKEN = '8505811106:AAGJpuK7pEVBWSikf0RbdNX1BNvuLoKPpSM'
ADMIN_ID = 8931925905

bot = TelegramClient('gamers_call_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

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
@bot.on(events.NewMessage(pattern=r'(?i)^/start'))
async def start_handler(event):
    if not event.is_private: return
    welcome_text = "🛡️ <b>GAMERS CALL ESCROW BOT</b> 🛡️\n\nOfficial group assistant bot for <b>GAMERS CALL ESCROW SERVICE</b>."
    buttons = [[Button.url("➕ Add To Group", f"https://t.me/{(await bot.get_me()).username}?startgroup=true")]]
    await event.respond(welcome_text, buttons=buttons, parse_mode='html')

# ==========================================
# 2. INFO / RULES PANEL (Restored to /info)
# ==========================================
@bot.on(events.NewMessage(pattern=r'(?i)^/info'))
async def info_handler(event):
    if event.is_private: return
    info_text = (
        "🎮 <b>GAMERS CALL ESCROW SERVICE</b> 🎮\n\n"
        "📌 <b>Important Safety Rules:</b>\n"
        "1️⃣ Always verify the admin username before sending payment.\n"
        "2️⃣ Real admins <b>NEVER</b> message you first in DM.\n"
        "3️⃣ Keep all chat and screenshots inside this group.\n"
        "4️⃣ Fee details and middleman terms must be cleared before trading.\n\n"
        "🛡️ <i>Trade safely with trusted official middlemen!</i>"
    )
    buttons = [[Button.inline("📜 View Terms", b"terms"), Button.inline("👑 Official Admins", b"admins")]]
    await event.reply(info_text, buttons=buttons, parse_mode='html')

@bot.on(events.CallbackQuery(pattern=b'terms'))
async def terms_callback(event):
    await event.answer("All deals must go through official group admins. No outside DM deals covered!", alert=True)

@bot.on(events.CallbackQuery(pattern=b'admins'))
async def admins_callback(event):
    await event.answer("Only deal with admins listed in the group description!", alert=True)

# ==========================================
# 3. AUTO-WELCOME
# ==========================================
@bot.on(events.ChatAction)
async def welcome_new_member(event):
    if event.user_joined or event.added_by:
        for user in event.users:
            if user.bot: continue
            welcome_msg = f"👋 Welcome <a href='tg://user?id={user.id}'>{user.first_name}</a> to <b>GAMERS CALL ESCROW SERVICE</b>!\n📌 Type <code>/info</code> for safe trading rules."
            try:
                await event.respond(welcome_msg, parse_mode='html')
            except Exception: pass

# ==========================================
# 4. WARNING SYSTEM
# ==========================================
@bot.on(events.NewMessage(pattern=r'(?i)^/warn'))
async def warn_handler(event):
    if event.sender_id != ADMIN_ID: return
    reply = await event.get_reply_message()
    if not reply: return await event.reply("⚠️ Reply to a user's message to warn them.")
    
    uid = reply.sender_id
    user_warns[uid] = user_warns.get(uid, 0) + 1
    
    if user_warns[uid] >= 3:
        try:
            await event.client.edit_permissions(event.chat_id, uid, view_messages=False)
            await event.reply(f"🚨 <b>User reached 3 warnings and has been BANNED!</b>\n👤 ID: <code>{uid}</code>", parse_mode='html')
            user_warns[uid] = 0
        except: pass
    else:
        await event.reply(f"⚠️ <b>User Warned!</b> ({user_warns[uid]}/3 warnings)\n👤 ID: <code>{uid}</code>", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'(?i)^/unwarn'))
async def unwarn_handler(event):
    if event.sender_id != ADMIN_ID: return
    reply = await event.get_reply_message()
    if not reply: return
    if reply.sender_id in user_warns:
        user_warns[reply.sender_id] = 0
        await event.reply("✅ <b>User warnings reset to 0!</b>", parse_mode='html')

# ==========================================
# 5. PIN WITH LOUD / SILENT
# ==========================================
@bot.on(events.NewMessage(pattern=r'(?i)^/pin'))
async def pin_prompt(event):
    if event.sender_id != ADMIN_ID: return
    reply = await event.get_reply_message()
    if not reply: return await event.reply("⚠️ Reply to a message to pin it.")
    
    buttons = [[Button.inline("🔊 Loud Pin", data=f"pin_loud_{reply.id}".encode()), Button.inline("🔕 Silent Pin", data=f"pin_silent_{reply.id}".encode())]]
    await event.reply("📌 Choose pin notification mode:", buttons=buttons)

@bot.on(events.CallbackQuery(pattern=b'pin_'))
async def pin_callback(event):
    data = event.data.decode().split('_')
    mode, msg_id = data[1], int(data[2])
    notify = (mode == 'loud')
    try:
        await bot.pin_message(event.chat_id, msg_id, notify=notify)
        await event.edit(f"📌 <b>Message Pinned!</b> ({'Loud' if notify else 'Silent'})", parse_mode='html')
    except Exception as e: pass

@bot.on(events.NewMessage(pattern=r'(?i)^/unpin'))
async def unpin_handler(event):
    if event.sender_id != ADMIN_ID: return
    reply = await event.get_reply_message()
    if not reply: return await event.reply("⚠️ Reply to a pinned message to unpin it.")
    try:
        await bot.unpin_message(event.chat_id, reply.id)
        await event.reply("📌 <b>Message Unpinned!</b>", parse_mode='html')
    except: pass

# ==========================================
# 6. MODERATION (BAN/MUTE)
# ==========================================
@bot.on(events.NewMessage(pattern=r'(?i)^/ban'))
async def ban_handler(event):
    if event.sender_id != ADMIN_ID: return
    reply = await event.get_reply_message()
    if not reply: return
    
    reason = event.raw_text.split(maxsplit=1)[1] if len(event.raw_text.split()) > 1 else "No reason"
    ban_reasons[reply.sender_id] = reason
    try:
        await event.client.edit_permissions(event.chat_id, reply.sender_id, view_messages=False)
        await event.reply(f"🔨 <b>Banned!</b>\n👤 ID: <code>{reply.sender_id}</code>\n📝 Reason: {reason}", parse_mode='html')
    except: pass

@bot.on(events.NewMessage(pattern=r'(?i)^/mute'))
async def mute_handler(event):
    if event.sender_id != ADMIN_ID: return
    reply = await event.get_reply_message()
    if not reply: return
    try:
        await event.client.edit_permissions(event.chat_id, reply.sender_id, send_messages=False)
        await event.reply(f"🔇 <b>Muted!</b> User cannot send messages.", parse_mode='html')
    except: pass

@bot.on(events.NewMessage(pattern=r'(?i)^/unban|(?i)^/unmute'))
async def unban_mute_handler(event):
    if event.sender_id != ADMIN_ID: return
    reply = await event.get_reply_message()
    if not reply: return
    try:
        await event.client.edit_permissions(event.chat_id, reply.sender_id, view_messages=True, send_messages=True)
        await event.reply(f"✅ <b>Restrictions Removed!</b>", parse_mode='html')
    except: pass

# ==========================================
# 7. ADMIN PROMOTE / DEMOTE
# ==========================================
@bot.on(events.NewMessage(pattern=r'(?i)^/promote'))
async def promote_handler(event):
    if event.sender_id != ADMIN_ID: return
    reply = await event.get_reply_message()
    if not reply: return
    try:
        rights = ChatAdminRights(change_info=False, post_messages=True, edit_messages=True, delete_messages=True, ban_users=True, invite_users=True, pin_messages=True, add_admins=False)
        await bot.edit_admin(event.chat_id, reply.sender_id, rights, title="Middleman")
        await event.reply(f"👑 <b>Promoted to Admin!</b>", parse_mode='html')
    except: pass

@bot.on(events.NewMessage(pattern=r'(?i)^/demote'))
async def demote_handler(event):
    if event.sender_id != ADMIN_ID: return
    reply = await event.get_reply_message()
    if not reply: return
    try:
        empty_rights = ChatAdminRights(change_info=False, post_messages=False, edit_messages=False, delete_messages=False, ban_users=False, invite_users=False, pin_messages=False, add_admins=False)
        await bot.edit_admin(event.chat_id, reply.sender_id, empty_rights)
        await event.reply(f"📉 <b>Demoted!</b>", parse_mode='html')
    except: pass

# ==========================================
# 8. FILTERS & ANTI-SPAM LINK SHIELD
# ==========================================
@bot.on(events.NewMessage(pattern=r'(?i)^/approve'))
async def approve_handler(event):
    if event.sender_id != ADMIN_ID: return
    reply = await event.get_reply_message()
    if not reply: return
    approved_users.add(reply.sender_id)
    await event.reply("✅ <b>User Approved!</b> (Can send links now)", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'(?i)^/filter'))
async def add_filter(event):
    if event.sender_id != ADMIN_ID: return
    args = event.raw_text.split(maxsplit=2)
    if len(args) < 3: return await event.reply("⚠️ Usage: `/filter [keyword] [reply text]`")
    group_filters[args[1].lower()] = args[2]
    await event.reply(f"✅ Filter added for: <code>{args[1]}</code>", parse_mode='html')

@bot.on(events.NewMessage(incoming=True))
async def main_chat_handler(event):
    if event.is_private: return
    text = event.raw_text.lower()
    
    # Check Filters
    for keyword, reply_text in group_filters.items():
        if keyword in text and not text.startswith('/'):
            await event.reply(reply_text)
            break 

    # Anti-Spam (Delete External Links)
    if event.sender_id == ADMIN_ID or event.sender_id in approved_users: return
    if "http://" in text or "https://" in text or "t.me/" in text:
        try:
            await event.delete()
            warning = await event.respond(f"⚠️ External links are blocked here! Ask Admin to /approve you.")
            await asyncio.sleep(5)
            await warning.delete()
        except: pass

print("GAMERS CALL ESCROW BOT IS FULLY ACTIVE...")
bot.run_until_disconnected()
            
