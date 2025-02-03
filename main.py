import asyncio
import time
from pyrogram import Client, filters
from pymongo import MongoClient
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# 🔹 Config
SESSION_STRING = "YOUR_SESSION_STRING"
API_ID = 22878444
API_HASH = "550641aa3600a98c1cb94afc259f2244"
OWNER_ID = 6663845789  # Only owner can use commands
MONGO_URL = "mongodb+srv://Akeno:Hajime@akeno.zyn9h.mongodb.net/"

# 🔹 MongoDB Setup
client = MongoClient(MONGO_URL)
db = client["CenzoAd"]
groups = db["groups"]  # Store groups
settings = db["settings"]  # Store scheduled message & delay settings
chat_links = db["chat_links"]  # Store chat folder links

# 🔹 Pyrogram Client
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)


# ✅ **Start Command**
@app.on_message(filters.command("start") & filters.user(OWNER_ID))
async def start(client, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Network", url="https://t.me/identicate"),
         InlineKeyboardButton("Marketplace", url="https://t.me/martline")],
        [InlineKeyboardButton("Developer", url="https://t.me/cenzeo")]
    ])

    await message.reply_photo(
        photo="https://ibb.co/bjQKPGgH",  # Change this URL
        caption="""◆━━━━━━━━◆ 𝗠𝗮𝗿𝗸𝗲𝘁𝗽𝗹𝗮𝗰𝗲 𝗠𝗮𝗻𝗮𝗴𝗲𝗿 ◆━━━━━━━━◆  

✦ 𝗪𝗲𝗹𝗰𝗼𝗺𝗲!  
┗• This bot helps you manage & automate your marketplace operations.  
┗• Schedule announcements, broadcast messages, and stay in control.  

✦ 𝗙𝗲𝗮𝘁𝘂𝗿𝗲𝘀  
┣• Auto-scheduled messages to groups & channels  
┣• Instant broadcasting with Markdown formatting  
┣• Chat folder-based management for easy control  
┗• Secure & Owner-controlled commands  

✦ 𝗨𝘀𝗮𝗴𝗲  
┣• /help - View available commands  
┗• Support: [Alcyone Support](https://t.me/AlcyoneSupport)  

◆━━━━━━━━━━━━━━━━━━━━◆  
⚡ Let's get started!""",
        reply_markup=buttons
    )


# ✅ **Help Command**
@app.on_message(filters.command("help") & filters.user(OWNER_ID))
async def help_command(client, message):
    help_text = """
**📌 Available Commands:**
- `/set` (reply to message) → Set message for scheduling
- `/setdelay 1m` → Set delay (1m = 1 minute, 1h = 1 hour, max 24h)
- `/broadcast` (reply to message) → Send broadcast to all groups
- `/feedback` → Contact support
- `/addlink chat_folder_link` → Add chat folder link for broadcasts
"""
    await message.reply(help_text, parse_mode="markdown")


# ✅ **Set Scheduled Message**
@app.on_message(filters.command("set") & filters.reply & filters.user(OWNER_ID))
async def set_scheduled_message(client, message):
    msg_id = message.reply_to_message.message_id
    chat_id = message.chat.id

    settings.update_one({"owner_id": OWNER_ID}, {"$set": {"msg_id": msg_id, "chat_id": chat_id}}, upsert=True)
    await message.reply("✅ **Message has been set for scheduling!**", parse_mode="markdown")


# ✅ **Set Delay**
@app.on_message(filters.command("setdelay") & filters.user(OWNER_ID))
async def set_delay(client, message):
    if len(message.command) < 2:
        return await message.reply("**Usage:** `/setdelay 1m` or `/setdelay 1h` (max 24h)", parse_mode="markdown")

    delay_str = message.command[1]
    if delay_str.endswith("m"):
        delay = int(delay_str[:-1]) * 60
    elif delay_str.endswith("h"):
        delay = int(delay_str[:-1]) * 3600
    else:
        return await message.reply("❌ **Invalid format!** Use `1m` (minutes) or `1h` (hours).", parse_mode="markdown")

    if delay < 60 or delay > 86400:
        return await message.reply("❌ **Delay must be between 1 minute and 24 hours!**", parse_mode="markdown")

    settings.update_one({"owner_id": OWNER_ID}, {"$set": {"delay": delay}}, upsert=True)
    await message.reply(f"✅ **Delay set to `{delay_str}`!**", parse_mode="markdown")


# ✅ **Scheduled Message Task**
async def scheduled_messages():
    while True:
        data = settings.find_one({"owner_id": OWNER_ID})
        if data and "msg_id" in data and "delay" in data:
            msg_id = data["msg_id"]
            delay = data["delay"]
            chat_id = data["chat_id"]

            for group in groups.find():
                try:
                    await app.forward_messages(chat_id=group["chat_id"], from_chat_id=chat_id, message_ids=msg_id)
                    print(f"✅ Scheduled message sent to {group['title']}")
                except Exception as e:
                    print(f"❌ Failed: {e}")

            await asyncio.sleep(delay)
        else:
            await asyncio.sleep(60)  # No delay set, check again in 1 min


# ✅ **Broadcast Command**
@app.on_message(filters.command("broadcast") & filters.reply & filters.user(OWNER_ID))
async def broadcast(client, message):
    msg_id = message.reply_to_message.message_id
    chat_id = message.chat.id

    success, failed = 0, 0
    start_time = time.time()

    for group in groups.find():
        try:
            await app.forward_messages(chat_id=group["chat_id"], from_chat_id=chat_id, message_ids=msg_id)
            success += 1
        except:
            failed += 1

    end_time = time.time()
    taken = round(end_time - start_time, 2)

    await message.reply(
        f"✅ **Broadcast Complete!**\n\n📌 **Success:** `{success}`\n❌ **Failed:** `{failed}`\n⏳ **Time Taken:** `{taken}s`",
        parse_mode="markdown"
    )


# ✅ **Feedback Command**
@app.on_message(filters.command("feedback") & filters.user(OWNER_ID))
async def feedback(client, message):
    await message.reply("📩 **For queries, contact [Alcyone Support](https://t.me/AlcyoneSupport)**", parse_mode="markdown")


# ✅ **Add Chat Folder Link**
@app.on_message(filters.command("addlink") & filters.user(OWNER_ID))
async def add_chat_folder(client, message):
    if len(message.command) < 2:
        return await message.reply("**Usage:** `/addlink chat_folder_link`", parse_mode="markdown")

    link = message.command[1]
    chat_links.insert_one({"link": link})
    await message.reply("✅ **Chat folder link added!**", parse_mode="markdown")


# ✅ **Bot Startup Task**
async def main():
    await app.start()
    print("Bot is running!")
    asyncio.create_task(scheduled_messages())  # Start scheduled messages task
    await idle()


# ✅ **Run Bot**
if __name__ == "__main__":
    import asyncio
    from pyrogram import idle
    asyncio.run(main())
