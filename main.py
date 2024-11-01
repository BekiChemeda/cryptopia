from flask import Flask

import telebot
from telebot import TeleBot, types
from telebot.types import ReplyKeyboardRemove
import requests
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime
import time

load_dotenv()
API_KEY = os.getenv('API_KEY')
bot = telebot.TeleBot(API_KEY)

AUTHORIZED_USER_ID = os.getenv("AUTHORIZED_USER_ID")

DATABASE_USERNAME = os.getenv("DATABASE_USERNAME")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
URI = os.getenv("URI")
pm_me = types.InlineKeyboardMarkup()
pm_me_button = types.InlineKeyboardButton(
    text="📥PM me ",
    url=f"https://t.me/{bot.get_me().username}"
)
pm_me.add(pm_me_button)
client = MongoClient(URI)
db = client[DATABASE_USERNAME]
bot_users_collection = db["bot_users"]
bot_groups_collection = db["bot_groups"]
bot_admins_collection = db["bot_admins"]
bot_settings_collection = db["bot_settings"]


app = Flask(__name__)
@app.route('/webhook', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '!', 200
# Pre Functions
def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def extract_id_from_link(referral_link):
    """
    Extracts the user ID from the referral link.
    Example referral link: https://t.me/yourbot?start=123456789
    """
    if "start=" in referral_link:
        # Extract the user ID after 'start='
        return referral_link.split("start=")[1].strip()
    return None


def add_referral_bonus(user_id, referral_link):
    """
    Adds a referral bonus to the referrer's balance if a valid referral link is provided.
    """
    referrer_id = extract_id_from_link(referral_link)
    if referrer_id:
        try:
            # Retrieve the referral value from the bot_settings_collection
            setting = bot_settings_collection.find_one({"setting": "refer_value"})
            refer_value = int(setting["value"]) if setting and setting["value"] else 0

            # Update the referrer's balance
            result = bot_users_collection.update_one(
                {"user_id": referrer_id},
                {"$inc": {"balance:": refer_value}}  # Increment the balance by refer_value
            )

            if result.matched_count > 0:
                bot.send_message(referrer_id, f"You have received a referral bonus of {refer_value}!")
            else:
                # Optionally handle case where referrer does not exist
                bot.send_message(user_id, "Referrer not found.")

        except Exception as e:
            # Notify admins about the error
            notify_admins(f"Error in add_referral_bonus: {e}")
            bot.send_message(user_id, "An error occurred while processing the referral. The admins have been notified.")
    else:
        bot.send_message(user_id, "Invalid referral link provided.")


def store_user_id(user_id, firstName, referral_link=None):
    added_by = None
    try:
        # Check if the user ID already exists in the database
        if not bot_users_collection.find_one({"user_id": user_id}):
            # Insert the new user ID if it doesn't already exist
            bot_users_collection.insert_one({
                "user_id": user_id,
                "balance:": 0,
                "started_at": datetime.now(),
                "added_by": added_by,
                "Name": firstName
            })
            bot.send_message(user_id, "Account Created Successfully")

            # Add referral bonus if referral_link is provided
            if referral_link:
                add_referral_bonus(user_id, referral_link)

        else:
            bot.send_message(user_id, "You were already a member!")

    except Exception as e:
        bot.send_message(user_id,
                         "Error Happened While Creating Your Account. No worries I have sent the error log to admins and they will fix it soon")
        notify_admins(f"Error in store_user_id: {e}")


def check_membership(user_id):
    try:
        member_bright_codes = bot.get_chat_member('@Bright_Codes', user_id)
        member_et_cryptopia = bot.get_chat_member('@Et_Cryptopia', user_id)
        return member_bright_codes.status in ['member', 'administrator', 'creator'] and member_et_cryptopia.status in [
            'member', 'administrator', 'creator']
    except Exception as e:
        bot.send_message(user_id,
                         f"Error occurred while checking your membership status! Don't worry I have told the admins about it and they will fix it soon! ")
        # print(f"Error checking membership: {e}")
        admins = bot_admins_collection.find()
        admin_list = [str(admin['admin_id']) for admin in admins]
        for i in admin_list:
            bot.send_message(i, f'''
        Hello Admin Error Happened while I was chatting with - 
        User : {user_id}
        Error : {e}''')
        return False


def get_usdt_price_data():
    url = "https://ethiopian-currency-exchange.vercel.app/"
    res = requests.get(url).json()
    best_rate = res['bestRates'][3]
    global buy_rate, sell_rate
    buy_rate = best_rate['buyRate']
    sell_rate = best_rate['sellRate']

    return (
        f"<b>Platform: <a href='https://www.binance.info/activity/referral-entry/CPA/together-v4?hl=en&ref=CPA_00II2YH68T'> Binance</a></b>\n"
        f"Base Currency: <b>{best_rate['baseCurrency']}</b>\n"
        f"Currency Code: <b>{best_rate['currencyCode']}</b>\n"
        f"Buy Rate: {buy_rate} ETB\n"
        f"Sell Rate: {sell_rate} ETB\n"
        f"Buy-Sell Difference: {best_rate['buySellDifference']} ETB\n"
        f"Last Updated: {res['lastUpdated']}\n\n\n"
        f"📢 Channel : @Et_Cryptopia\n"
        f"💻Developer : @BEK_I"
    )

#Banks Info 

banks = [
"🏦CBE",
'🏦Awash B.',
'🏦B. of Abyssinia',
"🏦B. of Abyssinia",
"🏦Zemen B.",
"🏦Buna B.",
"🏦Nib Int B.",
'🏦Berhan B.',
"🏦Wegagen B.",
"🏦Global B.",
"🏦Enat B.",
"🏦Ahadu B.",
"🏦Addis Int B.",
"🏦Dashen B.",
"🏦Oromia Inte B.",
"🏦Lion Int B.",
"🏦Development B. of Eth",
"🏦Cooperative B. of Oromia",
"🏦Hijra B.",
"🏦Amhara B.",
"🏦Tsehay B.",
"🏦Tsedey B.",
"🏦Siinqee B.",
"🏦Hibret Bank",
"🏦Gohbetoch Bank",
"🏦National B. Of Ethiopia"
]

def keyboardss():
   buttons = []
   for index, bank in enumerate(banks):
    buttons.append(types.InlineKeyboardButton(text=bank, callback_data=str(index)))
    markup = types.InlineKeyboardMarkup(row_width=3).add(*buttons)
   return markup
    
def local_currency(bank):
    url = "https://ethiopian-currency-exchange.vercel.app/"
    res = requests.get(url).json()
    usd_rate = res['exchange_rates'][bank]['rates'][0]
    euro_rate = res['exchange_rates'][bank]['rates'][2]
    bank_name = res['exchange_rates'][bank]['name']
    global buy_rate, sell_rate
   # print(best_rate)
    return(
        f"<b>Bank: {bank_name} </b>\n\n"
        f"Base Currency: <b>{usd_rate['baseCurrency']}</b>\n"
        f"Currency Code: <b>{usd_rate['currencyCode']}</b>\n"
        f"Buying for: {usd_rate['buyRate']} ETB\n"
        f"Selling for: {usd_rate['sellRate']} ETB\n"
        f"Buy-Sell Difference: {usd_rate['buySellDifference']} ETB\n\n\n"
 
  
        f"Base Currency: <b>{euro_rate['baseCurrency']}</b>\n"
        f"Currency Code: <b>{euro_rate['currencyCode']}</b>\n"
        f"Buying for: {euro_rate['buyRate']} ETB\n"
        f"Selling for: {euro_rate['sellRate']} ETB\n"
        f"Buy-Sell Difference: {euro_rate['buySellDifference']} ETB\n\n\n"
        
        
        
        
        f"Last Updated: {res['lastUpdated']}\n\n\n"
        f"📢 Channel : @Et_Cryptopia\n"
        f"💻Developer : @BEK_I"
    )
    
    
    

#local_currency(1)

@bot.message_handler(commands=["/BanksRate", "banksrate", "Banksrate", "banksRate", "BANKSRATE", "bankrate", "BANKRATE", "bankRate", "BankRate", "bank", "banks"])
def banks_rate(msg):
 #banks = types.InlineKeyboardMarkup()
 #cbe = types.InlineKeyboardButton("💳 Commercial Bank Of Ethiopia", callback_data='0')
# awash = types.InlineKeyboardButton("💳 Awash Bank", callback_data='1')
# abysnia = types.InlineKeyboardButton("💳 Abysnia Bank", callback_data='1')
# banks.add(cbe, awash, abysnia )    
    bot.reply_to(msg, "Please Select One Of The Following Banks", reply_markup = keyboardss())



@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    # Acknowledge the callback query
    bot.answer_callback_query(call.id, text="Fetching data...")
    # Delete the previous message
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    # Process the callback data
    bank = int(call.data)
    result = local_currency(bank)
    # Send the new message with the result
    bot.send_message(call.message.chat.id, result)
    start_command(call.message)












# Function to check if a user is an admin
def is_admin(user_id):
    return bot_admins_collection.find_one({"admin_id": user_id}) is not None

def coming_soon(message, service):
    bot.send_message(message.chat.id, f"{service} is Coming to Cryptopia Soon")

def services(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    button1 = types.KeyboardButton("🪙Crypto News")
    button2 = types.KeyboardButton("📈Technical Analysis")
    button3 = types.KeyboardButton("🏠Home")

    keyboard.add(button2, button1)
    keyboard.add(button3)

    bot.send_message(message.chat.id, "Choose an option:", reply_markup=keyboard)


@bot.message_handler(commands=['suggest', 'Suggestion'])
def suggest_idea(message):
    if message.chat.type == "private":
        user_id = message.from_user.id
        chat_type = message.chat.type

        # Ask the user for their suggestion
        bot.reply_to(message, "Please share your suggestion or idea:")

        # Define a function to handle the response
        @bot.message_handler(func=lambda m: m.from_user.id == user_id)
        def handle_suggestion(response):
            suggestion_text = response.text

            # Notify admins about the suggestion
            notify_admins(f"New suggestion from User {user_id}:\n{suggestion_text}")

            # Acknowledge the user
            bot.reply_to(response, "Thank you for your suggestion! It has been sent to the admins.")

            # Remove the suggestion handler after the response
            bot.message_handler(func=lambda m: m.from_user.id == user_id)(None)
    else:
        bot.reply_to(message, "oops! This Command Works only in Private Chat!", reply_markup=pm_me)

# Command to add a new setting to bot_settings_collection
@bot.message_handler(commands=['add_setting'])
def add_setting(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    try:
        _, setting_name = message.text.split(maxsplit=1)
        # Check if setting already exists
        if bot_settings_collection.find_one({"setting": setting_name}):
            bot.reply_to(message, f"Setting '{setting_name}' already exists.")
            return

        # Insert new setting with an initial value of None
        bot_settings_collection.insert_one({"setting": setting_name, "value": None})
        bot.reply_to(message, f"Setting '{setting_name}' has been added.")
    except Exception as e:
        # Notify admins about the error
        notify_admins(f"Error in /add_setting: {e}")
        bot.reply_to(message, "An error occurred while adding the setting. The admins have been notified.")


# Command to set or update a setting's value
@bot.message_handler(commands=['set'])
def set_setting(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    try:
        _, setting_name, value = message.text.split(maxsplit=2)
        # Update the setting's value if it exists
        result = bot_settings_collection.update_one(
            {"setting": setting_name},
            {"$set": {"value": value}}
        )

        if result.matched_count == 0:
            bot.reply_to(message, f"Setting '{setting_name}' does not exist. Please add it first using /add_setting.")
        else:
            bot.reply_to(message, f"Setting '{setting_name}' updated to '{value}'.")
    except Exception as e:
        # Notify admins about the error
        notify_admins(f"Error in /set: {e}")
        bot.reply_to(message, "An error occurred while setting the value. The admins have been notified.")


# Command to display all settings and their values
@bot.message_handler(commands=['settings'])
def show_settings(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    try:
        settings = bot_settings_collection.find()
        settings_text = "Current Settings:\n\n"
        for setting in settings:
            settings_text += f"{setting['setting']}: {setting['value']}\n"

        if settings_text == "Current Settings:\n\n":
            settings_text = "No settings have been added yet."

        bot.reply_to(message, settings_text)
    except Exception as e:
        # Notify admins about the error
        notify_admins(f"Error in /settings: {e}")
        bot.reply_to(message, "An error occurred while retrieving settings. The admins have been notified.")


# Helper function to notify all admins of an error
def notify_admins(error_message):
    admins = bot_admins_collection.find()
    for admin in admins:
        bot.send_message(admin['admin_id'], error_message)


# Basic Commands
@bot.message_handler(commands=['start', 'Start'])
def start_command(message):
    user_id = message.from_user.id
    chat_type = message.chat.type
    markup = types.InlineKeyboardMarkup()
    add_to_group_button = types.InlineKeyboardButton(
        text="➕ Add to Group",
        url=f"https://t.me/{bot.get_me().username}?startgroup=true"
    )
    markup.add(add_to_group_button)
    if chat_type == "private":  # User
        firstname = message.from_user.first_name
        store_user_id(user_id, firstname)

        # Create inline keyboard
        keyboard = types.InlineKeyboardMarkup()
        join_channel_button = types.InlineKeyboardButton("📢 Bright Codes", url='https://t.me/Bright_Codes')
        join_channel_button2 = types.InlineKeyboardButton("📢 Cryptopia", url='https://t.me/Et_Cryptopia')
        check_membership_button = types.InlineKeyboardButton("🟢 Check Membership", callback_data='check_membership')

        keyboard.add(join_channel_button, join_channel_button2)
        keyboard.add(check_membership_button)

        if not check_membership(user_id):
            bot.reply_to(message,
                         "You must be a member of Below Channels In order to Use this Bot. \n @Bright_Codes \n @Et_Cryptopia",
                         reply_markup=keyboard)
            return

        # Enhanced welcome message
        welcome_message = ('''👋 Greetings! Welcome to Cryptopia Bot. 
    This is cryptopia, a bot which is created to serve you with all your crypto related needs.

    Use /help To see list Of Commands available for this bot.'''
                           )

        bot.reply_to(message, welcome_message, reply_markup=markup)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

        button1 = types.KeyboardButton("🪙p2p Rate")
        button2 = types.KeyboardButton("🆘Help")
        button8 = types.KeyboardButton("🏦Banks")
        button3 = types.KeyboardButton("About")
        button4 = types.KeyboardButton("👤Profile")
        button5 = types.KeyboardButton("📊Stats")
        button6 = types.KeyboardButton("⚙️Services")
        button7 = types.KeyboardButton("💬Comment")

        keyboard.add(button1, button2, button8)
        keyboard.add(button3, button4, button5)
        keyboard.add(button6, button7)

        bot.send_message(message.chat.id, "Choose an option:", reply_markup=keyboard)
    elif chat_type in ["group", "supergroup"]:  # Group
        group_id = message.chat.id
        group_name = message.chat.title

        # Check if the group is already in the database
        group_data = bot_groups_collection.find_one({"group_id": group_id})

        if group_data:
            # If group is found, check if the name has changed
            if group_data['group_name'] != group_name:
                # Update the group name in the database
                bot_groups_collection.update_one({"group_id": group_id}, {"$set": {"group_name": group_name}})

                # Send a message to notify about the name update
                bot.send_message(group_id, "🔄 The group name has been updated in the database.", reply_markup=pm_me)
        else:
            # If group is not found, insert it into the database with the timestamp
            timestamp = datetime.now()
            bot_groups_collection.insert_one({"group_id": group_id, "group_name": group_name, "added_at": timestamp})
            bot.send_message(group_id, "🎉 The bot has been added to the group!", reply_markup=pm_me)


# Help command
@bot.message_handler(commands=['help', 'Help'])
def help_command(message):
    chat_type = message.chat.type
    donate_keyboard = types.InlineKeyboardMarkup()
    donate_button = types.InlineKeyboardButton("💳 Donate", callback_data='donate')
    donate_keyboard.add(donate_button)
    help_text = ("<b>Available Commands</b>\n"
                 "/start - Refresh The Bot\n"
                 "/about - About the Bot\n"
                 "/profile - Your Profile\n"
                 "/help - Display assistance options\n"
                 "/pprice - Binance P2P Price\n"
                 "/conv - Convert Between currencies"
                 "/banks - TO get Current foreign Exchange data of banks"
                 
                 )
    if chat_type == "private":  # User
        bot.send_message(message.chat.id, help_text, parse_mode="HTML", reply_markup=donate_keyboard)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

        button1 = types.KeyboardButton("🪙p2p Rate")
        button2 = types.KeyboardButton("🏠Home")
        button3 = types.KeyboardButton("About")
        button4 = types.KeyboardButton("👤Profile")
        button5 = types.KeyboardButton("📊Stats")
        button6 = types.KeyboardButton("⚙️Services")
        button7 = types.KeyboardButton("💬Comment")
        button8 = types.KeyboardButton("🏦Banks")
        

        keyboard.add(button2, button1, button8)
        keyboard.add(button3, button4, button5)
        keyboard.add(button6, button7)

        bot.send_message(message.chat.id, "Choose an option:", reply_markup=keyboard)
    elif chat_type in ["group", "supergroup"]:  # Group
        bot.send_message(message.chat.id, help_text, parse_mode="HTML", reply_markup=pm_me)


@bot.message_handler(commands=["pprice", "Pprice", "pPrice", "PPRICE"])
def send_binance_rate(message):
    bot.reply_to(message, "Sending rate...")
    result = get_usdt_price_data()
    bot.send_message(message.chat.id, result, parse_mode="HTML",
                     disable_web_page_preview=True)


@bot.message_handler(commands=['about', 'ABOUT'])
def send_about(message):
    about_message = """
<b>Welcome to Cryptopia Bot v1.0!</b>
This bot is designed to provide you with different Crypto services Such as :
- crypto Conversions 
- Real time USDT prices in ETB on Binance Rates
- Current Crypto News
- Crypto Trade Analysis

Exciting news! I have plans for an update in just <b>few days</b>. I’ll be releasing the next version, which will include additional features to enhance your experience.

I want to be transparent with you: I know this bot can be slow at times and may even avoid answering occasionally. This is due to limitations of the free hosting service I'm using. To improve performance and ensure <b>24/7 accessibility</b>, I would greatly appreciate your support. If you'd like to help, please consider donating through the button below.

Thank you for your understanding and support!


Our channel 📢: <a href="https://t.me/Et_Cryptopia">@Et_Cryptopia</a>
Developer 🧑‍💻: <a href="https://t.me/BEK_I">@BEK_I</a>
Dev Channel 🧑‍💻: <a href="https://t.me/Bright_Codes">@Bright_Codes</a>
    """
    donate_keyboard = types.InlineKeyboardMarkup()
    donate_button = types.InlineKeyboardButton("💳 Donate", callback_data='donate')
    donate_keyboard.add(donate_button)

    if message.chat.type == "private":
        bot.send_message(message.chat.id, about_message, parse_mode='HTML', reply_markup=donate_keyboard,
                         disable_web_page_preview=True)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

        button1 = types.KeyboardButton("🪙p2p Rate")
        button2 = types.KeyboardButton("🏠Home")
        button3 = types.KeyboardButton("🆘Help")
        button4 = types.KeyboardButton("👤Profile")
        button5 = types.KeyboardButton("📊Stats")
        button6 = types.KeyboardButton("⚙️Services")
        button7 = types.KeyboardButton("💬Comment")
        button8 = types.KeyboardButton("🏦Banks")
        

        keyboard.add(button2, button1, button8)
        keyboard.add(button3, button4, button5)
        keyboard.add(button6, button7)

        bot.send_message(message.chat.id, "Choose an option:", reply_markup=keyboard)


    bot.send_message(message.chat.id, about_message, parse_mode='HTML',
                     disable_web_page_preview=True)

@bot.message_handler(commands=['profile', 'Profile', 'PROFILE'])
def profile(message):
    user_id = message.from_user.id
    # Find user data from MongoDB
    user_data = bot_users_collection.find_one({"user_id": user_id})
    if message.chat.type == "private":
        if user_data:
            # Format account details
            balance = user_data.get("balance", 0)
            started_at = user_data.get("started_at", datetime.now()).strftime("%Y-%m-%d")
            added_by = user_data.get("added_by", "Unknown")
            first_name = user_data.get("Name", "N/A")

            # Generate referral link
            referral_link = f"https://t.me/{bot.get_me().username}?start={user_id}"

            # Prepare profile message
            profile_message = (
             f"👤 <b>Profile</b>\n\n"
            f"<b>Name:</b> {first_name}\n"
            f"<b>Balance:</b> {balance} ETB\n"
            f"<b>Account Created On:</b> {started_at}\n"
            f"<b>Added By:</b> {added_by}\n\n"
            f"<b>Referral Link:</b> <a href='{referral_link}'>Invite friends</a>\n"
            f"<b>🔗URL:</b> {referral_link} "
            )

            # Send profile message with referral and share buttons
            markup = types.InlineKeyboardMarkup()
            share_button = types.InlineKeyboardButton(
                text="📤 Share", url=f"https://t.me/share/url?url={referral_link}"
            )
            markup.add( share_button)

            bot.send_message(
                message.chat.id,
                profile_message,
                parse_mode="html",
                reply_markup=markup,
                disable_web_page_preview=True
            )
        else:
            # If user data is not found in MongoDB
            bot.send_message(message.chat.id, "Profile not found. Please register first!")
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("🏠Home")

        keyboard.add(button1)

        bot.send_message(message.chat.id, "Wanna Go Back?", reply_markup=keyboard)

    else:
        bot.reply_to(message, "oops! This Command Works only in Private Chat!", reply_markup=pm_me)



# Convert USDT to ETB
@bot.message_handler(commands=['conv', 'Conv', 'CONV'])
def convert_usdt_to_etb(message):
    chat_type = message.chat.type
    donate_keyboard = types.InlineKeyboardMarkup()
    donate_button = types.InlineKeyboardButton("Donate", callback_data='donate')
    donate_keyboard.add(donate_button)
    split_text = message.text.split()
    if len(split_text) > 2:
        if is_float(split_text[1]) or message.text.split()[1].isdigit():
            amount = float(split_text[1])
            url = "https://ethiopian-currency-exchange.vercel.app/"
            res = requests.get(url).json()
            best_rate = res['bestRates'][3]
            buy_rate = round(float(best_rate['buyRate']), 2)
            sell_rate = round(float(best_rate['sellRate']), 2)
            if message.text.split()[2].lower() == "etb" and message.text.split()[3].lower() == "usdt":
                buy_price = round(amount / buy_rate, 3)
                sell_price = round(amount / sell_rate, 3)
                if chat_type == "private":  # User
                    response = (f"Binance Exchange USDT Rate\n"
                                f"Buy: {buy_price} USDT\n"
                                f"Sell to: {sell_price} USDT\n"
                                f"Buying price: 1 USDT ~ {buy_rate} ETB \n "
                                f"Selling price: 1 USDT ~ {sell_rate} ETB \n\n"
                                f"📢 Join Our Channel @Et_Cryptopia"
                                )
                    bot.reply_to(message, response, parse_mode="HTML", reply_markup=donate_keyboard)
                elif chat_type in ["group", "supergroup"]:  # Group
                    response = (f"Binance Exchange USDT Rate\n"
                                f"Sell to: {sell_price} USDT\n"
                                f"Buy: {buy_price} USDT\n"
                                f"Buying price: 1 USDT ~ {buy_rate} ETB\n"
                                f"Selling price: 1 USDT ~ {sell_rate} ETB \n\n"
                                f"📢 Join Our Channel @Et_Cryptopia"
                                )
                    bot.reply_to(message, response, parse_mode="HTML")
            elif message.text.split()[2].lower() == "usdt" and message.text.split()[3].lower() == "etb":
                buy_price = round(amount * buy_rate, 3)
                sell_price = round(amount * sell_rate, 3)
                if chat_type == "private":  # User
                    response = (f"Binance Exchange USDT Rate\n"
                                f"Buy: {buy_price} ETB\n"
                                f"Sell to: {sell_price} ETB\n"
                                f"Buying price: 1 USDT ~ {buy_rate} ETB \n"
                                f"Selling price: 1 USDT ~ {sell_rate} ETB \n\n"
                                f"📢 Join Our Channel @Et_Cryptopia"
                                )
                    bot.reply_to(message, response, parse_mode="HTML", reply_markup=donate_keyboard)
                elif chat_type in ["group", "supergroup"]:  # Group
                    response = (f"Binance Exchange USDT Rate\n"
                                f"Buy: {buy_price} USDT\n"
                                f"Sell to: {sell_price} USDT\n"
                                f"Buying price: 1 USDT ~ {buy_rate} ETB\n"
                                f"Selling price: 1 USDT ~ {sell_rate} ETB \n\n"
                                f"📢 Join Our Channel @Et_Cryptopia"
                                )
                    bot.reply_to(message, response, parse_mode="HTML", reply_markup=pm_me)
        else:
            bot.send_message(message.chat.id, '''Please Use The following Format.
    /conv [amount] currency1 currency2 or
    /conv [amount] currency1 currency2 
    
    More Coins Coming Soon...''')
    else:
        bot.send_message(message.chat.id, '''Please Use The following Format.
    /conv [amount] currency1 currency2 or
    /conv [amount] currency1 currency2 

    More Coins Coming Soon...''')


# Register command handler for /broadcast
# @bot.message_handler(commands=['broadcast'])
# def handle_broadcast_command(message):
#     broadcast_command(message)

@bot.message_handler(commands=['stats'])
def stats_command(message):

    if message.chat.type == "private":
        # Get the number of users
        user_count = bot_users_collection.count_documents({})  # Assuming you still use CSV for users
        # Get the number of groups
        group_count = bot_groups_collection.count_documents({})  # Count groups in the database

        # Prepare the response message
        stats_message = f"📊 Stats:\n" \
                        f"👤 Total Users: {user_count}\n" \
                        f"👥 Total Groups: {group_count}\n"

        # Check if the sender is an admin
        admin_data = bot_admins_collection.find_one({"admin_id": message.from_user.id})
        if admin_data:
            # Get the number of admins
            admin_count = bot_admins_collection.count_documents({})
            stats_message += f"👨‍💼 Total Admins: {admin_count}\n"
        bot.reply_to(message, stats_message)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("🏠Home")

        keyboard.add(button1)

        bot.send_message(message.chat.id, "Wanna Go Back?", reply_markup=keyboard)
    else:
        bot.reply_to(message, "oops! This Command Works only in Private Chat!", reply_markup=pm_me)

@bot.message_handler(commands=['add'])
def add_admin_command(message):
    if message.chat.type== "private":
        # Check if the sender is the authorized user
        if message.from_user.id != int(AUTHORIZED_USER_ID):
            bot.reply_to(message, "❌ You are not authorized to use this command.")
            return

        # Extract the user ID of the admin to add from the message text
        try:
            added_by = message.chat.id
            new_admin_id = int(message.text.split()[1])  # Assuming the command is /add <user_id>
            bot_admins_collection.insert_one({"admin_id": new_admin_id, "added_by": message.chat.id})
            bot.reply_to(message, f"✅ User {new_admin_id} has been added as an admin.")
        except (IndexError, ValueError):
            bot.reply_to(message, "❌ Please provide a valid user ID to add as admin."
                                  "Example /add 0000000000 "
                                  "where 0000000000 is user id")
    else:
        bot.reply_to(message, "oops! This Command Works only in Private Chat!", reply_markup=pm_me)


@bot.message_handler(commands=['admins'])
def admins_command(message):
    if message.chat.type == "private":
        # Check if the sender is an admin
        admin_data = bot_admins_collection.find_one({"admin_id": message.from_user.id})
        if not admin_data:
            bot.reply_to(message, "❌ You must be an admin to use this command.")
            return

        # Retrieve the list of admins
        admins = bot_admins_collection.find()
        admin_list = [str(admin['admin_id']) for admin in admins]

        if admin_list:
            admin_list_message = "👥 Admins:\n" + "\n".join(admin_list)
        else:
            admin_list_message = "🛑 No admins found."

        bot.reply_to(message, admin_list_message)


@bot.message_handler(commands=['remove'])
def remove_admin_command(message):
    if message.chat.type == "private":

        # Check if the sender is the authorized user
        if message.from_user.id != AUTHORIZED_USER_ID:
            bot.reply_to(message, "❌ You are not authorized to use this command.")
            return

        # Extract the user ID of the admin to remove from the message text
        try:
            admin_id_to_remove = int(message.text.split()[1])  # Assuming the command is /remove <user_id>
            result = bot_admins_collection.delete_one({"admin_id": admin_id_to_remove})

            if result.deleted_count > 0:
                bot.reply_to(message, f"✅ User {admin_id_to_remove} has been removed from admins.")
            else:
                bot.reply_to(message, f"❌ User {admin_id_to_remove} is not an admin.")
        except (IndexError, ValueError):
            bot.reply_to(message, "❌ Please provide a valid user ID to remove from admin.")


# @bot.message_handler(func=lambda message: message.from_user.id in broadcast_context)
# def handle_broadcast_step(message):
#     user_id = message.from_user.id
#     step = broadcast_context[user_id]['step']
#
#     if step == 'target_audience':
#         # Store the audience choice
#         broadcast_context[user_id]['audience'] = message.text
#         # Ask for the type of message
#         markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
#         markup.add('Direct Text', 'Forward')
#         bot.reply_to(message, "📨 Choose the type of message to broadcast:", reply_markup=markup)
#         broadcast_context[user_id]['step'] = 'message_type'
#
#     elif step == 'message_type':
#         # Store the message type choice
#         broadcast_context[user_id]['message_type'] = message.text
#         if message.text == 'Direct Text':
#             bot.reply_to(message, "✏️ Please enter the text you want to broadcast:")
#             broadcast_context[user_id]['step'] = 'direct_text'
#         elif message.text == 'Forward':
#             bot.reply_to(message, "📥 Please forward the message you want to broadcast:")
#             broadcast_context[user_id]['step'] = 'forward_message'
#
#     elif step == 'direct_text':
#         # Broadcast the direct text to the selected audience
#         audience = broadcast_context[user_id]['audience']
#         text_to_broadcast = message.text
#         sent_count = send_broadcast(audience, text_to_broadcast)
#
#         # Notify the admin about the completion
#         bot.reply_to(message, f"✅ Your message has been broadcasted to {sent_count} recipients.")
#
#         # Clean up the context
#         del broadcast_context[user_id]
#
#     elif step == 'forward_message':
#         # Handle the forwarded message
#         forwarded_message = message.reply_to_message
#         if forwarded_message:
#             audience = broadcast_context[user_id]['audience']
#             sent_count = send_forwarded_broadcast(audience, forwarded_message)
#             bot.reply_to(message, f"✅ Your forwarded message has been broadcasted to {sent_count} recipients.")
#         else:
#             bot.reply_to(message, "⚠️ Please forward a message to use this option.")
#
#         # Clean up the context
#         del broadcast_context[user_id]

@bot.callback_query_handler(func=lambda call: call.data == 'check_membership')
def check_membership_callback(call):
    user_id = call.from_user.id
    if check_membership(user_id):
        # Automatically start the bot by calling start_command
        bot.answer_callback_query(call.id, "You are a member! Starting...")

        # Simulate sending /start command
        start_command(call.message)
    else:
        bot.answer_callback_query(call.id, "You are NOT a member of the required channels. Please join first.")


@bot.callback_query_handler(func=lambda call: call.data == 'donate')
def donate_callback(call):
    # Your crypto addresses
    crypto_addresses = (
        '''<b>Support Our Development!</b>

Thank you for using Binance Rates v1.0! Your support is vital for keeping this bot running smoothly and improving its features.

Currently, this bot is hosted on a free service, which can sometimes lead to performance issues. By contributing, you help us upgrade to a reliable hosting solution, ensuring <b>faster response times</b> and <b>24/7 availability</b>.

If you would like to support us, please consider donating using the addresses below:

<b>Telebirr:</b>
<code>+251904253864</code>

<b>USDT (Trc 20):</b>
<code>TXjnroubMzwx3fxqiQg2x6uNzcJUsKa5b7</code>

<b>USDT (TON Network):</b>
<code>EQD5mxRgCuRNLxKxeOjG6r14iSroLF5FtomPnet-sgP5xNJb</code>
Memo: <code>106749170</code>

<b>USDT (BEP 20):</b>
<code>0x9647bd1c80ba188f87c29f5e7949f1a1d048e026</code>

<b>USDT (ERC 20):</b>
<code>0x9647bd1c80ba188f87c29f5e7949f1a1d048e026</code>

<b>NOT (TON):</b>
<code>EQD5mxRgCuRNLxKxeOjG6r14iSroLF5FtomPnet-sgP5xNJb</code>
Memo: <code>106749170</code>

<b>DOGS (TON):</b>
<code>EQD5mxRgCuRNLxKxeOjG6r14iSroLF5FtomPnet-sgP5xNJb</code>
Memo: <code>106749170</code>

<b>Bitcoin:</b>
<code>1EkS5c1aTXrDbrbtimbCeahz8Vdi39wWyG</code>

Every contribution, no matter how small, makes a significant difference. Thank you for your generosity!

For any questions or further information, feel free to reach out!

<b>Our channel:</b> <a href="https://t.me/Et_Cryptopia">@Et_Cryptopia</a>
'''
    )

    bot.answer_callback_query(call.id, "Here are our crypto addresses:")
    bot.send_message(call.message.chat.id, crypto_addresses, parse_mode="html")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "🏠Home":
        start_command(message)
    elif message.text == "👤Profile":
        profile(message)
    elif message.text == "🆘Help":
        help_command(message)
    elif message.text == "📊Stats":
        stats_command(message)
    elif message.text == "🪙p2p Rate":
        send_binance_rate(message)
    elif message.text == "🪙Crypto News":
        coming_soon(message, "Crypto News")
    elif message.text == "📈Technical Analysis":
        coming_soon(message, "📈Technical Analysis")
    elif message.text == "⚙️Services":
        services(message)
    elif message.text == "About":
        send_about(message)
    elif message.text == "💬Comment":
        suggest_idea()
    elif message.text =="🏦Banks":
        banks_rate(message)

bot.remove_webhook()  # Remove any existing webhook
bot.set_webhook(url='secondary-drucy-bright-codes-3408871d.koyeb.app/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
    print("Running...")
    # bot.infinity_polling()
