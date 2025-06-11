import telebot
import requests
import random
import os

# 🔐 টোকেন Environment Variable থেকে পড়া হবে
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

user_data = {}
CHANNEL_ID = "@METHOD_VAl"
GROUP_ID = "@METHOD_VAI_Support"

def generate_credentials():
    uid = str(random.randint(1000, 9999))
    email = f"user{uid}@auto.com"
    password = f"pass{uid}"
    return email, password

def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("/register", "/login")
    markup.row("/login_manually", "/me")
    markup.row("/bind", "/check")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id

    commands = [
        telebot.types.BotCommand("register", "একাউন্ট রেজিস্টার করুন"),
        telebot.types.BotCommand("login", "অটো লগইন করুন"),
        telebot.types.BotCommand("login_manually", "ম্যানুয়ালি লগইন করুন"),
        telebot.types.BotCommand("bind", "নতুন WhatsApp bind করুন"),
        telebot.types.BotCommand("check", "Bind করা নম্বর দেখুন"),
        telebot.types.BotCommand("me", "আপনার একাউন্ট তথ্য")
    ]
    bot.set_my_commands(commands)

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_ID[1:]}"),
        telebot.types.InlineKeyboardButton("💬 Join Group", url=f"https://t.me/{GROUP_ID[1:]}")
    )
    markup.add(telebot.types.InlineKeyboardButton("✅ JOINED", callback_data="joined"))
    bot.send_message(chat_id, "🚫 আগে নিচের চ্যানেল এবং গ্রুপে জয়েন করুন তারপর Access পাবেন:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "joined")
def joined_check(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    try:
        channel_status = bot.get_chat_member(CHANNEL_ID, user_id).status
        group_status = bot.get_chat_member(GROUP_ID, user_id).status

        if channel_status in ["member", "administrator", "creator"] and \
           group_status in ["member", "administrator", "creator"]:
            bot.send_message(chat_id, "✅ Access Granted! নিচের মেনু থেকে অপশন নির্বাচন করুন।", reply_markup=main_menu())
        else:
            bot.send_message(chat_id, "❌ আপনি এখনো চ্যানেল এবং গ্রুপে জয়েন করেননি।")
    except:
        bot.send_message(chat_id, "⚠️ বট চ্যানেল/গ্রুপে অ্যাডমিন নয় অথবা কোনো ত্রুটি হয়েছে।")

@bot.message_handler(commands=['register'])
def register(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "🎁 আপনার রেফার কোড দিন:")
    bot.register_next_step_handler(message, handle_referral)

def handle_referral(message):
    chat_id = message.chat.id
    promo_code = message.text.strip()

    email, password = generate_credentials()
    data = {
        "email": email,
        "password": password,
        "confirmPassword": password,
        "promo_code": promo_code,
        "source": None
    }

    r = requests.post("https://api.balama.vip/h5/taskBase/biz3/register", json=data)
    res = r.json()

    if res.get("code") == 0:
        user_data[chat_id] = {"email": email, "password": password}
        bot.send_message(chat_id, f"✅ রেজিস্ট্রেশন সফল!\n\n🆔 Email: `{email}`\n🔐 Password: `{password}`\n🎁 Promo Code: `{promo_code}`\n\n➡️ এখন `/login` দিন", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, f"❌ রেজিস্ট্রেশন ব্যর্থ: {res.get('msg')}")

@bot.message_handler(commands=['login'])
def login(message):
    chat_id = message.chat.id
    creds = user_data.get(chat_id)

    if not creds:
        bot.send_message(chat_id, "❗আপনি আগে `/register` করেননি।")
        return

    payload = {
        "email": creds["email"],
        "password": creds["password"],
        "country_phone_code": "1"
    }

    r = requests.post("https://api.balama.vip/h5/taskBase/login", json=payload)
    res = r.json()

    if res.get("code") == 0:
        token = res['data']['token']
        user_data[chat_id]["token"] = token
        bot.send_message(chat_id, f"✅ লগইন সফল!\n\n🔐 Token:\n`{token}`", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, f"❌ লগইন ব্যর্থ: {res.get('msg')}")

@bot.message_handler(commands=['login_manually'])
def ask_login(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "📧 আপনার ইমেইল দিন:")
    bot.register_next_step_handler(message, get_email)

def get_email(message):
    chat_id = message.chat.id
    email = message.text.strip()
    bot.send_message(chat_id, "🔐 আপনার পাসওয়ার্ড দিন:")
    bot.register_next_step_handler(message, get_password, email)

def get_password(message, email):
    chat_id = message.chat.id
    password = message.text.strip()

    payload = {
        "email": email,
        "password": password,
        "country_phone_code": "1"
    }

    r = requests.post("https://api.balama.vip/h5/taskBase/login", json=payload)
    res = r.json()

    if res.get("code") == 0:
        token = res['data']['token']
        user_data[chat_id] = {
            "email": email,
            "password": password,
            "token": token
        }
        bot.send_message(chat_id, f"✅ ম্যানুয়াল লগইন সফল!\n\n🔐 Token:\n`{token}`", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, f"❌ লগইন ব্যর্থ: {res.get('msg')}")

@bot.message_handler(commands=['bind'])
def bind(message):
    chat_id = message.chat.id
    info = user_data.get(chat_id)

    if not info or "token" not in info:
        bot.send_message(chat_id, "❌ আগে লগইন করুন `/login` অথবা `/login_manually` দিয়ে।")
        return

    bot.send_message(chat_id, "📱 আপনার WhatsApp নম্বর দিন (country code সহ):")
    bot.register_next_step_handler(message, handle_bind_phone)

def handle_bind_phone(message):
    chat_id = message.chat.id
    phone = message.text.strip()
    info = user_data.get(chat_id)

    if not info or "token" not in info:
        bot.send_message(chat_id, "❌ টোকেন খুঁজে পাওয়া যায়নি। আগে লগইন করুন।")
        return

    uuid = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz1234567890', k=16))
    user_data[chat_id]['uuid'] = uuid
    user_data[chat_id]['phone'] = phone

    headers = {
        "x-token": info['token']
    }

    body = {
        "uuid": uuid,
        "phone": phone
    }

    r = requests.post("https://api.balama.vip/h5/taskUser/phoneCode", json=body, headers=headers)
    res = r.json()

    if res.get("code") == 0:
        code = res['data']['phone_code']
        bot.send_message(chat_id, f"📶 Bind কোড: `{code}`", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, f"❌ Bind ব্যর্থ: {res.get('msg')}")

@bot.message_handler(commands=['check'])
def check_bind_status(message):
    chat_id = message.chat.id
    info = user_data.get(chat_id)

    if not info or "token" not in info:
        bot.send_message(chat_id, "❌ আগে লগইন করুন `/login` অথবা `/login_manually` দিয়ে।")
        return

    headers = {
        "x-token": info["token"]
    }

    r = requests.get("https://api.balama.vip/h5/taskUser/bindWsList", headers=headers)
    res = r.json()

    if res.get("code") == 0 and res["data"]:
        numbers = [f"✅ {entry['whatsapp']}" for entry in res["data"]]
        bot.send_message(chat_id, "🔗 Bind করা WhatsApp নম্বর:\n" + "\n".join(numbers))
    else:
        bot.send_message(chat_id, "❌ কোনো Bind নম্বর পাওয়া যায়নি।")

@bot.message_handler(commands=['me'])
def show_info(message):
    chat_id = message.chat.id
    info = user_data.get(chat_id)

    if not info:
        bot.send_message(chat_id, "❌ কোনো একাউন্ট তথ্য নেই। আগে `/register` অথবা `/login_manually` করুন।")
        return

    email = info.get("email")
    password = info.get("password")
    token = info.get("token", "❌ Not logged in")

    bot.send_message(chat_id, f"🧾 আপনার একাউন্ট তথ্য:\n\n🆔 Email: `{email}`\n🔐 Password: `{password}`\n\n📲 Token:\n`{token}`", parse_mode="Markdown")

# ▶️ Start polling
bot.polling()