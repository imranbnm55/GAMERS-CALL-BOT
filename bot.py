import os
from flask import Flask
from threading import Thread
from telethon import TelegramClient, events
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

# Storage for ban reasons
ban_reasons = {}

# ==========================================
# /START COMMAND (Private Chat)
# ==========================================
@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if not event.is_private:
        return
    welcome_text = (
        "🛡️ <b>GAMERS CALL ESCROW BOT</b> 🛡️\n\n"
        "Official group assistant bot for <b>GAMERS CALL ESCROW SERVICE</b>.\n\n"
        "<i>Add me to your group and give FULL Admin rights!</i>"
    )
    buttons = [[events.custom.Button.inline("➕ Add To Group", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true")]]
    await event.respond(welcome_text, buttons=buttons, parse_mode='html')

# ==========================================
# GROUP INFO & RULES PANEL
# ==========================================
@bot.on(events.NewMessage(pattern=r'/info'))
async def info_handler(event):
    if event.is_private:
        return
    info_text = (
        "🎮 <b>WELCOME TO GAMERS CALL ESCROW SERVICE</b> 🎮\n\n"
        "📌 <b>Important Safety Rules:</b>\n"
        "1️⃣ Always verify the admin username before sending payment.\n"
        "2️⃣ Real admins <b>NEVER</b> message you first in DM.\n"
        "3️⃣ Keep all chat and screenshots inside this group.\n"
        "4️⃣ Fee details and middleman terms must be cleared before trading.\n\n"
        "🛡️ <i>Trade safely with trusted official middlemen!</i>"
    )
    buttons = [
        [events.custom.Button.inline("📜 View Terms", b"terms"), events.custom.Button.inline("👑 Official Admins", b"admins")]
    ]
    await event.reply(info_text, buttons=buttons, parse_mode='html')

@bot.on(events.CallbackQuery(pattern=b'terms'))
async def terms_callback(event):
    await event.answer("Terms: All deals must go through official group admins. No outside DM deals covered!", alert=True)

@bot.on(events.CallbackQuery(pattern=b'admins'))
async def admins_callback(event):
    await event.answer("Official Admin: Only deal with admins listed in the group description!", alert=True)

# ==========================================
# AUTO-WELCOME
# ==========================================
@bot.on(events.ChatAction)
async def welcome_new_member(event):
    if event.user_joined or event.added_by:
        for user in event.users:
            if user.bot:
                continue
            welcome_msg = f"👋 Welcome <a href='tg://user?id={user.id}'>{user.first_name}</a> to <b>GAMERS CALL ESCROW SERVICE</b>!\n📌 Type <code>/info</code> for safe trading rules."
            try:
                await event.respond(welcome_msg, parse_mode='html')
            except Exception:
                pass

# ==========================================
# PIN WITH LOUD / SILENT BUTTONS
# ==========================================
@bot.on(events.NewMessage(pattern=r'/pin'))
async def pin_prompt(event):
    if event.sender_id != ADMIN_ID: return
    reply = await event.get_reply_message()
    if not reply: return await event.reply("⚠️ Reply to a message to pin it.")
    
    buttons = [
        [
            events.custom.Button.inline("🔊 Loud Pin", data=f"pin_loud_{reply.id}".encode()),
            events.custom.Button.inline("🔕 Silent Pin", data=f"pin_silent_{reply.id}".encode())
        ]
    ]
    await event.reply("📌 Choose pin notification mode:", buttons=buttons)

@bot.on(events.CallbackQuery(pattern=b'pin_'))
async def pin_callback(event):
    data = event.data.decode()
    parts = data.split('_')
    mode = parts[1] # 'loud' or 'silent'
    msg_id = int(parts[2])
    
    notify = (mode == 'loud')
    try:
        await bot.pin_message(event.chat_id, msg_id, notify=notify)
        mode_text = "Loud (With Notification)" if notify else "Silent (No Notification)"
        await event.edit(f"📌 <b>Message Pinned Successfully!</b>\nMode: {mode_text}", parse_mode='html')
    except Exception as e:
        await event.edit(f"❌ Error pinning message: {str(e)}")

@bot.on(events.NewMessage(pattern=r'/unpin'))
async def unpin_handler(event):
    if event.sender_id != ADMIN_ID: return
    reply = await event.get_reply_message()
    if not reply: return await event.reply("⚠️ Reply to a pinned message to unpin it.")
    try:
        await bot.unpin_message(event.chat_id, reply.id)
        await event.reply("📌 <b>Message Unpinned!</b>", parse_mode='html')
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

# ==========================================
# BAN WITH REASON & BANINFO
# ==========================================
@bot.on(events.NewMessage(pattern=r'/ban'))
async def ban_handler(event):
    if event.sender_id != ADMIN_ID: return
    reply = await event.get_reply_message()
    if not reply: return await event.reply("⚠️ Reply to a message with `/ban [reason]` to ban a user.")
    
    args = event.raw_text.split(maxsplit=1)
    reason = args[1] if len(args) > 1 else "No reason provided"
    
    ban_reasons[reply.sender_id] = reason
    
    try:
        await event.client.edit_permissions(event.chat_id, reply.sender_id, view_messages=False)
        await event.reply(f"🔨 <b>User Banned Successfully!</b>\n👤 User ID: <code>{reply.sender_id}</code>\n📝 Reason: {reason}", parse_mode='html')
    except Exception as e:
        await event.reply(f"❌ Error banning user: {str(e)}")

@bot.on(events.NewMessage(pattern=r'/baninfo'))
async def baninfo_handler(event):
    if event.sender_id != ADMIN_ID: return
    reply = await event.get_reply_message()
    if not reply: return await event.reply("⚠️ Reply to a user's message to check their ban reason.")
    
    reason = ban_reasons.get(reply.sender_id, "No ban record found or user not banned with reason.")
    await event.reply(f"🔍 <b>Ban Info:</b>\n👤 User ID: <code>{reply.sender_id}</code>\n📝 Reason: {reason}", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'/unban'))
async def unban_handler(event):
    if event.sender_id != ADMIN_ID: return
    reply = await event.get_reply_message()
    if not reply: return await event.reply("⚠️ Reply to a user's message to unban them.")
    try:
        await event.client.edit_permissions(event.chat_id, reply.sender_id, view_messages=True, send_messages=True)
        if reply.sender_id in ban_reasons:
            del ban_reasons[reply.sender_id]
        await event.reply(f"✅ <b>User Unbanned Successfully!</b>", parse_mode='html')
    except Exception as e:
        pass

# ==========================================
# PROMOTE & DEMOTE
# ==========================================
@bot.on(events.NewMessage(pattern=r'/promote'))
async def promote_handler(event):
    if event.sender_id != ADMIN_ID: return
    reply = await event.get_reply_message()
    if not reply: return await event.reply("⚠️ Reply to a message to promote user.")
    try:
        rights = ChatAdminRights(change_info=False, post_messages=True, edit_messages=True, delete_messages=True, ban_users=True, invite_users=True, pin_messages=True, add_admins=False)
        await bot.edit_admin(event.chat_id, reply.sender_id, rights, title="Middleman")
        await event.reply(f"👑 <b>User Promoted to Admin!</b>", parse_mode='html')
    except Exception as e:
        await event.reply(f"❌ Error: Make sure bot has 'Add Admins' right.")

@bot.on(events.NewMessage(pattern=r'/demote'))
async def demote_handler(event):
    if event.sender_id != ADMIN_ID: return
    reply = await event.get_reply_message()
    if not reply: return await event.reply("⚠️ Reply to a message to demote user.")
    try:
        empty_rights = ChatAdminRights(change_info=False, post_messages=False, edit_messages=False, delete_messages=False, ban_users=False, invite_users=False, pin_messages=False, add_admins=False)
        await bot.edit_admin(event.chat_id, reply.sender_id, empty_rights)
        await event.reply(f"📉 <b>User Demoted Successfully!</b>", parse_mode='html')
    except Exception as e:
        pass

print("GAMERS CALL ESCROW BOT IS FULLY ACTIVE...")
bot.run_until_disconnected()
  
