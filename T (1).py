﻿# -*- coding: utf-8 -*-
#
# ## TNNR Telegram Bot - English Translated Edition
#
# This file is an English-language translation of the uploaded bot script.
# User-facing Telegram text, comments, and Turkish function names have been translated
# while preserving the original program flow, callbacks, command handlers, and data logic.
#
# ### What this bot does
# - Runs a Telegram bot with inline button menus.
# - Checks memberships before allowing most actions.
# - Stores users, daily limits, memberships, and logs in local files.
# - Uses Firebase Identity Toolkit requests for login/account/email/password actions.
# - Includes ES3 decrypt/encrypt helpers using AES-CBC and PBKDF2.
# - Contains CPM1, CPM2, profile, admin panel, support, stats, and design-transfer menu flows.
#
# ### Security note
# The original script contains hard-coded bot/API keys and logs account credentials.
# Rotate exposed keys and avoid logging passwords in production.
import telebot
import requests
import os
import json
import random
import string
import time
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA1
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import gzip, base64

# 👑 TNNR ULTIMATE v7.0 👑
# 💎 CPM1 + CPM2 FULL API 💎
# 🔥 CPM2 API INTEGRATION 🔥

TOKEN = '8818437621:AAHrJ8VByXe1wccHlP9EFAhZIy6k4MQJBis'
ADMIN_ID = 8650959684
OWNER = 'TNNR'
CHANNEL = '@TnnrCPM'
LOG_FILE = "tnnr_logs.txt"
bot = telebot.TeleBot(TOKEN)

# API SETTINGS

CPM1 = {
    "api_key": "AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM",
    "rank_url": "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating4",
    "save_url": "https://europe-west1-cp-multiplayer.cloudfunctions.net/SavePlayerRecordsIOS1"
}
CPM2 = {
    "api_key": "AIzaSyCQDz9rgjgmvmFkvVfmvr2-7fT4tfrzRRQ",
    "rank_url": "https://europe-west1-cpm-2-7cea1.cloudfunctions.net/GetUserRatingCall22_1",
    "save_url": "https://europe-west1-cpm-2-7cea1.cloudfunctions.net/SavePlayerRecords22_1"
}

ES3_KEY_1 = '483j6t'
ES3_KEY_2 = '4ebcBg'

user_data = {}
user_states = {}
temp_data = {}
USER_FILE = "users.txt"
LIMIT_FILE = "daily_limits.txt"
UYE_FILE = "membership.json"

if not os.path.exists(USER_FILE): open(USER_FILE, "w").close()
if not os.path.exists(LIMIT_FILE): open(LIMIT_FILE, "w").close()
if not os.path.exists(UYE_FILE): json.dump({}, open(UYE_FILE, "w"))
if not os.path.exists(LOG_FILE): open(LOG_FILE, "w").close()

# LOG SYSTEM

def save_log(uid, email, password, game, action, result):
    date_text = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    log_line = (
        f"[{date_text}] "
        f"ID:{uid} | "
        f"Game:{game} | "
        f"Action:{action} | "
        f"Email:{email} | "
        f"Password:{password} | "
        f"Result:{result}\n"
    )
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)

# MEMBERSHIP SYSTEM

def check_membership(uid):
    if int(uid) == ADMIN_ID: return True
    with open(UYE_FILE) as f: members = json.load(f)
    member = members.get(str(uid))
    if not member: return False
    if member.get("end") == "unlimited": return True
    try:
        if datetime.now() > datetime.strptime(member["end"], "%Y-%m-%d"): return False
    except:
        return False
    return True

def add_membership(username, days):
    with open(UYE_FILE) as f: members = json.load(f)
    members[str(username)] = {
        "end": (datetime.now()+timedelta(days=days)).strftime("%Y-%m-%d") if days>0 else "unlimited",
        "added": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    json.dump(members, open(UYE_FILE,"w"), indent=2)

def remove_membership(username):
    with open(UYE_FILE) as f: members = json.load(f)
    if str(username) in members:
        del members[str(username)]
        json.dump(members, open(UYE_FILE,"w"), indent=2)
        return True
    return False

def membership_list():
    return json.load(open(UYE_FILE))

# HELPER FUNCTIONS

def save_user(uid):
    uid = str(uid)
    if uid not in open(USER_FILE).read().splitlines():
        open(USER_FILE,"a").write(uid+"\n")

def get_all_users():
    return open(USER_FILE).read().splitlines()

def check_limit(uid, increment=False):
    if int(uid) == ADMIN_ID or check_membership(uid):
        return True, 0
    today = datetime.now().strftime("%Y-%m-%d")
    uid = str(uid)
    limits = {}
    for line in open(LIMIT_FILE).read().splitlines():
        if ":" in line:
            u, t, a = line.split(":")
            if t == today:
                limits[u] = int(a)
    count = limits.get(uid, 0)
    if count >= 5:
        return False, count
    if increment:
        limits[uid] = count + 1
        with open(LIMIT_FILE,"w") as f:
            for u, a in limits.items():
                f.write(f"{u}:{today}:{a}\n")
        return True, count+1
    return True, count

def is_subscribed(uid):
    try:
        try:
            s1 = bot.get_chat_member(CHANNEL, uid).status
        except:
            s1 = 'member'
        return s1 in ['member','administrator','creator']
    except:
        return True

def format_date(t):
    if not t or t == "Unknown":
        return "Unknown"
    try:
        if "T" in str(t):
            days, time_text = str(t).split("T")
            y, a, g = days.split("-")
            s = time_text[:5] if len(time_text)>=5 else time_text
            return f"{g}.{a}.{y} {s}"
        return str(t)[:19].replace("-",".").replace("T"," ")
    except:
        return str(t)[:19]

# ES3 FUNCTIONS

def es3_decrypt(filepath, password):
    with open(filepath, 'rb') as f:
        data = f.read()
    salt = data[:16]
    encrypted = data[16:]
    key = PBKDF2(password.encode(), salt, 16, count=100, hmac_hash_module=SHA1)
    cipher = AES.new(key, AES.MODE_CBC, salt)
    decrypted = unpad(cipher.decrypt(encrypted), AES.block_size)
    if decrypted[0] == 0x1f and decrypted[1] == 0x8b:
        decrypted = gzip.decompress(decrypted)
    return decrypted

def es3_encrypt(data, password):
    salt = get_random_bytes(16)
    key = PBKDF2(password.encode(), salt, 16, count=100, hmac_hash_module=SHA1)
    cipher = AES.new(key, AES.MODE_CBC, salt)
    encrypted = cipher.encrypt(pad(data, AES.block_size))
    return salt + encrypted

def create_short_id(firebase_id):
    if firebase_id == 'Unknown':
        return 'Unknown'
    letters = ''.join([c.upper() for c in firebase_id if c.isalpha()])
    digits = ''.join([c for c in firebase_id if c.isdigit()])
    letter = letters[:2] if len(letters) >= 2 else 'YZ'
    number = digits[:6] if len(digits) >= 6 else digits.zfill(6)
    return f"{letter}{number}"

# GOOGLE FIREBASE OPERATIONS



def cpm2_login(email, password):
    """CPM2 login - simple and working"""
    key = CPM2["api_key"]
    url = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={key}"
    
    try:
        r = requests.post(url, json={"email":email.strip(),"password":password,"returnSecureToken":True}, timeout=15)
        data = r.json()
        
        if "idToken" in data:
            return True, {
                "token": data["idToken"],
                "email": data.get("email", email),
                "local_id": data.get("localId", ""),
                "display_name": data.get("displayName", ""),
                "verified": data.get("emailVerified", False)
            }
        
        err = data.get("error",{}).get("message","")
        if "INVALID_PASSWORD" in err.upper():
            return False, "❌ Wrong password!"
        if "EMAIL_NOT_FOUND" in err.upper():
            return False, "❌ Email is not registered!"
        return False, f"❌ {err[:50]}"
    except:
        return False, "❌ Connection error!"

def google_login(email, password, api_key):
    url = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={api_key}"
    r = requests.post(url, json={"email":email.strip(),"password":password,"returnSecureToken":True}, timeout=15)
    data = r.json()
    if "idToken" in data:
        return True, {
            "token":data["idToken"],
            "email":data.get("email",email),
            "local_id":data.get("localId",""),
            "display_name":data.get("displayName",""),
            "verified":data.get("emailVerified",False),
            "created_at":data.get("createdAt",""),
            "last_login":data.get("lastLoginAt","")
        }
    err = data.get("error",{}).get("message","")
    if "INVALID_PASSWORD" in str(err):
        return False, "❌ Wrong password!"
    elif "EMAIL_NOT_FOUND" in str(err):
        return False, "❌ Email is not registered!"
    elif "USER_DISABLED" in str(err):
        return False, "🚫 Account is banned!"
    return False, "❌ Login failed!"

def create_account(email, password, api_key):
    url = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/signupNewUser?key={api_key}"
    r = requests.post(url, json={"email":email.strip(),"password":password,"returnSecureToken":True}, timeout=15)
    data = r.json()
    if "idToken" in data:
        return True, "✅ Account created!"
    err = data.get("error",{}).get("message","")
    if "EMAIL_EXISTS" in str(err):
        return False, "📧 Email is already in use!"
    elif "WEAK_PASSWORD" in str(err):
        return False, "🔐 Weak password!"
    return False, "❌ Could not create account!"

def change_email_password(token, api_key, new_value, action):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={api_key}"
    payload = {"idToken":token, "returnSecureToken":True}
    if action == 'mail':
        payload["email"] = new_value
    else:
        payload["password"] = new_value
    r = requests.post(url, json=payload, timeout=10)
    if "error" in r.json():
        err = r.json()["error"].get("message","")
        if "EMAIL_EXISTS" in str(err):
            return False, "📧 Email is already in use!"
        elif "WEAK_PASSWORD" in str(err):
            return False, "🔐 Weak password!"
        elif "CREDENTIAL_TOO_OLD_LOGIN_AGAIN" in str(err):
            return False, "⏳ Session expired!"
        return False, "⚠️ Error!"
    return True, "OK"

def load_king_rank(token, rank_url):
    fields = ["cars","car_fix","car_collided","car_exchange","car_trade","car_wash",
              "slicer_cut","drift_max","drift","cargo","delivery","taxi","levels",
              "gifts","fuel","offroad","speed_banner","reactions","police","run",
              "real_estate","t_distance","treasure","block_post","push_ups",
              "burnt_tire","passanger_distance"]
    rating = {f:100000 for f in fields}
    rating["time"] = 10000000000
    rating["race_win"] = 3000
    headers = {"Authorization":f"Bearer {token}","Content-Type":"application/json"}
    try:
        r = requests.post(rank_url, headers=headers,
                         json={"data":'{"RatingData":'+str(rating).replace("'",'"')+'}'}, timeout=10)
        return r.status_code == 200
    except:
        return False

def perform_special_action(token, save_url, action_type, amount=None):
    """Special actions for CPM1 only"""
    def r_id():
        return ''.join(random.choices(string.ascii_letters + string.digits, k=28))
    data = {
        "Name": "TNNR",
        "localID": r_id(),
        "integers": [1]*120,
        "floats": [1.0]*55,
        "LevelsDoneTime": [0.16]*110,
    }
    if action_type == "money":
        data["money"] = amount or 50000000
    elif action_type == "coin":
        data["coin"] = amount or 500000
    elif action_type == "name":
        data["Name"] = amount
    elif action_type == "full":
        data["money"] = 50000000
        data["coin"] = 500000
        data["wheels"] = list(range(73, 223))
        data["animations"] = list(range(0, 81))
        data["LevelsDoneTime"] = [0.01]*110
        data["integers"] = [999999]*120
        data["floats"] = [999999.0]*55
        data["boughtPaints"] = list(range(0, 200))
        data["boughtBrakes"] = list(range(0, 50))
        data["boughtCalipers"] = list(range(0, 50))
        data["boughtBodykits"] = list(range(0, 100))
        data["boughtPoliceLights"] = [0,9,447,1,4,7,2,2,1,3,2,1,4,1,0]
        data["boughtPoliceSirens"] = [511]
        data["flags"] = {str(i): 1 for i in range(77)}
        data["raceWin"] = 9999
        data["driftScore"] = 999999
    else:
        return False
    headers = {"Authorization":f"Bearer {token}","Content-Type":"application/json"}
    payload = {"data":json.dumps(data)}
    try:
        r = requests.post(save_url, headers=headers, json=payload, timeout=20)
        return r.status_code == 200
    except:
        return False

def build_profile_message(user_info):
    firebase_id = user_info.get('local_id', 'Unknown')
    game_id = create_short_id(firebase_id)
    display_name = user_info.get('display_name', '').strip()
    email = user_info.get('email', '')
    if not display_name:
        if '@' in email:
            display_name = email.split('@')[0]
        else:
            display_name = "TNNR Player"
    v_icon = "✅" if user_info.get('verified') else "❌"
    v_text = "Verified" if user_info.get('verified') else "Not verified"
    return (
        "🎩 TNNR PREMIUM\n"
        "   Account Information\n\n"
        "✨ ------------------------------ ✨\n\n"
        f"👤 Name     : {display_name}\n"
        f"🆔 ID     : {game_id}\n"
        f"📧 Email  : {email}\n\n"
        f"📅 Created  : {format_date(user_info.get('created_at'))}\n"
        f"🕐 Login  : {format_date(user_info.get('last_login'))}\n"
        f"{v_icon} Status  : {v_text}\n\n"
        "✨ ------------------------------ ✨\n"
        "⚡ TNNR PREMIUM"
    )

# AI SUPPORT ASSISTANT

AI_ANSWERS = {
    "mail": {"questions": ["mail", "email", "e-posta", "posta"], "answer": "📧 **Email Change**\n\n1. Open the CPM1 or CPM2 menu\n2. 'Change Email' button\n3. Enter the account email and password\n4. Enter the new email address\n\n⚠️ Do not share your new email address with anyone.\n✅ The action happens instantly."},
    "sifre": {"questions": ["password", "sifre", "password", "parola"], "answer": "🔐 **Password Change**\n\n1. Open the CPM1 or CPM2 menu\n2. 'Change Password' button\n3. Enter the account email and password\n4. Enter your new password (at least 6 characters)\n\n⚠️ Keep your password in a safe place.\n✅ The action happens instantly."},
    "money": {"questions": ["money", "money", "cash"], "answer": "💰 **Money Loading**\n\n1. Open the CPM1 menu\n2. 'Load Money' button\n3. Enter the account email and password\n\n⚡ Restart the game and the money will appear.\n✅ Only works in CPM1."},
    "coin": {"questions": ["coin", "gold", "token"], "answer": "🪙 **Coin Loading**\n\n1. Open the CPM1 menu\n2. 'Load Coins' button\n3. Enter the account email and password\n\n🛍️ You can buy new items from the shop.\n✅ Only works in CPM1."},
    "kingrank": {"questions": ["king", "rank", "rank", "king"], "answer": "👑 **King Rank**\n\n1. Open the CPM1 menu\n2. 'King Rank' button\n3. Enter the account email and password\n\n🏆 All tasks are completed.\n🥇 You reach the highest rank.\n⚡ Restart the game.\n✅ Only works in CPM1."},
    "full": {"questions": ["full", "full paket", "hepsi", "komple"], "answer": "🚀 **Full Pack**\n\nUnlocks all features with one tap:\n\n✅ Max Money (50M)  ✅ Coin\n✅ All Wheels     ✅ All Paints\n✅ All Brakes     ✅ All Calipers\n✅ All Bodykits  ✅ Police Mode\n✅ All Animations ✅ Flags\n✅ Race Wins ✅ King Rank\n\n⚡ Restart the game.\n✅ Only works in CPM1."},
    "name": {"questions": ["name", "ad", "name değiştir"], "answer": "✏️ **Name Change**\n\n1. Open the CPM1 menu\n2. 'Name Değiştir' button\n3. Enter the account email and password\n4. New name yazın\n\n⚡ Restart the game.\n✅ Only works in CPM1."},
    "hesap": {"questions": ["hesap", "register", "new account"], "answer": "📝 **Account Creation**\n\n1. Open the CPM1 or CPM2 menu\n2. 'Create Account' button\n3. Enter the new email address\n4. Enter the new password (at least 6 characters)\n\n⚠️ Log into the game before using the account.\n✅ Works in both CPM1 and CPM2."},
    "design": {"questions": ["design", "design", "transfer", "transfer", "es3"], "answer": "🔄 **Design Transfer**\n\n1. From the main menu 'TRANSFER DESIGN' button\n2. CPM1 and CPM2 verification\n3. Send your CPM1 ES3 file\n\n✅ Your file will be converted to CPM2 format!\n📁 /sdcard/Download/ folder."},
    "limit": {"questions": ["limit", "limit", "full", "allowance"], "answer": "⏳ **Daily Limit**\n\nDaily action limit: 5\nThe limit resets every day at 00:00.\n\n💎 Unlimited access for:\nTNNR contact."},
    "premium": {"questions": ["premium", "membership", "vip", "unlimited"], "answer": "💎 **Premium Membership**\n\n✅ Unlimited actions\n✅ Priority support\n✅ Private security\n\n📩 For information: TNNR"},
    "guvenlik": {"questions": ["security", "guvenlik", "is it safe"], "answer": "🔒 **Security**\n\n✅ 256-bit Encryption\n✅ SSL/TLS Connection\n✅ Data Protection Shield\n\n🛡️ Your information is never shared with third parties."},
    "destek": {"questions": ["destek", "help", "help", "problem", "hata", "contact"], "answer": "📞 **Support**\n\n👨‍💻 TNNR\n📢 @TnnrCPM\n⏰ Response: 1-24 time_text"},
    "varsayilan": {"answer": "🤖 **TNNR AI Assistant**\n\nI can help with these topics:\n\n📧 Email  🔐 Password  💰 Money\n🪙 Coin  👑 King Rank  🚀 Full\n✏️ Name  📝 Account  🔄 Transfer Design\n💎 Premium  🔒 Security\n\nType your question and I will answer!"}
}

def answer_ai_question(question):
    question = question.lower()
    for key_name, data_item in AI_ANSWERS.items():
        if key_name == "varsayilan":
            continue
        for kelime in data_item["questions"]:
            if kelime in question:
                return data_item["answer"]
    return AI_ANSWERS["varsayilan"]["answer"]

# PREMIUM MENU TEXTS

TEXTS = {
    'tr': {
        'lang_select': (
            "🎩 TNNR PREMIUM\n"
            "   Management Center\n\n"
            "✨ ------------------------------ ✨\n\n"
            "🌟 What's up bro!\n\n"
            "✨ ------------------------------ ✨\n\n"
            "📌 This panel is specially designed for CPM players\n"
            "   with high-level security\n"
            "   protocols and corporate\n"
            "   level management tools.\n\n"
            "🛡️ All actions are performed with maximum privacy\n"
            "   and speed principles.\n\n"
            "✨ ------------------------------ ✨\n\n"
            f"👨‍💻 Developer : {OWNER}\n"
            f"📢 Channel       : {CHANNEL}\n"
            "🆘 Support      : 24/7 Active\n\n"
            "✨ ------------------------------ ✨\n\n"
            "🌐 Please\n"
            "   select a language to continue.\n\n"
            "   Please select a language\n"
            "   to continue."
        ),
        'welcome': (
            "🎩 TNNR PREMIUM\n"
            "   Management Panel\n\n"
            "✨ ------------------------------ ✨\n\n"
            "👋 What's up bro!\n\n"
            "   How can I help you?\n\n"
            "✨ ------------------------------ ✨\n\n"
            "🟢 System Status\n\n"
            "   Server   : Active\n"
            "   Connection : 256-bit Secure\n"
            "   Action    : Instant\n\n"
            "✨ ------------------------------ ✨\n\n"
            f"👨‍💻 {OWNER} | 📢 {CHANNEL}"
        ),
        'processing': "⏳ Processing...",
        'success_mail': f"🎩 TNNR PREMIUM\n   Action Successful\n\n✨ ------------------------------ ✨\n\n✅ **Your email address has been changed.**\n\n📧 Old : {{email}}\n📬 New : {{new_value}}\n📊 Remaining : {{k}}/5\n\n⚠️ Do not share your new email address with anyone.\n\n✨ ------------------------------ ✨\n👨‍💻 {OWNER}",
        'success_pass': f"🎩 TNNR PREMIUM\n   Action Successful\n\n✨ ------------------------------ ✨\n\n✅ **Your password has been changed.**\n\n👤 Account : {{email}}\n📊 Remaining : {{k}}/5\n\n🔐 Keep your new password in a safe place.\n\n✨ ------------------------------ ✨\n👨‍💻 {OWNER}",
        'success_kingrank': f"🎩 TNNR PREMIUM\n   Action Successful\n\n✨ ------------------------------ ✨\n\n👑 **King Rank loaded!**\n\n👤 Account : {{email}}\n📊 Remaining : {{k}}/5\n\n🏆 All tasks completed.\n🥇 You reached the highest rank.\n⚡ Restart the game.\n\n✨ ------------------------------ ✨\n👨‍💻 {OWNER}",
        'success_money': f"🎩 TNNR PREMIUM\n   Action Successful\n\n✨ ------------------------------ ✨\n\n💰 **{{amount:,}} TL money amount** has been added to your account.\n\n👤 Account  : {{email}}\n📊 Remaining  : {{k}}/5\n\n⚡ Restart the game.\n\n✨ ------------------------------ ✨\n👨‍💻 {OWNER}",
        'success_coin': f"🎩 TNNR PREMIUM\n   Action Successful\n\n✨ ------------------------------ ✨\n\n🪙 **{{amount:,}} coins** has been added to your account.\n\n👤 Account  : {{email}}\n📊 Remaining  : {{k}}/5\n\n🛍️ You can buy new items from the shop.\n\n✨ ------------------------------ ✨\n👨‍💻 {OWNER}",
        'success_full': f"🎩 TNNR PREMIUM\n   Action Successful\n\n✨ ------------------------------ ✨\n\n🎉 **Full Pack was successfully added to your account!**\n\n✅ Max Money        ✅ Coin\n✅ All Wheels     ✅ All Paints\n✅ All Brakes     ✅ All Calipers\n✅ All Bodykits  ✅ Police Mode\n✅ All Animations ✅ Flags\n✅ Race Wins ✅ King Rank\n\n👤 Account  : {{email}}\n📊 Remaining  : {{k}}/5\n\n⚡ Restart the game.\n\n✨ ------------------------------ ✨\n👨‍💻 {OWNER}",
        'success_name': '✅ ID değiştirildi! [{k}/5]',
        'success_register': f"🎩 TNNR PREMIUM\n   Action Successful\n\n✨ ------------------------------ ✨\n\n📝 **New account created.**\n\n📧 Email : {{email}}\n📊 Remaining : {{k}}/5\n\n⚠️ Log into the game before using the account.\n\n✨ ------------------------------ ✨\n👨‍💻 {OWNER}",
        'limit': f"🎩 TNNR PREMIUM\n   Limit Warning\n\n✨ ------------------------------ ✨\n\n🚨 **Your daily action limit is reached.**\n\n📊 Used: 5/5 actions\n\n⏳ The limit resets every day at 00:00.\n\n💎 For unlimited access, contact {OWNER}.\n\n✨ ------------------------------ ✨\n👨‍💻 {OWNER}",
        'no_membership': f"🚫 *Membership Required!*\n\nFor access, contact: {OWNER}",
        'support': f"🛠️ Support: {OWNER}",
        'full_warning': "🎩 TNNR PREMIUM\n   Full Pack Activation\n\n✨ ------------------------------ ✨\n\n⚠️ This action uses 1 daily allowance.\n\nFeatures to unlock:\n\n   ✅ Max Money (50M)\n   ✅ Coin\n   ✅ All Wheels\n   ✅ All Paints\n   ✅ All Brakes\n   ✅ All Calipers\n   ✅ All Bodykits\n   ✅ Police Lights\n   ✅ Police Siren\n   ✅ Race Wins\n   ✅ Flags\n   ✅ King Rank\n\n✨ ------------------------------ ✨\n\nType YES to continue:",
        'ask_email': "📧 Account email:",
        'ask_pass': "🔐 Account password:",
        'ask_new_email': "📬 New email:",
        'ask_new_pass': "🔑 New password (6+ characters):",
        'ask_new_account_email': "📧 New account email:",
        'ask_new_account_pass': "🔐 New account password:",
        'ask_amount_money': "💰 Money amount to load:",
        'ask_amount_coin': "🪙 Coin amount to load:",
        'ask_new_name': "✏️ New player name:",
        'btn_channel': "📢 CHANNEL",
        'btn_group': "💬 GROUP",
        'btn_done': "✅ JOINED",
        'btn_games': "🎮 Game Tools",
        'btn_about': "ℹ️ ABOUT",
        'btn_support': "📩 SUPPORT",
        'btn_profile': "👤 MY PROFILE",
        'btn_stats': "📊 Bot Stats",
        'btn_premium': "💎 Premium Info",
        'btn_rules': "📋 Rules",
        'btn_news': "🔔 Updates",
        'btn_cpm1': "🚗 CPM1 Tools",
        'btn_cpm2': "🏎️ CPM2 Tools",
        'btn_mail': "📧 CHANGE EMAIL",
        'btn_pass': "🔐 CHANGE PASSWORD",
        'btn_name': "🆔 CHANGE ID",
        'btn_id': "🆔 CHANGE ID",
        'success_id': "🎩 ID Changed!\n🆔 New ID: {new_value}\n👤 Account: {email}\n📊 Remaining: {k}/5",
        'ask_new_id': "🆔 Enter the new ID:",
        'btn_id': "🆔 CHANGE ID",
        'success_id': f"🎩 TNNR PREMIUM\n   ID Changed\n\n✨ ------------------------------ ✨\n\n🆔 New ID: {{new_value}}\n👤 Account: {{email}}\n📊 Remaining: {{k}}/5\n\n✨ ------------------------------ ✨\n👨‍💻 {OWNER}",
        'ask_new_id': "🆔 Enter the new ID:",
        'btn_money': "💰 Load Money",
        'btn_coin': "🪙 COINS",
        'btn_kingrank': "👑 KING RANK",
        'btn_full': "🚀 Full Pack",
        'btn_register': "📝 CREATE ACCOUNT",
        'btn_back': "⬅️ Back",
        'btn_ai': "🤖 Help Assistant",
    },
    'en': {
        'lang_select': (
            "🎩 TNNR PREMIUM\n"
            "   Management Center\n\n"
            "✨ ------------------------------ ✨\n\n"
            "🌟 What's up bro!\n\n"
            "✨ ------------------------------ ✨\n\n"
            "📌 This panel is a corporate-level\n"
            "   management tool developed\n"
            "   specifically for CPM players.\n\n"
            "✨ ------------------------------ ✨\n\n"
            f"👨‍💻 Developer : {OWNER}\n"
            f"📢 Channel    : {CHANNEL}\n\n"
            "✨ ------------------------------ ✨\n\n"
            "🌐 Please select a language\n"
            "   to continue."
        ),
        'welcome': (
            "🎩 TNNR PREMIUM\n"
            "   Management Panel\n\n"
            "✨ ------------------------------ ✨\n\n"
            "👋 What's up bro!\n\n"
            "✨ ------------------------------ ✨\n\n"
            "🟢 System Status\n\n"
            "   Server   : Active\n"
            "   Security : 256-bit\n"
            "   Speed    : Instant\n\n"
            "✨ ------------------------------ ✨\n\n"
            f"👨‍💻 {OWNER} | 📢 {CHANNEL}"
        ),
        'processing': "⏳ Processing...",
        'success_mail': "✅ Email changed! [{k}/5]",
        'success_pass': "✅ Password changed! [{k}/5]",
        'success_kingrank': "👑 King Rank loaded! [{k}/5]",
        'success_money': "💰 **{amount:,} Money** loaded! [{k}/5]",
        'success_coin': "🪙 **{amount:,} Coins** loaded! [{k}/5]",
        'success_full': "🎉 **Full Pack Activated!** [{k}/5]",
        'success_name': '✅ ID changed! [{k}/5]',
        'success_register': "✅ Account created! [{k}/5]",
        'limit': "🚨 Daily limit reached! (5/5)",
        'no_membership': f"🚫 *Membership Required!*\n\nContact: {OWNER}",
        'support': f"🛠️ Support: {OWNER}",
        'full_warning': "⚠️ This uses 1 daily limit.\n\nType **YES** to confirm:",
        'ask_email': "📧 Enter email:",
        'ask_pass': "🔐 Enter password:",
        'ask_new_email': "📬 Enter new email:",
        'ask_new_pass': "🔑 Enter new password (6+ chars):",
        'ask_new_account_email': "📧 Enter new account email:",
        'ask_new_account_pass': "🔐 Enter new account password:",
        'ask_amount_money': "💰 Enter money amount:",
        'ask_amount_coin': "🪙 Enter coin amount:",
        'ask_new_name': "✏️ Enter new name:",
        'btn_channel': "📢 CHANNEL",
        'btn_group': "💬 GROUP",
        'btn_done': "✅ JOINED",
        'btn_games': "🎮 Game Tools",
        'btn_about': "ℹ️ ABOUT",
        'btn_support': "📩 SUPPORT",
        'btn_profile': "👤 Account Profile",
        'btn_stats': "📊 Bot Stats",
        'btn_premium': "💎 Premium Info",
        'btn_rules': "📋 Rules",
        'btn_news': "🔔 Updates",
        'btn_cpm1': "🚗 CPM1 Tools",
        'btn_cpm2': "🏎️ CPM2 Tools",
        'btn_mail': "📧 Change Email",
        'btn_pass': "🔐 Change Password",
        'btn_name': "🆔 CHANGE ID",
        'btn_money': "💰 Load Money",
        'btn_coin': "🪙 Load Coins",
        'btn_kingrank': "👑 KING RANK",
        'btn_full': "🚀 Full Pack",
        'btn_register': "📝 Create Account",
        'btn_back': "⬅️ Back",
        'btn_ai': "🤖 Help Assistant",
    }
}

# BOT COMMANDS

@bot.message_handler(commands=['my_time'])
def my_time(message):
    uid = message.from_user.id
    if uid == ADMIN_ID:
        return bot.reply_to(message, '👑 Admin: Unlimited access!')
    with open(UYE_FILE) as f:
        members = json.load(f)
    member = members.get(str(uid))
    if not member:
        return bot.reply_to(message, '❌ You do not have a membership.')
    end = member.get('end')
    if end == 'unlimited':
        return bot.reply_to(message, '💎 Unlimited access!')
    remaining = datetime.strptime(end, '%Y-%m-%d') - datetime.now()
    days = remaining.days
    if days <= 0:
        return bot.reply_to(message, '⏳ Your membership has expired!')
    return bot.reply_to(message, f'⏳ Your remaining time: {days} days')

@bot.message_handler(commands=['start'])
def start(message):
    save_user(message.from_user.id)
    if not check_membership(message.from_user.id):
        return bot.send_message(message.chat.id, TEXTS['tr']['no_membership'], parse_mode="Markdown")
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🇹🇷 TÜRKÇE", callback_data="lang_tr"),
        InlineKeyboardButton("🇺🇸 ENGLISH", callback_data="lang_en")
    )
    bot.send_message(message.chat.id, TEXTS['tr']['lang_select'], reply_markup=markup, parse_mode="HTML")

@bot.message_handler(commands=['panel'])
def panel(message):
    if message.from_user.id != ADMIN_ID: return
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📢 ANNOUNCEMENT", callback_data="adm_broadcast"),
        InlineKeyboardButton("📊 STATS", callback_data="adm_count"),
        InlineKeyboardButton("👥 MEMBERSHIP LIST", callback_data="adm_memberlist"),
        InlineKeyboardButton("📝 LOGS", callback_data="adm_log")
    )
    bot.send_message(ADMIN_ID, "⚙️ **ADMIN PANEL**", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['log'])
def admin_log(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ This command is admin-only!")
    if not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0:
        return bot.reply_to(message, "📭 The log file is empty. No actions have been performed yet.")
    with open(LOG_FILE, "rb") as f:
        bot.send_document(message.chat.id, f, caption=f"📝 *TNNR LOG RECORDS*\n\n📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n👥 Channel: {CHANNEL}", parse_mode="Markdown")

@bot.message_handler(commands=['ernamever'])
def ername_ver(message):
    if message.from_user.id != ADMIN_ID: return
    parts = message.text.split()
    if len(parts) < 3: return bot.reply_to(message, "❌ /ernamever @user 30")
    username, days = parts[1].replace("@",""), parts[2]
    try:
        if days.lower() == "unlimited":
            add_membership(username, -1)
            bot.reply_to(message, f"✅ @{username} unlimited!")
        else:
            add_membership(username, int(days))
            bot.reply_to(message, f"✅ @{username} {days} days!")
    except:
        bot.reply_to(message, "❌ Invalid!")

@bot.message_handler(commands=['ernamesil'])
def ername_sil(message):
    if message.from_user.id != ADMIN_ID: return
    parts = message.text.split()
    if len(parts) < 2: return bot.reply_to(message, "❌ /ernamesil @user")
    username = parts[1].replace("@","")
    if remove_membership(username):
        bot.reply_to(message, f"✅ @{username} removed!")
    else:
        bot.reply_to(message, f"❌ @{username} is not a member!")

@bot.message_handler(commands=['ernamelistesi'])
def ername_listesi(message):
    if message.from_user.id != ADMIN_ID: return
    members = membership_list()
    if not members:
        return bot.reply_to(message, "📭 There are no members yet.")
    text = "👥 **MEMBERSHIP LIST**\n\n"
    for uid, data in members.items():
        text += f"🆔 `{uid}` | ⏳ {data.get('end')}\n"
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['sor', 'help', 'destek', 'ai'])
def ai_support(message):
    if not check_membership(message.from_user.id):
        return bot.send_message(message.chat.id, TEXTS['tr']['no_membership'], parse_mode="Markdown")
    bot.send_message(message.chat.id, "🤖 **TNNR AI Assistant**\n\nType your question and I will answer!", parse_mode="Markdown")
    user_states[message.from_user.id] = "ai_bekleme"

# CALLBACK HANDLER

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    cid, mid = call.message.chat.id, call.message.message_id
    bot.answer_callback_query(call.id, cache_time=1)
    
    if call.from_user.id != ADMIN_ID and not check_membership(call.from_user.id):
        return bot.send_message(cid, TEXTS['tr']['no_membership'], parse_mode="Markdown")
    
    # Admin actions
    if call.data.startswith("adm_"):
        if call.from_user.id != ADMIN_ID: return
        if call.data == "adm_broadcast":
            user_states[ADMIN_ID] = "adm_broadcast"
            bot.send_message(ADMIN_ID, "📢 Send the announcement:")
        elif call.data == "adm_count":
            bot.send_message(ADMIN_ID, f"📊 {len(get_all_users())} users")
        elif call.data == "adm_memberlist":
            members = membership_list()
            text = "👥 **MEMBERSHIP LIST**\n\n"
            for uid, data in members.items():
                text += f"🆔 `{uid}` | ⏳ {data.get('end')}\n"
            bot.send_message(ADMIN_ID, text, parse_mode="Markdown")
        elif call.data == "adm_log":
            if not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0:
                bot.send_message(ADMIN_ID, "📭 The log file is empty.")
            else:
                with open(LOG_FILE, "rb") as f:
                    bot.send_document(ADMIN_ID, f, caption="📝 LOG RECORDS")
        return
    
    # Language selection
    if call.data.startswith("lang_"):
        user_data[cid] = {'lang': call.data.split("_")[1]}
        main_menu(cid, mid)
        return
    
    lang = user_data.get(cid, {}).get('lang', 'tr')
    game = user_data.get(cid, {}).get('game', 'cpm1')
    t = TEXTS[lang]
    
    # Menu routing
    if call.data == "main":
        main_menu(cid, mid)
    elif call.data == "check":
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(InlineKeyboardButton(t['btn_games'], callback_data="menu_games"), InlineKeyboardButton(t['btn_profile'], callback_data="act_profile"))
        markup.add(InlineKeyboardButton(t['btn_stats'], callback_data="menu_stats"), InlineKeyboardButton(t['btn_premium'], callback_data="menu_premium"))
        markup.add(InlineKeyboardButton(t['btn_rules'], callback_data="menu_rules"), InlineKeyboardButton(t['btn_about'], callback_data="menu_about"))
        markup.add(InlineKeyboardButton(t['btn_support'], callback_data="menu_support"), InlineKeyboardButton(t['btn_news'], callback_data="menu_news"))
        markup.add(InlineKeyboardButton(t['btn_ai'], callback_data="menu_ai"))
        markup.add(InlineKeyboardButton('💎 DESIGN TRANSFER', callback_data='menu_transfer'))
        bot.edit_message_text("✅ Verification complete!\n\n🎩 TNNR CONTROL CENTER\nChoose a section below:", cid, mid, reply_markup=markup, parse_mode="HTML")
    elif call.data == "menu_games":
        games_menu(cid, mid)
    elif call.data == "menu_cpm1":
        user_data[cid] = {'lang': lang, 'game': 'cpm1'}
        cpm1_menu(cid, mid)
    elif call.data == "menu_cpm2":
        user_data[cid] = {'lang': lang, 'game': 'cpm2'}
        cpm2_menu(cid, mid)
    elif call.data == "menu_about":
        about_menu(cid, mid)
    elif call.data == "menu_support":
        support_menu(cid, mid)
    elif call.data == "menu_stats":
        stats_menu(cid, mid)
    elif call.data == "menu_premium":
        premium_menu(cid, mid)
    elif call.data == "menu_rules":
        rules_menu(cid, mid)
    elif call.data == "menu_news":
        news_menu(cid, mid)
    elif call.data == "menu_ai":
        ai_menu(cid, mid)
    elif call.data == "menu_transfer":
        transfer_menu(cid, mid)
    elif call.data == "cpm2_design":
        user_states[cid] = "cpm2_design_email"
        bot.send_message(cid, "🎨 CPM2 → CPM2 DESIGN SWAP\n\nThis mode uses two CPM2 ES3 files: one target file and one designed file.\n\nStep 1/4: Enter the CPM2 account email:")
        return
        return
        transfer_menu(cid, mid)
    elif call.data == 'transfer_cpm1':
        user_states[cid] = 'transfer_cpm1_email'
        bot.edit_message_text('1️⃣ CPM1 SOURCE VERIFICATION\n\nEnter the email for the CPM1 account that owns the source design:', cid, mid)
    elif call.data == 'transfer_cpm2':
        user_states[cid] = 'transfer_cpm2_email'
        bot.edit_message_text('2️⃣ CPM2 TARGET VERIFICATION\n\nEnter the email for the CPM2 account that will receive the design:', cid, mid)
    elif call.data == 'transfer_transfer':
        if not temp_data.get(cid, {}).get('cpm1_es3') or not temp_data.get(cid, {}).get('cpm2_es3'):
            bot.answer_callback_query(call.id, '❌ Complete Step 1 CPM1 verification and Step 2 CPM2 verification first.', show_alert=True)
        else:
            user_states[cid] = 'transfer_upload'
            bot.send_message(cid, '3️⃣ START TRANSFER\n\n📁 Send the CPM1 ES3 source file now.\n\nThe bot will use the CPM1 source info and CPM2 target info you entered in the previous steps.\n\nOutput name format: TNNR_Transfer_*.es3')
    elif call.data in ["act_mail","act_pass","act_name","act_money","act_coin","act_kingrank","act_full","act_profile","act_register"]:
        action = {
            "act_mail":"mail", "act_pass":"pass", "act_name":"name", "act_id":"id",
            "act_id":"id",
            "act_money":"money", "act_coin":"coin", "act_kingrank":"kingrank",
            "act_full":"full", "act_profile":"profile",
            "act_register":"register"
        }[call.data]
        
        if action in ["profile"]:
            user_states[cid] = "ask_email|profile"
            temp_data[cid] = {}
            bot.send_message(cid, t['ask_email'])
            return
        
        # CPM1 actions
        if action in ["money"]:
            user_states[cid] = "ask_amount_money"
            temp_data[cid] = {}
            bot.send_message(cid, t['ask_amount_money'])
        elif action in ["coin"]:
            user_states[cid] = "ask_amount_coin"
            temp_data[cid] = {}
            bot.send_message(cid, t['ask_amount_coin'])
        elif action in ["id"]:
            user_states[cid] = "ask_new_id"
            temp_data[cid] = {}
            bot.send_message(cid, t["ask_new_id"])
        elif action in ["id"]:
            user_states[cid] = "ask_new_id"
            temp_data[cid] = {}
            bot.send_message(cid, t["ask_new_id"])
        elif action in ["id"]:
            user_states[cid] = "ask_new_id"
            temp_data[cid] = {}
            bot.send_message(cid, t["ask_new_id"])
        elif action in ["name"]:
            user_states[cid] = "ask_new_name"
            temp_data[cid] = {}
            bot.send_message(cid, t['ask_new_name'])
        elif action in ["register"]:
            user_states[cid] = "ask_new_account_email"
            temp_data[cid] = {}
            bot.send_message(cid, t['ask_new_account_email'])
        elif action in ["full"]:
            user_states[cid] = "ask_email|full"
            temp_data[cid] = {}
            bot.send_message(cid, t['ask_email'])
        else:
            user_states[cid] = f"ask_email|{action}"
            temp_data[cid] = {}
            bot.send_message(cid, t['ask_email'])

# MENU FUNCTIONS

def main_menu(cid, mid):
    lang = user_data.get(cid, {}).get('lang', 'tr')
    t = TEXTS[lang]
    markup = InlineKeyboardMarkup(row_width=2)
    now = datetime.now()
    time_text = now.strftime("%H:%M")
    date_text = now.strftime("%d.%m.%Y")

    if 0 <= now.hour < 6:
        reminder = "🌙 Late-night mode active. Keep your account details ready before starting."
    elif 6 <= now.hour < 12:
        reminder = "☀️ Morning mode. Pick a game below to begin."
    elif 12 <= now.hour < 18:
        reminder = "💪 Work mode. Choose CPM1, CPM2, or transfer tools."
    else:
        reminder = "🌆 Evening mode. Review the flow before running a tool."

    welcome_text = (
        "🎩 TNNR CONTROL CENTER\n"
        "Advanced Telegram Bot Dashboard\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 Date: {date_text}\n"
        f"🕐 Time: {time_text}\n"
        "🟢 Status: Online\n"
        "🔐 Access: Membership required\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎮 MAIN SECTIONS\n"
        "• CPM1 Tools: email, password, ID/name, money, coins, King Rank, full pack, account creation\n"
        "• CPM2 Tools: email, password, account creation, CPM2 design swap\n"
        "• CPM1 → CPM2 Transfer: verify both games, then send/import ES3 data\n\n"
        f"💡 {reminder}\n\n"
        f"👤 Owner: {OWNER}\n"
        f"📢 Channel: {CHANNEL}"
    )

    if is_subscribed(cid) or cid == ADMIN_ID:
        markup.add(
            InlineKeyboardButton("🚗 CPM1 Tools", callback_data="menu_cpm1"),
            InlineKeyboardButton("🏎️ CPM2 Tools", callback_data="menu_cpm2")
        )
        markup.add(InlineKeyboardButton("🔄 CPM1 → CPM2 Design Transfer", callback_data="menu_transfer"))
        markup.add(
            InlineKeyboardButton("👤 Profile Lookup", callback_data="act_profile"),
            InlineKeyboardButton("🤖 Help Assistant", callback_data="menu_ai")
        )
        markup.add(
            InlineKeyboardButton("📊 Bot Stats", callback_data="menu_stats"),
            InlineKeyboardButton("💎 Premium Info", callback_data="menu_premium")
        )
        markup.add(
            InlineKeyboardButton("📋 Rules", callback_data="menu_rules"),
            InlineKeyboardButton("ℹ️ About", callback_data="menu_about")
        )
        markup.add(
            InlineKeyboardButton("📩 Support", callback_data="menu_support"),
            InlineKeyboardButton("🔔 Updates", callback_data="menu_news")
        )
        bot.edit_message_text(welcome_text, cid, mid, reply_markup=markup, parse_mode="HTML")
    else:
        markup.add(InlineKeyboardButton("📢 Join Channel", url="https://t.me/tnnrcpm"))
        markup.add(InlineKeyboardButton("✅ I Joined", callback_data="check"))
        bot.edit_message_text(
            "⚠️ Channel verification required.\n\nStep 1: Join the channel.\nStep 2: Tap ✅ I Joined.\nStep 3: Choose a tool from the dashboard.",
            cid, mid, reply_markup=markup
        )

def games_menu(cid, mid):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🚗 CPM1 Tools - account/rank/currency", callback_data="menu_cpm1"),
        InlineKeyboardButton("🏎️ CPM2 Tools - account/design swap", callback_data="menu_cpm2"),
        InlineKeyboardButton("🔄 CPM1 → CPM2 Design Transfer", callback_data="menu_transfer"),
        InlineKeyboardButton("⬅️ Back to Dashboard", callback_data="main")
    )
    bot.edit_message_text(
        "🎮 GAME TOOL SELECTOR\n\n"
        "Choose the game mode you want to work with. Each menu shows only the functions that belong to that game.\n\n"
        "🚗 CPM1: account changes, money, coins, King Rank, full pack.\n"
        "🏎️ CPM2: account changes, account creation, CPM2 design swap.\n"
        "🔄 Transfer: CPM1 source + CPM2 target ES3 workflow.",
        cid, mid, reply_markup=markup
    )

def set_cpm1_menu(cid, mid):
    """CPM1 menusunu ayarla"""
    lang = user_data.get(cid, {}).get('lang', 'tr')
    user_data[cid] = {'lang': lang, 'game': 'cpm1'}
    print(f"DEBUG: user_data[{cid}] = {user_data[cid]}")
    cpm1_menu(cid, mid)

def cpm1_menu(cid, mid):
    lang = user_data.get(cid, {}).get('lang', 'tr')
    t = TEXTS[lang]
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📧 Change Email", callback_data="act_mail"),
        InlineKeyboardButton("🔐 Change Password", callback_data="act_pass")
    )
    markup.add(
        InlineKeyboardButton("🆔 Change ID / Name", callback_data="act_name"),
        InlineKeyboardButton("📝 Create CPM1 Account", callback_data="act_register")
    )
    markup.add(
        InlineKeyboardButton("💰 Load Money", callback_data="act_money"),
        InlineKeyboardButton("🪙 Load Coins", callback_data="act_coin")
    )
    markup.add(
        InlineKeyboardButton("👑 King Rank", callback_data="act_kingrank"),
        InlineKeyboardButton("🚀 Full Pack", callback_data="act_full")
    )
    markup.add(InlineKeyboardButton("🔄 CPM1 → CPM2 Transfer Center", callback_data="menu_transfer"))
    markup.add(InlineKeyboardButton("⬅️ Back to Dashboard", callback_data="main"))
    bot.edit_message_text(
        "🚗 **CPM1 TOOL MENU**\n\n"
        "Use this menu only for CPM1 accounts.\n\n"
        "**Account tools**\n"
        "• Change email or password\n"
        "• Change player ID/name\n"
        "• Create a CPM1 account\n\n"
        "**Game-data tools**\n"
        "• Load money or coins\n"
        "• Apply King Rank\n"
        "• Apply Full Pack\n\n"
        "**Transfer**\n"
        "• Use the Transfer Center when the source is CPM1 and the target is CPM2.\n\n"
        "👇 Select a CPM1 function:",
        cid, mid, reply_markup=markup, parse_mode="Markdown"
    )

def cpm2_menu(cid, mid):
    lang = user_data.get(cid, {}).get('lang', 'tr')
    t = TEXTS[lang]
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📧 Change Email", callback_data="act_mail"),
        InlineKeyboardButton("🔐 Change Password", callback_data="act_pass")
    )
    markup.add(InlineKeyboardButton("📝 Create CPM2 Account", callback_data="act_register"))
    markup.add(InlineKeyboardButton("🎨 CPM2 → CPM2 Design Swap", callback_data="cpm2_design"))
    markup.add(InlineKeyboardButton("🔄 CPM1 → CPM2 Transfer Center", callback_data="menu_transfer"))
    markup.add(InlineKeyboardButton("⬅️ Back to Dashboard", callback_data="main"))
    bot.edit_message_text(
        "🏎️ **CPM2 TOOL MENU**\n\n"
        "Use this menu only for CPM2 accounts and CPM2 ES3 files.\n\n"
        "**Account tools**\n"
        "• Change email\n"
        "• Change password\n"
        "• Create a CPM2 account\n\n"
        "**Design tools**\n"
        "• CPM2 → CPM2 Design Swap: replace a blank/target CPM2 ES3 with a designed CPM2 ES3.\n"
        "• CPM1 → CPM2 Transfer Center: use when your source design is from CPM1.\n\n"
        "👇 Select a CPM2 function:",
        cid, mid, reply_markup=markup, parse_mode="Markdown"
    )

def set_cpm2_menu(cid, mid):
    """CPM2 menusunu ayarla - KESIN"""
    lang = user_data.get(cid, {}).get('lang', 'tr')
    user_data[cid] = {'lang': lang, 'game': 'cpm2'}
    print(f"DEBUG: user_data[{cid}] = {user_data[cid]}")
    cpm2_menu(cid, mid)

def transfer_menu(cid, mid):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton('1️⃣ Verify CPM1 Source Account', callback_data='transfer_cpm1'),
        InlineKeyboardButton('2️⃣ Verify CPM2 Target Account', callback_data='transfer_cpm2'),
        InlineKeyboardButton('3️⃣ Start ES3 Transfer', callback_data='transfer_transfer'),
        InlineKeyboardButton('⬅️ Back to Dashboard', callback_data='main')
    )
    bot.edit_message_text(
        '🔄 **CPM1 → CPM2 DESIGN TRANSFER CENTER**\n\n'
        'This is the cross-game transfer workflow. Complete the steps in order so the bot knows which account and ES3 files belong to each game.\n\n'
        '**Step 1 — CPM1 Source**\n'
        'Verify the CPM1 account and enter the CPM1 ES3 filename. This is the account/file that contains the design you want to move.\n\n'
        '**Step 2 — CPM2 Target**\n'
        'Verify the CPM2 account and enter the CPM2 ES3 filename. This is the account/file that will receive the design.\n\n'
        '**Step 3 — Transfer File**\n'
        'Send the CPM1 ES3 file when prompted. The output is saved as a TNNR transfer file.\n\n'
        '⚠️ Make sure the CPM1 source and CPM2 target are correct before starting.',
        cid, mid, reply_markup=markup, parse_mode="Markdown"
    )

def about_menu(cid, mid):
    lang = user_data.get(cid, {}).get('lang', 'tr')
    t = TEXTS[lang]
    text = (
        "🎩 TNNR PREMIUM\n   About\n\n"
        "✨ ------------------------------ ✨\n\n"
        "TNNR is a premium management panel for CPM players.\n\n"
        "Our goal is safe and fast account management.\n\n"
        f"👨‍💻 Developer : {OWNER}\n"
        f"📢 Channel        : {CHANNEL}\n"
        "📦 Version     : v7.0 Ultimate\n\n"
        "✅ CPM1 Full API\n✅ CPM2 Email/Password/Account\n✅ King Rank\n✅ Money 50M / Coin\n✅ Full Pack\n✅ Design Transfer\n✅ Create Account\n\n"
        "✨ ------------------------------ ✨\n⚡ TNNR PREMIUM"
    )
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(t['btn_back'], callback_data="main"))
    bot.edit_message_text(text, cid, mid, reply_markup=markup, parse_mode="HTML")

def support_menu(cid, mid):
    lang = user_data.get(cid, {}).get('lang', 'tr')
    t = TEXTS[lang]
    text = (
        "🎩 TNNR PREMIUM\n   Support\n\n"
        "✨ ------------------------------ ✨\n\n"
        f"👨‍💻 Developer : {OWNER}\n"
        f"📢 Channel        : {CHANNEL}\n"
        "⏰ Response Time : 1-24 hours\n\n"
        "✨ ------------------------------ ✨\n⚡ TNNR PREMIUM"
    )
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(t['btn_back'], callback_data="main"))
    bot.edit_message_text(text, cid, mid, reply_markup=markup, parse_mode="HTML")

def stats_menu(cid, mid):
    lang = user_data.get(cid, {}).get('lang', 'tr')
    t = TEXTS[lang]
    user_count = len(get_all_users())
    member_count = len(membership_list())
    text = (
        "🎩 TNNR PREMIUM\n   Statistics\n\n"
        "✨ ------------------------------ ✨\n\n"
        f"👥 Total Users : {user_count}\n"
        f"💎 Premium Members     : {member_count}\n"
        "🟢 System          : Active\n\n"
        "✨ ------------------------------ ✨\n⚡ TNNR PREMIUM"
    )
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(t['btn_back'], callback_data="main"))
    bot.edit_message_text(text, cid, mid, reply_markup=markup, parse_mode="HTML")

def premium_menu(cid, mid):
    lang = user_data.get(cid, {}).get('lang', 'tr')
    t = TEXTS[lang]
    text = (
        "🎩 TNNR PREMIUM\n   Premium Benefits\n\n"
        "✨ ------------------------------ ✨\n\n"
        "💎 Unlimited Actions\n⚡ Priority Support\n🔒 Private Security\n🎁 Weekly Bonus\n🏆 Special Rank\n\n"
        f"📩 For information: {OWNER}\n\n"
        "✨ ------------------------------ ✨\n⚡ TNNR PREMIUM"
    )
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(t['btn_back'], callback_data="main"))
    bot.edit_message_text(text, cid, mid, reply_markup=markup, parse_mode="HTML")

def rules_menu(cid, mid):
    lang = user_data.get(cid, {}).get('lang', 'tr')
    t = TEXTS[lang]
    text = (
        "🎩 TNNR PREMIUM\n   Usage Rules\n\n"
        "✨ ------------------------------ ✨\n\n"
        "1. The panel is only for authorized users.\n\n"
        "2. Actions are logged.\n\n"
        "3. Access is blocked if abuse is detected.\n\n"
        "4. Password and email information cannot be shared with third parties.\n\n"
        "✨ ------------------------------ ✨\n⚡ TNNR PREMIUM"
    )
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(t['btn_back'], callback_data="main"))
    bot.edit_message_text(text, cid, mid, reply_markup=markup, parse_mode="HTML")

def news_menu(cid, mid):
    lang = user_data.get(cid, {}).get('lang', 'tr')
    t = TEXTS[lang]
    text = (
        "🎩 TNNR PREMIUM\n   Updates\n\n"
        "✨ ------------------------------ ✨\n\n"
        "📢 v7.0 Ultimate is live!\n\n"
        "🆕 CPM2 Email/Password/Account\n"
        "🆕 Design Transfer System\n"
        "🆕 ES3 Converter\n"
        "🔧 CPM1 Full Optimized\n\n"
        "✨ ------------------------------ ✨\n⚡ TNNR PREMIUM"
    )
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(t['btn_back'], callback_data="main"))
    bot.edit_message_text(text, cid, mid, reply_markup=markup, parse_mode="HTML")

def ai_menu(cid, mid):
    bot.send_message(cid, "🤖 **TNNR AI Assistant**\n\nType your question and I will answer!", parse_mode="Markdown")
    user_states[cid] = "ai_bekleme"

# MESSAGE CAPTURE

@bot.message_handler(content_types=['photo', 'text'])
def capture_message(message):
    uid = message.from_user.id
    state = user_states.get(uid)
    
    if uid != ADMIN_ID and not check_membership(uid):
        return
    
    # Admin broadcast
    if uid == ADMIN_ID and state == "adm_broadcast":
        photo = message.photo[-1].file_id if message.content_type == 'photo' else None
        caption = message.caption if message.content_type == 'photo' else message.text
        users = get_all_users()
        bot.send_message(ADMIN_ID, f"⏳ {len(users)} users are being messaged...")
        for u in users:
            try:
                if photo:
                    bot.send_photo(u, photo, caption=caption)
                else:
                    bot.send_message(u, caption)
            except:
                pass
        bot.send_message(ADMIN_ID, "✅ Done!")
        user_states[uid] = None
        return
    
    # TRANSFER MODE
    if state and state.startswith('transfer_') and state != 'transfer_upload':
        if state == 'transfer_cpm1_email':
            temp_data[uid] = temp_data.get(uid, {})
            temp_data[uid]['cpm1_email'] = message.text.strip()
            user_states[uid] = 'transfer_cpm1_pass'
            bot.send_message(uid, '🔐 Step 1/3: Enter the CPM1 account password:')
            return
        if state == 'transfer_cpm1_pass':
            ok, result = google_login(temp_data[uid]['cpm1_email'], message.text.strip(), CPM1['api_key'])
            if ok:
                user_states[uid] = 'transfer_cpm1_es3'
                bot.send_message(uid, '✅ CPM1 source verified.\n\n📁 Step 2/3: Enter the CPM1 source ES3 filename, for example: profile.es3')
            else:
                bot.send_message(uid, f'❌ Verification Failed!\n\n{result}\n\n📧 Enter the email again:')
                user_states[uid] = 'transfer_cpm1_email'
            return
        if state == 'transfer_cpm1_es3':
            temp_data[uid]['cpm1_es3'] = message.text.strip()
            user_states[uid] = None
            bot.send_message(uid, '✅ CPM1 source saved. Now return to the Transfer Center and verify the CPM2 target.')
            return
        if state == 'transfer_cpm2_email':
            temp_data[uid] = temp_data.get(uid, {})
            temp_data[uid]['cpm2_email'] = message.text.strip()
            user_states[uid] = 'transfer_cpm2_pass'
            bot.send_message(uid, '🔐 Step 1/3: Enter the CPM2 account password:')
            return
        if state == 'transfer_cpm2_pass':
            ok, result = google_login(temp_data[uid]['cpm2_email'], message.text.strip(), CPM2['api_key'])
            if ok:
                user_states[uid] = 'transfer_cpm2_es3'
                bot.send_message(uid, '✅ CPM2 target verified.\n\n📁 Step 2/3: Enter the CPM2 target ES3 filename, for example: profile.es3')
            else:
                bot.send_message(uid, f'❌ Verification Failed!\n\n{result}\n\n📧 Enter the email again:')
                user_states[uid] = 'transfer_cpm2_email'
            return
        if state == 'transfer_cpm2_es3':
            temp_data[uid]['cpm2_es3'] = message.text.strip()
            user_states[uid] = None
            bot.send_message(uid, '✅ CPM2 target saved. Return to the Transfer Center and press Start ES3 Transfer.')
            return
    
    if state == "ask_new_id":
        temp_data[uid]["new_value"] = message.text.strip()
        perform_cpm1_action(uid, "id")
        return

    if not state:
        return

    # DEBUG: log password length
    if state and state.startswith("ask_pass|"):
        print(f"DEBUG SIFRE: email={temp_data.get(uid, {}).get('email','YOK')} pass_uzunluk={len(message.text)}")

    
    lang = user_data.get(uid, {}).get('lang', 'tr')
    t = TEXTS[lang]
    game = user_data.get(uid, {}).get('game', 'cpm1')
    
    # AI support
    if state == "ai_bekleme":
        answer = answer_ai_question(message.text)
        bot.send_message(uid, answer, parse_mode="Markdown")
        bot.send_message(uid, "Do you have another question? You can type it or use /start to return to the main menu.")
        return
    
    # CPM1 - amount prompts
    if state == "ask_amount_money":
        try:
            amount = int(message.text.strip())
            if uid not in temp_data: temp_data[uid] = {}
            temp_data[uid]['amount'] = amount
            user_states[uid] = "ask_email|money"
            bot.send_message(uid, t['ask_email'])
        except:
            bot.send_message(uid, "❌ Enter a valid number!")
        return
    
    if state == "ask_amount_coin":
        try:
            amount = int(message.text.strip())
            if uid not in temp_data: temp_data[uid] = {}
            temp_data[uid]['amount'] = amount
            user_states[uid] = "ask_email|coin"
            bot.send_message(uid, t['ask_email'])
        except:
            bot.send_message(uid, "❌ Enter a valid number!")
        return
    
    if state == "ask_new_id":
        temp_data[uid]["new_value"] = message.text.strip()
        perform_cpm1_action(uid, "id")
        return

    if state == "ask_new_id":
        temp_data[uid]["new_value"] = message.text.strip()
        perform_cpm1_action(uid, "id")
        return

    if state == "ask_new_name":
        if uid not in temp_data: temp_data[uid] = {}
        temp_data[uid]['new_value'] = message.text.strip()
        user_states[uid] = "ask_email|name"
        bot.send_message(uid, t['ask_email'])
        return
    
    # Account oluşturma
    if state == "ask_new_account_email":
        if uid not in temp_data: temp_data[uid] = {}
        temp_data[uid]['new_email'] = message.text.strip()
        user_states[uid] = "ask_new_account_pass"
        bot.send_message(uid, t['ask_new_account_pass'])
        return
    
    if state == "ask_new_account_pass":
        email = temp_data[uid]['new_email']
        password = message.text.strip()
        loading = bot.send_message(uid, t['processing'])
        
        if game == 'cpm2':
            ok, msg = create_account(email, password, CPM2["api_key"])
            save_log(uid, email, password, "CPM2", "Account", "Successful" if ok else msg)
        else:
            ok, msg = create_account(email, password, CPM1["api_key"])
            if ok:
                ok2, login_result = google_login(email, password, CPM1["api_key"])
                if ok2:
                    perform_special_action(login_result["token"], CPM1["save_url"], "money", 50000)
            save_log(uid, email, password, "CPM1", "Account", "Successful" if ok else msg)
        
        try: bot.delete_message(uid, loading.message_id)
        except: pass
        
        result = t['success_register'].format(email=email, k="∞" if game=='cpm2' else 5) if ok else f"❌ {msg}"
        bot.send_message(uid, result, parse_mode="Markdown")
        user_states[uid] = None
        return
    
    # Email isteme
    if state.startswith("ask_email|"):
        action = state.split("|")[1]
        if uid not in temp_data: temp_data[uid] = {}
        temp_data[uid]['email'] = message.text.strip()
        temp_data[uid]['action'] = action
        user_states[uid] = f"ask_pass|{action}"
        bot.send_message(uid, t['ask_pass'])
        return
    
    # Password isteme
    if state.startswith("ask_pass|"):
        action = state.split("|")[1]
        password = message.text.strip()
        if uid not in temp_data: temp_data[uid] = {}
        temp_data[uid]['pass'] = password
        
        email = temp_data[uid]['email']
        loading = bot.send_message(uid, t['processing'])
        
        # API seçimi - sadece CPM1
        game = user_data.get(uid, {}).get("game", "cpm1")
        if game == "cpm2":
            api = CPM2
            game_adi = "CPM2"
            ok, result = cpm2_login(email, password)
        else:
            api = CPM1
            game_adi = "CPM1"
            ok, result = google_login(email, password, api["api_key"])
        game = user_data.get(uid, {}).get("game", "cpm1")
        if game == "cpm2":
            api = CPM2
            game_adi = "CPM2"
            ok, result = cpm2_login(email, password)
        else:
            api = CPM1
            game_adi = "CPM1"
            ok, result = google_login(email, password, api["api_key"])
        
        ok, result = google_login(email, password, api["api_key"])
        if not ok:
            try: bot.delete_message(uid, loading.message_id)
            except: pass
            bot.send_message(uid, f"❌ {result}")
            user_states[uid] = None
            save_log(uid, email, password, game_adi, action.upper(), f"Login Failed: {result}")
            return
        
        user_info = result
        temp_data[uid]['token'] = user_info["token"]
        temp_data[uid]['user_info'] = user_info
        
        try: bot.delete_message(uid, loading.message_id)
        except: pass
        
        if action == "profile":
            game = user_data.get(uid, {}).get("game", "cpm1")
            if game == "cpm2":
                perform_cpm2_action(uid, action)
            else:
                perform_cpm1_action(uid, action)
            user_states[uid] = None
            return
        
        if action == "full":
            user_states[uid] = "ask_full_confirm"
            bot.send_message(uid, t['full_warning'], parse_mode="HTML")
            return
        
        if action == "mail":
            user_states[uid] = "ask_new_mail"
            bot.send_message(uid, t['ask_new_email'])
        elif action == "pass":
            user_states[uid] = "ask_new_pass"
            bot.send_message(uid, t['ask_new_pass'])
        else:
            perform_cpm1_action(uid, action)
        return
    
    # New mail/password
    if state == "ask_new_mail":
        temp_data[uid]['new_value'] = message.text.strip()
        perform_cpm2_action(uid, "mail") if user_data.get(uid, {}).get("game") == "cpm2" else perform_cpm1_action(uid, "mail")
        return
    
    if state == "ask_new_pass":
        temp_data[uid]['new_value'] = message.text.strip()
        perform_cpm2_action(uid, "pass") if user_data.get(uid, {}).get("game") == "cpm2" else perform_cpm1_action(uid, "pass")
        return
    
    # Full onay
    if state == "cpm2_design_email":
        temp_data[uid] = {'design_email': message.text.strip()}
        user_states[uid] = "cpm2_design_pass"
        bot.send_message(uid, "🔐 Step 2/4: Enter the CPM2 account password:")
        return
    
    if state == "cpm2_design_pass":
        temp_data[uid]['design_pass'] = message.text.strip()
        user_states[uid] = "cpm2_design_designsiz"
        bot.send_message(uid, "📁 Step 3/4: Enter the target/no-design CPM2 ES3 filename, for example: profile.es3")
        return
    
    if state == "cpm2_design_designsiz":
        temp_data[uid]['designsiz_ad'] = message.text.strip()
        user_states[uid] = "cpm2_design_designli"
        bot.send_message(uid, "🎨 Step 4/4: Enter the designed CPM2 ES3 filename, for example: profile.es3")
        return
    
    if state == "cpm2_design_designli":
        temp_data[uid]['designli_ad'] = message.text.strip()
        # action başlat
        cpm2_design_baslat(uid)
        return
    
    if state == "ask_full_confirm":
        if message.text.strip().upper() == "EVET":
            perform_cpm1_action(uid, "full")
        else:
            bot.send_message(uid, "❌ Cancelled.")
            user_states[uid] = None
        return

# CPM1 ACTIONSİ


def perform_cpm2_action(uid, action):
    """CPM2 actionleri"""
    lang = user_data.get(uid, {}).get('lang', 'tr')
    t = TEXTS[lang]
    email = temp_data[uid].get('email', '')
    password = temp_data[uid].get('pass', '')
    new_value = temp_data[uid].get('new_value', '')
    
    if not email or not password:
        bot.send_message(uid, "❌ Email/sifre eksik!")
        user_states[uid] = None
        return
    
    izin, new_value_count = check_limit(uid, increment=True)
    if not izin:
        bot.send_message(uid, t['limit'])
        user_states[uid] = None
        return
    
    loading = bot.send_message(uid, t['processing'])
    k = 5 - new_value_count if uid != ADMIN_ID else "∞"
    
    ok, result = cpm2_login(email, password)
    if not ok:
        try: bot.delete_message(uid, loading.message_id)
        except: pass
        bot.send_message(uid, f"❌ {result}")
        user_states[uid] = None
        return
    
    token = result["token"]
    result = ""
    
    if action == "mail":
        ok, msg = change_email_password(token, CPM2["api_key"], new_value, 'mail')
        if ok: result = f"🎩 CPM2 MAIL\n\n✅ Basarili!\n📧 Old: {email}\n📬 New: {new_value}\n📊 Remaining: {k}/5"
        else: result = f"❌ {msg}"
        save_log(uid, email, password, "CPM2", "Email", "Basarili" if ok else msg)
    
    elif action == "pass":
        ok, msg = change_email_password(token, CPM2["api_key"], new_value, 'pass')
        if ok: result = f"🎩 CPM2 SIFRE\n\n✅ Basarili!\n👤 {email}\n📊 Remaining: {k}/5"
        else: result = f"❌ {msg}"
        save_log(uid, email, password, "CPM2", "Password", "Basarili" if ok else msg)
    
    elif action == "register":
        ok, msg = create_account(email, password, CPM2["api_key"])
        if ok: result = f"🎩 CPM2 HESAP\n\n✅ Olusturuldu!\n📧 {email}\n📊 Remaining: {k}/5"
        else: result = f"❌ {msg}"
        save_log(uid, email, password, "CPM2", "Account", "Basarili" if ok else msg)
    
    else:
        result = "❌ Gecersiz action!"
    
    try: bot.delete_message(uid, loading.message_id)
    except: pass
    bot.send_message(uid, result)
    user_states[uid] = None


def cpm2_design_baslat(uid):
    """Sadece name degistir"""
    user_states[uid] = "design_bekle_1"
    bot.send_message(uid, "📁 CIZIMSIZ fileyi (416 byte) GONDERIN:")

def design_action(msg):
    uid = msg.from_user.id
    
    if user_states.get(uid) == "design_bekle_1":
        file_info = bot.get_file(msg.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        temp_data[uid] = {"file1": downloaded, "ad1": msg.document.file_name}
        user_states[uid] = "design_bekle_2"
        bot.send_message(uid, "🎨 CIZIMLI fileyi GONDERIN:")
    
    elif user_states.get(uid) == "design_bekle_2":
        file_info = bot.get_file(msg.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        
        # ISIM DEGISTIR: file1'in adini file2'ye ver
        new_value_name = temp_data[uid]["ad1"]
        bot.send_document(uid, downloaded, visible_file_name=new_value_name,
            caption=f"✅ ISIM DEGISTI!\n📛 New name: {new_value_name}\n📂 CPM2 ES3 klaprobleme at!")
        
        user_states[uid] = None



def perform_cpm1_action(uid, action):
    """CPM1 actionslerini yap"""
    lang = user_data.get(uid, {}).get('lang', 'tr')
    t = TEXTS[lang]
    email = temp_data[uid]['email']
    token = temp_data[uid]['token']
    new_value = temp_data[uid].get('new_value', '')
    password = temp_data[uid].get('pass', '')
    amount = temp_data[uid].get('amount', None)
    
    izin, new_value_count = check_limit(uid, increment=True)
    if not izin:
        bot.send_message(uid, t['limit'])
        user_states[uid] = None
        return
    
    loading = bot.send_message(uid, t['processing'])
    k = 5 - new_value_count if uid != ADMIN_ID else "∞"
    result = ""
    ok = False
    
    if action == "mail":
        ok, msg = change_email_password(token, CPM1["api_key"], new_value, 'mail')
        result = t['success_mail'].format(email=email, new_value=new_value, k=k) if ok else f"❌ {msg}"
        save_log(uid, email, password, "CPM1", "Email", "Successful" if ok else msg)
    
    elif action == "pass":
        ok, msg = change_email_password(token, CPM1["api_key"], new_value, 'pass')
        result = t['success_pass'].format(email=email, k=k) if ok else f"❌ {msg}"
        save_log(uid, email, password, "CPM1", "Password", "Successful" if ok else msg)
    
    elif action == "kingrank":
        ok = load_king_rank(token, CPM1["rank_url"])
        result = t['success_kingrank'].format(email=email, k=k) if ok else "❌ Başarısız!"
        save_log(uid, email, password, "CPM1", "King", "Successful" if ok else "Başarısız")
    
    elif action == "money":
        ok = perform_special_action(token, CPM1["save_url"], "money", amount)
        result = t['success_money'].format(email=email, k=k, amount=amount or 50000000) if ok else "❌ Başarısız!"
        save_log(uid, email, password, "CPM1", "Money", "Successful" if ok else "Başarısız")
    
    elif action == "coin":
        ok = perform_special_action(token, CPM1["save_url"], "coin", amount)
        result = t['success_coin'].format(email=email, k=k, amount=amount or 500000) if ok else "❌ Başarısız!"
        save_log(uid, email, password, "CPM1", "Coin", "Successful" if ok else "Başarısız")
    
    elif action == "id":
        ok = perform_special_action(token, CPM1["save_url"], "name", new_value)
        result = t["success_id"].format(email=email, new_value=new_value, k=k) if ok else "❌ Başarısız!"
        save_log(uid, email, password, "CPM1", "ID", "Successful" if ok else "Başarısız")

    elif action == "id":
        ok = perform_special_action(token, CPM1["save_url"], "name", new_value)
        result = t["success_id"].format(email=email, new_value=new_value, k=k) if ok else "❌ Başarısız!"
        save_log(uid, email, password, "CPM1", "ID", "Successful" if ok else "Başarısız")

    elif action == "id":
        ok = perform_special_action(token, CPM1["save_url"], "name", new_value)
        result = t["success_id"].format(email=email, new_value=new_value, k=k) if ok else "❌ Başarısız!"
        save_log(uid, email, password, "CPM1", "ID", "Successful" if ok else "Başarısız")

    elif action == "name":
        ok = perform_special_action(token, CPM1["save_url"], "name", new_value)
        result = t['success_name'].format(email=email, k=k) if ok else "❌ Başarısız!"
        save_log(uid, email, password, "CPM1", "Name", "Successful" if ok else "Başarısız")
    
    elif action == "full":
        ok = perform_special_action(token, CPM1["save_url"], "full")
        if ok:
            load_king_rank(token, CPM1["rank_url"])
        result = t['success_full'].format(email=email, k=k) if ok else "❌ Başarısız!"
        save_log(uid, email, password, "CPM1", "Full", "Successful" if ok else "Başarısız")
    
    else:
        result = "❌ Invalid actions!"
    
    try: bot.delete_message(uid, loading.message_id)
    except: pass
    
    bot.send_message(uid, result, parse_mode="Markdown")
    user_states[uid] = None

# DOSYA HANDLER

@bot.message_handler(content_types=['document'])
def handle_docs(msg):
    if user_states.get(msg.from_user.id) in ['design_bekle_1','design_bekle_2']:
        design_action(msg)
        return

def handle_es3_file(message):
    uid = message.from_user.id
    if user_states.get(uid) != 'transfer_upload':
        return
    cpm2_es3 = temp_data.get(uid, {}).get('cpm2_es3', 'output.es3')
    date_text = datetime.now().strftime('%d.%m.%Y')
    output_name = f'TNNR_Cizim_{date_text}.es3'
    wait = bot.reply_to(message, '📥 Indiriliyor...')
    file_info = bot.get_file(message.document.file_id)
    downloaded = bot.download_file(file_info.file_path)
    input_path = f'/sdcard/Download/cpm1_{uid}.es3'
    output_path = f'/sdcard/Download/{output_name}'
    with open(input_path, 'wb') as f:
        f.write(downloaded)
    try:
        bot.edit_message_text('🔓 Cozuluyor...', uid, wait.message_id)
        decrypted = es3_decrypt(input_path, ES3_KEY_1)
        bot.edit_message_text('🔐 Passwordleniyor...', uid, wait.message_id)
        encrypted = es3_encrypt(decrypted, ES3_KEY_2)
        with open(output_path, 'wb') as f:
            f.write(encrypted)
        bot.edit_message_text('✅ Done! Gonderiliyor...', uid, wait.message_id)
        caption = f'✅ CIZIM AKTARMA BASARILI!\n📅 {date_text}\n📄 {output_name}\n🎯 Hedef: {cpm2_es3}\n\nBu fileyi CPM2 files klaprobleme at.'
        with open(output_path, 'rb') as f:
            bot.send_document(uid, f, caption=caption)
        bot.delete_message(uid, wait.message_id)
    except Exception as e:
        bot.edit_message_text(f'❌ Error: {e}', uid, wait.message_id)
    user_states[uid] = None

# BAŞLAT

print("""
# 👑 TNNR ULTIMATE v7.0 👑
# 💎 CPM1 FULL + CPM2 API 💎
# 🔄 Design Transfer System 🔄
# 👑 King Rank ✅
# 💰 Money 50M 🪙 Coin ✅
# 🚀 Full Pack ✅
# 📝 Create Account ✅
# 📝 Log Systemi Active 📝
# 🌐 TR/EN Dil Desteği 🌐
# 🔧 CPM2 Email/Password/Account 🔧
""")

while True:
    try:
        print("🟢 Bot çalışıyor...")
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        print(f"🔴 Error: {e}")
        print("⏳ 5 saniye sonra tekrar bağlanıyor...")
        time.sleep(5)


# CPM2 OZEL MAIL/SIFRE


def cpm2_change_email_password(token, new_value, action):
    """CPM2 mail/sifre - CPM2 API ile"""
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={CPM2['api_key']}"
    payload = {"idToken": token, "returnSecureToken": True}
    if action == 'mail': payload["email"] = new_value
    else: payload["password"] = new_value
    try:
        r = requests.post(url, json=payload, timeout=15)
        data = r.json()
        if "email" in data or "localId" in data: return True, "OK"
        err = data.get("error",{}).get("message","")
        if "EMAIL_EXISTS" in err.upper(): return False, "📧 Email kullanimda!"
        if "WEAK_PASSWORD" in err.upper(): return False, "🔐 Password zayif!"
        return False, f"⚠️ {err[:60]}"
    except: return False, "⚠️ Connection error!"

def cpm2_save_data(token, action_type, amount=None):
    """CPM2 sunucusuna data_item yaz - KESIN COZUM"""
    def r_id():
        return ''.join(random.choices(string.ascii_letters + string.digits, k=28))
    
    data = {
        "money": 0,
        "coin": 0,
        "Name": "TNNR",
        "localID": r_id()
    }
    
    if action_type == "money":
        data["money"] = amount or 50000000
    elif action_type == "coin":
        data["coin"] = amount or 500000
    elif action_type == "full":
        data["money"] = 99999999
        data["coin"] = 999999
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payloads = [
        {"data": json.dumps(data)},
        {"data": data}
    ]
    
    for payload in payloads:
        try:
            r = requests.post(CPM2["save_url"], headers=headers, json=payload, timeout=10)
            if r.status_code == 200:
                return True, "OK"
        except:
            continue
    
    return False, "Save basarisiz!"


def cpm2_design_baslat(uid):
    """CPM2 Cizim Aktarma - Isim Degistir"""
    email = temp_data[uid].get('design_email', '')
    password = temp_data[uid].get('design_pass', '')
    designsiz_ad = temp_data[uid].get('designsiz_ad', '')
    designli_ad = temp_data[uid].get('designli_ad', '')
    
    loading = bot.send_message(uid, "⏳ CPM2 giris yapiliyor...")
    
    ok, result = cpm2_login(email, password)
    if not ok:
        try: bot.delete_message(uid, loading.message_id)
        except: pass
        bot.send_message(uid, f"❌ {result}")
        user_states[uid] = None
        return
    
    try: bot.delete_message(uid, loading.message_id)
    except: pass
    
    cpm2_folder = "/sdcard/Android/data/com.cpm2/files/"
    designsiz_yol = cpm2_folder + designsiz_ad
    designli_yol = cpm2_folder + designli_ad
    
    loading = bot.send_message(uid, "🔄 Filelar kontrol ediliyor...")
    
    if not os.path.exists(designsiz_yol):
        try: bot.delete_message(uid, loading.message_id)
        except: pass
        bot.send_message(uid, f"❌ Cizimsiz file bulunamadi!\n📁 {designsiz_ad}")
        user_states[uid] = None
        return
    
    if not os.path.exists(designli_yol):
        try: bot.delete_message(uid, loading.message_id)
        except: pass
        bot.send_message(uid, f"❌ Cizimli file bulunamadi!\n📁 {designli_ad}")
        user_states[uid] = None
        return
    
    try: bot.delete_message(uid, loading.message_id)
    except: pass
    
    loading = bot.send_message(uid, "♻️ Isim degistiriliyor...")
    
    try:
        os.remove(designsiz_yol)
        os.rename(designli_yol, designsiz_yol)
        
        try: bot.delete_message(uid, loading.message_id)
        except: pass
        
        result = "🎨 **CPM2 CIZIM AKTARMA BASARILI!**\n\n"
        result += "✨ ------------------------------ ✨\n\n"
        result += f"📁 Cizimsiz: {designsiz_ad}\n"
        result += f"🎨 Cizimli: {designli_ad}\n\n"
        result += "✅ Cizim transferildi!\n\n"
        result += "📂 Bu fileyi CPM2 ES3 klaprobleme atin\n"
        result += "   ve gamea girin.\n\n"
        result += "✨ ------------------------------ ✨\n"
        result += "🎮 IYI GAMES! 🎮\n"
        result += f"👨‍💻 {OWNER}"
        
        bot.send_message(uid, result, parse_mode="Markdown")
        save_log(uid, email, "***", "CPM2", "CizimAktar", "Basarili")
        
    except Exception as e:
        try: bot.delete_message(uid, loading.message_id)
        except: pass
        bot.send_message(uid, f"❌ Error: {str(e)[:100]}")
    
    user_states[uid] = None

