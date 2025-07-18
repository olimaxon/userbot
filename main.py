from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import os
import json
from datetime import datetime

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])

DOWNLOAD_FOLDER = "downloads"
CONFIG_FILE = "config.json"
SENT_FILE = "sent_files.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"active": True}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def load_sent_files():
    if not os.path.exists(SENT_FILE):
        return []
    with open(SENT_FILE, "r") as f:
        return json.load(f)

def save_sent_files(sent_files):
    with open(SENT_FILE, "w") as f:
        json.dump(sent_files, f)

config = load_config()
sent_files = load_sent_files()
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
userbot = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=os.environ["SESSION_STRING"])

def get_main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Включить", callback_data="on"),
            InlineKeyboardButton("⛔ Выключить", callback_data="off"),
        ],
        [
            InlineKeyboardButton("📂 Показать файлы", callback_data="list_files"),
            InlineKeyboardButton("🔄 Обновить список", callback_data="refresh"),
        ]
    ])

def get_file_keyboard(filename):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🗑 Удалить {filename}", callback_data=f"delete:{filename})")]
    ])

@bot.on_message(filters.command("start") & filters.user(ADMIN_ID))
async def start_panel(client, message):
    await message.reply("🎛 Управление ботом:", reply_markup=get_main_keyboard())

@bot.on_callback_query(filters.user(ADMIN_ID))
async def handle_buttons(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    if data == "on":
        config["active"] = True
        save_config(config)
        await callback_query.message.edit_text("✅ Бот включён.", reply_markup=get_main_keyboard())
    elif data == "off":
        config["active"] = False
        save_config(config)
        await callback_query.message.edit_text("⛔ Бот выключен.", reply_markup=get_main_keyboard())
    elif data == "list_files":
        files = os.listdir(DOWNLOAD_FOLDER)
        if not files:
            await callback_query.message.reply("📁 Папка пуста.")
        else:
            for file in files:
                await callback_query.message.reply_document(
                    document=os.path.join(DOWNLOAD_FOLDER, file),
                    caption=f"📄 {file}",
                    reply_markup=get_file_keyboard(file)
                )
    elif data.startswith("delete:"):
        filename = data.split(":", 1)[1]
        path = os.path.join(DOWNLOAD_FOLDER, filename)
        if os.path.exists(path):
            os.remove(path)
            if filename in sent_files:
                sent_files.remove(filename)
                save_sent_files(sent_files)
            await callback_query.message.edit_text(f"🗑 Файл {filename} удалён.")
        else:
            await callback_query.message.edit_text("❌ Файл не найден.")
    elif data == "refresh":
        await callback_query.message.edit_text("🎛 Управление ботом (обновлено):", reply_markup=get_main_keyboard())

@userbot.on_message(filters.private & filters.media)
async def handle_media(client, message):
    if not config.get("active", True):
        return
    try:
        file_path = await message.download(file_name=f"{DOWNLOAD_FOLDER}/")
        filename = os.path.basename(file_path)
        print(f"📥 ЗАГРУЖЕНО: {file_path}")

        if filename not in sent_files:
            user = message.from_user
            name = user.first_name or ""
            username = f"@{user.username}" if user.username else ""
            user_id = user.id
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            caption = (
                f"🆕 НОВЫЙ ФАЙЛ: {filename}\n"
                f"👤 Отправил: {name} {username} (ID: {user_id})\n"
                f"📅 Дата: {now}"
            )
            await bot.send_document(
                chat_id=ADMIN_ID,
                document=file_path,
                caption=caption,
                reply_markup=get_file_keyboard(filename)
            )
            sent_files.append(filename)
            save_sent_files(sent_files)
            print(f"📤 ОТПРАВЛЕНО: {file_path}")
        else:
            print(f"⚠️ ФАЙЛ УЖЕ ОТПРАВЛЕН: {filename}")
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")

if __name__ == "__main__":
    bot.start()
    userbot.run()