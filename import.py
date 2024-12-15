import hashlib
import telebot
from telebot import types
from io import BytesIO
import requests
import logging
import os
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

# Replace with your actual Telegram bot token
TOKEN = '6145887818:AAES2mkvIt6XN_uB2aG4oNRpHWAzcho0Hxg'

# Replace with your group's chat ID
GROUP_CHAT_ID = -1001878276381  # Replace with your actual group chat ID
GROUP_INVITE_LINK = "https://t.me/IBMBotSupport"  # Replace with your group's invite link
MAX_PHOTO_SIZE_HD = 20 * 1024 * 1024  # 20 MB for HD images

# Replace with the actual Owner's user ID
OWNER_USER_ID = 2125687935

bot = telebot.TeleBot(TOKEN)

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Log file for user data
USER_LOG_FILE = 'users_log.txt'
LOGGED_USERS_FILE = 'logged_users.txt'  # To track users who have already started the bot

# Dictionary to temporarily store file_id to hash mappings
file_id_mapping = {}

# Load already logged users
def load_logged_users():
    if os.path.exists(LOGGED_USERS_FILE):
        with open(LOGGED_USERS_FILE, 'r') as file:
            return set(file.read().splitlines())
    return set()

# Save logged users
def save_logged_user(user_id):
    with open(LOGGED_USERS_FILE, 'a') as file:
        file.write(f"{user_id}\n")

# Log user information to a file
def log_user_info(user_id, username, first_name):
    with open(USER_LOG_FILE, 'a') as file:
        file.write(f"User ID: {user_id}, Username: @{username}, First Name: {first_name}\n")

# Send log to owner
def send_log_to_owner(image_data, action, requester_username):
    """Sends the image and action log to the owner."""
    try:
        jpeg_buffer = BytesIO()
        image_data.save(jpeg_buffer, format='JPEG')
        jpeg_buffer.seek(0)

        caption = f"Action: {action}\nRequested by @{requester_username}"
        bot.send_photo(OWNER_USER_ID, jpeg_buffer, caption=caption)
    except Exception as e:
        print(f"Error sending log to owner: {e}")

# Handle /start command
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    mention = f"<a href=\"tg://user?id={user_id}\">{first_name}</a>"

    # Check if user has already started the bot
    logged_users = load_logged_users()
    if str(user_id) in logged_users:
        bot.reply_to(
            message,
            f"Hey {mention}, welcome back! send a pic to start editing.",
            parse_mode='HTML'
        )
        return

    # Log user information and save the user ID
    log_user_info(user_id, username, first_name)
    save_logged_user(user_id)

    # Send user info to the group
    bot.send_message(
        GROUP_CHAT_ID,
        f"New user started the bot:\n\nUser ID: {user_id}\nUsername: @{username}\nFirst Name: {first_name}",
        parse_mode='HTML'
    )

    bot.reply_to(
        message,
        f"Hey {mention}, I am an image enhancer bot just send me any image & join @IBMBotSupport to use me.",
        parse_mode='HTML'
    )

@bot.message_handler(commands=['commands'])
def handle_commands(message):
    bot.reply_to(
        message,
        "Here are all available commands: /hd - to enhance the image, /bw - to convert a color image to black and white, /adjust - to adjust the image"
    )

def add_action_buttons(message):
    """Reply to an image with action buttons (HD, BW, Adjust) and custom URL buttons."""
    keyboard = types.InlineKeyboardMarkup()
    file_id = message.photo[-1].file_id

    # Hash the file_id to ensure the callback data fits within the 64-character limit
    hashed_file_id = hashlib.md5(file_id.encode()).hexdigest()

    # Store the file_id mapping for later retrieval
    file_id_mapping[hashed_file_id] = file_id

    # Add HD, BW, Adjust buttons
    hd_button = types.InlineKeyboardButton("Eɴʜᴀɴᴄᴇ", callback_data=f"hd:{hashed_file_id}")
    bw_button = types.InlineKeyboardButton("Bᴀʟᴄᴋ & Wʜɪᴛᴇ", callback_data=f"bw:{hashed_file_id}")
    adjust_button = types.InlineKeyboardButton("Aᴅɪᴜꜱᴛ", callback_data=f"adjust:{hashed_file_id}")

    keyboard.add(hd_button, bw_button, adjust_button)

    # Add custom URL buttons (IBM Bot Support, GitHub Repo)
    button1 = types.InlineKeyboardButton("𝗪𝗵𝗼𝗹𝗲𝘀𝗼𝗺𝗲 𝗖𝗶𝘁𝘆", url="https://t.me/WholesomeCity")
    button2 = types.InlineKeyboardButton("𝗢𝘄𝗻𝗲𝗱 𝗕𝘆", url="https://t.me/WholesomeCity")
    keyboard.add(button1, button2)

    bot.reply_to(
        message,
        "What can I do with this photo? Choose an option below:",
        reply_markup=keyboard
    )

@bot.message_handler(content_types=['photo'])
def handle_image_with_buttons(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    logging.debug(f"Handling message from {user_id}")

    try:
        # Check if the user is already a member of the group
        member = bot.get_chat_member(GROUP_CHAT_ID, user_id)

        # If they are a member, proceed
        if member.status in ["member", "administrator", "creator"]:
            add_action_buttons(message)
        else:
            logging.debug(f"User {user_id} is not a member, attempting to approve.")
            try:
                # Approve join request if the user is not a member
                bot.approve_chat_join_request(GROUP_CHAT_ID, user_id)
                logging.debug(f"Approved join request for {user_id}.")
                bot.reply_to(
                    message,
                    "You have been successfully added to the group. Please use the bot now to enhance your image."
                )
                add_action_buttons(message)
            except Exception as e:
                logging.error(f"Error approving join request for {user_id}: {e}")
                keyboard = types.InlineKeyboardMarkup()
                join_button = types.InlineKeyboardButton("Join the Group", url=GROUP_INVITE_LINK)
                keyboard.add(join_button)

                bot.reply_to(
                    message,
                    "Please join the group to proceed with enhancing your image.",
                    reply_markup=keyboard
                )
    except telebot.apihelper.ApiTelegramException as e:
        logging.error(f"Error checking membership status for user {user_id}: {e}")
        bot.reply_to(
            message,
            "There was an error checking your group membership. Please try again later."
        )

@bot.callback_query_handler(func=lambda call: True)
def handle_button_click(call):
    option, hashed_file_id = call.data.split(":") if ':' in call.data else (None, None)
    message_id = call.message.message_id
    chat_id = call.message.chat.id

    # Delete the original bot message
    bot.delete_message(chat_id, message_id)

    # Notify the user about processing
    processing_message = bot.send_message(chat_id, f"Processing your image for {option.upper()}...")

    # Retrieve the original file ID from the hash
    original_file_id = get_original_file_id_from_hash(hashed_file_id)

    if not original_file_id:
        bot.reply_to(chat_id, "Invalid file. Please try again.")
        return

    # Download the image using the valid file_id
    try:
        file_info = bot.get_file(original_file_id)
        image_data = bot.download_file(file_info.file_path)

        # Perform the selected action
        if option == "hd":
            enhanced_image = remini(image_data, effect='enhance')
            caption = "Image enhanced to HD."
        elif option == "bw":
            img = Image.open(BytesIO(image_data))
            enhanced_image = img.convert('L')
            caption = "Image converted to Black and White."
        elif option == "adjust":
            img = Image.open(BytesIO(image_data))
            enhanced_image = dynamic_adjust(img)
            caption = "Image adjusted."
        else:
            enhanced_image = None
            caption = "Unknown action."

        # Send the processed image
        if enhanced_image:
            output_buffer = BytesIO()
            enhanced_image.save(output_buffer, format='JPEG')
            output_buffer.seek(0)
            bot.send_photo(chat_id, output_buffer, caption=caption)

            # Send log to the owner
            send_log_to_owner(enhanced_image, option, call.from_user.username)

        # Delete the "processing" message
        bot.delete_message(chat_id, processing_message.message_id)

    except Exception as e:
        logging.error(f"Error during image processing: {e}")
        bot.reply_to(chat_id, "An error occurred while processing the image. Please try again.")

# Function to enhance image to HD quality using Vyro API
def remini(image_data, effect='enhance'):
    url = f'https://inferenceengine.vyro.ai/{effect}.vyro'
    files = {'image': ('image.jpg', image_data, 'image/jpeg')}
    headers = {
        'User-Agent': 'okhttp/4.9.3',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip'
    }

    response = requests.post(url, files=files, headers=headers)

    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    else:
        logging.error(f"Failed to enhance image: {response.text}")
        return None

def dynamic_adjust(img):
    """Adjust image dynamically based on its characteristics."""
    # Enhancing saturation, sharpness, and contrast based on the image
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.2)

    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(2.0)

    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.5)

    return img

def get_original_file_id_from_hash(hashed_file_id):
    """Retrieve the original file ID from the hash mapping."""
    return file_id_mapping.get(hashed_file_id)

# Start polling for updates
bot.polling(none_stop=True)
