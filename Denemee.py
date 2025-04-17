import telebot
from telebot import types
import json
import os
import random
import datetime

TOKEN = "BOT_TOKENINIZI_BURAYA_YAPISTIRIN"
ADMIN_ID = 123456789  # Kendi Telegram ID'nizi buraya yazın

bot = telebot.TeleBot(TOKEN)

# ---- DİL SİSTEMİ ----
user_langs = {}

# ---- ÜYELİKLER ----
memberships = {
    "daily": 1,
    "weekly": 7,
    "monthly": 30,
    "yearly": 365,
    "lifetime": 9999
}

prices = {
    "daily": 1,
    "weekly": 3,
    "monthly": 7,
    "yearly": 20,
    "lifetime": 30
}

user_data_file = "users.json"
payment_file = "payments.json"

# 1000+ sahte profil otomatik oluştur
fake_profiles = [f"@fakeuser{i}" for i in range(1, 1001)]

def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(default, f)
    with open(path) as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def load_users(): return load_json(user_data_file, {})
def save_users(data): save_json(user_data_file, data)

def load_payments(): return load_json(payment_file, {})
def save_payments(data): save_json(payment_file, data)

def get_lang(uid):
    return user_langs.get(uid, "tr")

def translate(uid, tr, en):
    return tr if get_lang(uid) == "tr" else en

# ---- BAŞLANGIÇ ----
@bot.message_handler(commands=["start"])
def start(message):
    uid = str(message.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("\ud83c\uddf9\ud83c\uddf7 Türkçe", "\ud83c\uddec\ud83c\udde7 English")
    bot.send_message(message.chat.id, "\ud83c\udf0d Lütfen dil seçin / Please choose language", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["\ud83c\uddf9\ud83c\uddf7 Türkçe", "\ud83c\uddec\ud83c\udde7 English"])
def lang_select(message):
    uid = str(message.from_user.id)
    user_langs[uid] = "tr" if "Türkçe" in message.text else "en"
    bot.send_message(message.chat.id, translate(uid, "✅ Dil ayarlandı!", "✅ Language set!"), reply_markup=main_menu(uid))

def main_menu(uid):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(translate(uid, "\ud83d\udcf8 Stalkla", "\ud83d\udcf8 Stalk"), translate(uid, "\ud83d\udcb3 Üyelik", "\ud83d\udcb3 Membership"))
    return markup

# ---- SAHTE PROFİLLER ----
@bot.message_handler(func=lambda m: m.text in ["\ud83d\udcf8 Stalkla", "\ud83d\udcf8 Stalk"])
def stalk_handler(message):
    uid = str(message.from_user.id)
    users = load_users()

    if uid not in users:
        users[uid] = {
            "queries": 0,
            "membership_end": None,
            "used_profiles": []
        }

    def has_membership():
        end = users[uid]["membership_end"]
        if end is None:
            return False
        return datetime.datetime.now() < datetime.datetime.strptime(end, "%Y-%m-%d")

    if users[uid]["queries"] >= 1 and not has_membership():
        return bot.send_message(message.chat.id, translate(uid, "❌ Üyelik gerekli. /üyelik", "❌ Membership required. Use /membership"))

    unused = [p for p in fake_profiles if p not in users[uid]["used_profiles"]]
    if not unused:
        return bot.send_message(message.chat.id, translate(uid, "✅ Tüm profilleri gördün!", "✅ You’ve seen all profiles!"))

    profile = random.choice(unused)
    users[uid]["used_profiles"].append(profile)
    users[uid]["queries"] += 1
    save_users(users)

    bot.send_message(message.chat.id, f"\ud83d\udc64 {profile}")

# ---- ÜYELİK ----
@bot.message_handler(commands=["üyelik", "membership"])
@bot.message_handler(func=lambda m: m.text in ["\ud83d\udcb3 Üyelik", "\ud83d\udcb3 Membership"])
def membership_handler(message):
    uid = str(message.from_user.id)
    payments = load_payments()
    lang = get_lang(uid)

    msg = "\ud83d\udcb3 Üyelik Planları:\n" if lang == "tr" else "\ud83d\udcb3 Membership Plans:\n"
    for k, days in memberships.items():
        plan_name = {
            "daily": "Günlük", "weekly": "Haftalık",
            "monthly": "Aylık", "yearly": "Yıllık", "lifetime": "Ömür Boyu"
        }[k] if lang == "tr" else k.capitalize()
        msg += f"• {plan_name}: ${prices[k]}\n"

    msg += "\n" + ("\ud83d\udccc Ödeme yöntemleri:\n" if lang == "tr" else "\ud83d\udccc Payment methods:\n")
    for k, v in payments.items():
        msg += f"• {k.title()}: `{v}`\n"

    msg += "\n" + ("\ud83d\udd01 Açıklamaya Telegram kullanıcı adını yaz!" if lang == "tr" else "\ud83d\udd01 Add your Telegram username in description.")
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

# ---- ADMIN PANELİ ----
@bot.message_handler(commands=["odeme_ekle"])
def admin_add_payment(message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split(maxsplit=2)
    if len(args) < 3: return bot.send_message(message.chat.id, "Kullanım: /odeme_ekle <tür> <bilgi>")
    data = load_payments()
    data[args[1].lower()] = args[2]
    save_payments(data)
    bot.send_message(message.chat.id, f"✅ {args[1].title()} eklendi!")

@bot.message_handler(commands=["odeme_sil"])
def admin_del_payment(message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2: return bot.send_message(message.chat.id, "Kullanım: /odeme_sil <tür>")
    data = load_payments()
    removed = data.pop(args[1].lower(), None)
    save_payments(data)
    bot.send_message(message.chat.id, f"🗑 {args[1].title()} silindi!" if removed else "Bulunamadı.")

@bot.message_handler(commands=["odeme_list"])
def admin_list_payment(message):
    if message.from_user.id != ADMIN_ID: return
    data = load_payments()
    if not data: return bot.send_message(message.chat.id, "📭 Hiç ödeme yöntemi yok.")
    msg = "💳 Mevcut ödeme yöntemleri:\n"
    for k, v in data.items():
        msg += f"• {k.title()}: `{v}`\n"
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

# ---- BOTU BAŞLAT ----
print("Bot çalışıyor...")
bot.polling()
