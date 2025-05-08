import asyncio
import logging
import os
import random

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from flask import Flask, request
from telegram import InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler, PicklePersistence, MessageHandler, filters
)

from bot_managers.account_manager import (
    login_or_logout, set_email, set_password, login_ktmb, logout_ktmb, clear, rejected_clear, confirmed_clear
)
from bot_managers.profile_manager import (
    manage_profiles, add_email, add_password, added_profile, selected_profile, change_password, deleted_profile
)
from bot_managers.reservation_manager import (
    set_reserve, show_reserved
)
from bot_managers.station_manager import (
    manage_shortcuts, add_from_state, add_from_station, add_to_state, add_to_station,
    added_shortcut, selected_shortcut, deleted_shortcut,
    set_from_state, set_from_station, set_to_state, set_to_station
)
from bot_managers.tracking_manager import (
    set_track, cancel_tracking, view_trackings, view_single_tracking
)
from bot_managers.trip_manager import (
    set_date, set_trip
)
from utils.bot_helper import (
    strikethrough_last_message, enable_hide_keyboard_only, disable_strikethrough, is_logged_in
)
from utils.constants import (
    START,
    ADD_EMAIL, ADD_PASSWORD,
    PROFILE, SELECTED_PROFILE, CHANGE_PASSWORD,
    ADD_FROM_STATE, ADD_FROM_STATION,
    ADD_TO_STATE, ADD_TO_STATION,
    SHORTCUT, SELECTED_SHORTCUT,
    SET_EMAIL, SET_PASSWORD,
    SET_FROM_STATE, SET_FROM_STATION,
    SET_TO_STATE, SET_TO_STATION,
    SET_DATE,
    SET_TRIP,
    SET_TRACK,
    VIEW_TRACK,
    VIEW_TRACKS,
    RESERVED,
    CLEAR,
    RANDOM_REPLIES
)
from utils.constants import (
    TRACK_NEW_TRAIN,
    VIEW_TRACKING,
    ADD_NEW_PROFILE_DATA,
    ADD_NEW_SHORTCUT_DATA,
    BACK_DATA,
    YES_DATA, NO_DATA,
    CHANGE_PASSWORD_DATA,
    DELETE_PROFILE_DATA,
    DELETE_SHORTCUT_DATA,
    RESERVE_DATA,
    REFRESH_TRACKING_DATA, CANCEL_TRACKING_DATA,
    REFRESH_RESERVED_DATA, CANCEL_RESERVATION_DATA
)
from utils.constants import (
    UUID_PATTERN, DATE_PATTERN,
    LAST_MESSAGE, STATE, PROFILES
)
from utils.file_manager import (
    upload_file_to_s3, download_file_from_s3
)
from utils.keyboard_helper import (
    build_bottom_reply_markup,
    build_profiles_keyboard
)
from jobs.tracking_job_manager import (
    scheduler
)

# drty
# Environment variables
load_dotenv()
AWS_S3_BUCKET_NAME = os.getenv('AWS_S3_BUCKET_NAME')
BOT_TOKEN = os.getenv('BOT_TOKEN')
ENV = os.getenv('ENV')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger('bot')
logger.info('ENV: ' + ENV)

app = Flask(__name__)

# Initialize only once
initialized = False


# scheduler = AsyncIOScheduler()


@app.route('/', methods=['GET', 'POST'])
def webhook():
    global initialized

    if request.method == 'GET':
        return {
            'status': 'Bot is running on Hugging Face!',
            'env': ENV
        }
    elif request.method == 'POST':
        update = Update.de_json(request.get_json(force=True), application.bot)

        async def handle():
            global initialized
            if not initialized:
                await application.initialize()
                # if not scheduler.running:
                #     scheduler.start()
                #
                initialized = True
            await application.process_update(update)

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(handle())
        return {'ok': True}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await strikethrough_last_message(context)

    enable_hide_keyboard_only(context.user_data)

    message = (
        f'Hello {update.message.from_user.first_name} 👋\n'
        '\n'
        'I am KTMB Bot 🤖, you can use me to track train seat availability\n'
        '\n'
        f'{'I need your KTMB account information to get started. Don\'t worry - your information is transmitted and stored securely on Hugging Face 🤗' if not is_logged_in(context.user_data) else 'You are logged in as:\n' + context.user_data.get('email') + '\n\nDo you want to /logout?'}'
    )

    context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
        message,
        reply_markup=build_bottom_reply_markup() if is_logged_in(context.user_data) else None
    )

    if not is_logged_in(context.user_data):
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )
        await asyncio.sleep(1)  # 1 second delay
        reply_markup = InlineKeyboardMarkup(
            build_profiles_keyboard(context.user_data.get(PROFILES, {}), f'{SET_EMAIL}:')
        )
        context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
            '⬇️ Select a profile below to log in, or enter your KTMB email' if context.user_data.get(PROFILES, {})
            else 'Enter your KTMB email',
            reply_markup=reply_markup
        )
        context.user_data[STATE] = SET_EMAIL
        return SET_EMAIL

    context.user_data[STATE] = START
    return START


async def upload_conversation_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await strikethrough_last_message(context)

    disable_strikethrough(context.user_data)

    res = upload_file_to_s3('ktmb_conversation_data', AWS_S3_BUCKET_NAME, 'ktmb_conversation_data')

    message = 'Backup successful' if res else 'Backup failed'

    context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(message, reply_markup=None)

    context.user_data[STATE] = START
    return START


async def download_conversation_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await strikethrough_last_message(context)

    disable_strikethrough(context.user_data)

    res = download_file_from_s3(AWS_S3_BUCKET_NAME, 'ktmb_conversation_data', 'ktmb_conversation_data')

    message = 'Restore successful' if res else 'Restore failed'

    context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(message, reply_markup=None)

    context.user_data[STATE] = START
    return START


async def print_unknown_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    disable_strikethrough(context.user_data)

    context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(query.data, reply_markup=None)


async def print_unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    disable_strikethrough(context.user_data)

    msg = update.message
    if not msg:
        return

    index = random.randint(0, len(RANDOM_REPLIES) - 1)
    message = RANDOM_REPLIES[index]

    # Text
    if msg.text:
        # context.user_data[LAST_MESSAGE] = await msg.reply_text(msg.text)
        context.user_data[LAST_MESSAGE] = await msg.reply_text(message)

    # Photo
    elif msg.photo:
        # context.user_data[LAST_MESSAGE] = await msg.reply_photo(photo=msg.photo[-1].file_id, caption=msg.caption)
        context.user_data[LAST_MESSAGE] = await msg.reply_text(message)

    # Sticker
    elif msg.sticker:
        context.user_data[LAST_MESSAGE] = await msg.reply_sticker(sticker=msg.sticker.file_id)

    # Document
    elif msg.document:
        # context.user_data[LAST_MESSAGE] = await msg.reply_document(document=msg.document.file_id, caption=msg.caption)
        context.user_data[LAST_MESSAGE] = await msg.reply_text(message)

    # Audio
    elif msg.audio:
        # context.user_data[LAST_MESSAGE] = await msg.reply_audio(audio=msg.audio.file_id, caption=msg.caption)
        context.user_data[LAST_MESSAGE] = await msg.reply_text(message)

    # Video
    elif msg.video:
        # context.user_data[LAST_MESSAGE] = await msg.reply_video(video=msg.video.file_id, caption=msg.caption)
        context.user_data[LAST_MESSAGE] = await msg.reply_text(message)

    # Voice
    elif msg.voice:
        # context.user_data[LAST_MESSAGE] = await msg.reply_voice(voice=msg.voice.file_id)
        context.user_data[LAST_MESSAGE] = await msg.reply_text(message)

    else:
        context.user_data[LAST_MESSAGE] = await msg.reply_text(message)


# Create the Application and pass it your bot's token.
persistence = PicklePersistence(filepath='ktmb_conversation_data')
application = Application.builder().token(BOT_TOKEN).persistence(persistence).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        START: [],
        PROFILE: [
            CallbackQueryHandler(add_email, pattern=f'{PROFILE}:{ADD_NEW_PROFILE_DATA}'),
            CallbackQueryHandler(selected_profile, pattern=f'^{PROFILE}:')
        ],
        ADD_EMAIL: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, add_password)
        ],
        ADD_PASSWORD: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, added_profile)
        ],
        SELECTED_PROFILE: [
            CallbackQueryHandler(manage_profiles, pattern=f'{SELECTED_PROFILE}:{BACK_DATA}'),
            CallbackQueryHandler(change_password, pattern=f'^{CHANGE_PASSWORD_DATA}/'),
            CallbackQueryHandler(deleted_profile, pattern=f'^{DELETE_PROFILE_DATA}/')
        ],
        CHANGE_PASSWORD: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, added_profile)
        ],
        SHORTCUT: [
            CallbackQueryHandler(add_from_state, pattern=f'{SHORTCUT}:{ADD_NEW_SHORTCUT_DATA}'),
            CallbackQueryHandler(selected_shortcut, pattern=f'^{SHORTCUT}:')
        ],
        ADD_FROM_STATE: [
            CallbackQueryHandler(add_from_station, pattern=f'^{ADD_FROM_STATE}:')
        ],
        ADD_FROM_STATION: [
            CallbackQueryHandler(add_from_state, pattern=f'{ADD_FROM_STATION}:{BACK_DATA}'),
            CallbackQueryHandler(add_to_state, pattern=f'^{ADD_FROM_STATION}:')
        ],
        ADD_TO_STATE: [
            CallbackQueryHandler(add_from_station, pattern=f'{ADD_TO_STATE}:{BACK_DATA}'),
            CallbackQueryHandler(add_to_station, pattern=f'^{ADD_TO_STATE}:')
        ],
        ADD_TO_STATION: [
            CallbackQueryHandler(add_to_state, pattern=f'{ADD_TO_STATION}:{BACK_DATA}'),
            CallbackQueryHandler(added_shortcut, pattern=f'^{ADD_TO_STATION}:')
        ],
        SELECTED_SHORTCUT: [
            CallbackQueryHandler(manage_shortcuts, pattern=f'{SELECTED_SHORTCUT}:{BACK_DATA}'),
            CallbackQueryHandler(deleted_shortcut, pattern=f'^{DELETE_SHORTCUT_DATA}/')
        ],
        SET_EMAIL: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, set_password),
            CallbackQueryHandler(login_ktmb, pattern=f'^{SET_EMAIL}:')
        ],
        SET_PASSWORD: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, login_ktmb)
        ],
        SET_FROM_STATE: [
            CallbackQueryHandler(set_date, pattern=f'^{SET_FROM_STATE}:{UUID_PATTERN}'),
            CallbackQueryHandler(set_from_station, pattern=f'^{SET_FROM_STATE}:')
        ],
        SET_FROM_STATION: [
            CallbackQueryHandler(set_from_state, pattern=f'{SET_FROM_STATION}:{BACK_DATA}'),
            CallbackQueryHandler(set_to_state, pattern=f'^{SET_FROM_STATION}:')
        ],
        SET_TO_STATE: [
            CallbackQueryHandler(set_from_station, pattern=f'{SET_TO_STATE}:{BACK_DATA}'),
            CallbackQueryHandler(set_to_station, pattern=f'^{SET_TO_STATE}:')
        ],
        SET_TO_STATION: {
            CallbackQueryHandler(set_to_state, pattern=f'{SET_TO_STATION}:{BACK_DATA}'),
            CallbackQueryHandler(set_date, pattern=f'^{SET_TO_STATION}:')
        },
        SET_DATE: [
            CallbackQueryHandler(set_to_station, pattern=f'{SET_DATE}:{BACK_DATA}'),
            CallbackQueryHandler(set_trip, pattern=f'^{SET_DATE}:'),
            MessageHandler(filters.Regex(f'^{DATE_PATTERN}$'), set_trip)
        ],
        SET_TRIP: [
            CallbackQueryHandler(set_date, pattern=f'{SET_TRIP}:{BACK_DATA}'),
            CallbackQueryHandler(set_track, pattern=f'^{SET_TRIP}:')
        ],
        SET_TRACK: [
            CallbackQueryHandler(set_trip, pattern=f'{SET_TRACK}:{BACK_DATA}'),
            CallbackQueryHandler(set_reserve, pattern=f'^{SET_TRACK}:-?\\d+$')
        ],
        VIEW_TRACK: [
            CallbackQueryHandler(view_trackings, pattern=f'{VIEW_TRACK}:{BACK_DATA}'),
            CallbackQueryHandler(show_reserved, pattern=f'^{RESERVE_DATA}/{UUID_PATTERN}$'),
            CallbackQueryHandler(set_reserve, pattern=f'^{REFRESH_TRACKING_DATA}/{UUID_PATTERN}$'),
            CallbackQueryHandler(cancel_tracking, pattern=f'^{CANCEL_TRACKING_DATA}/{UUID_PATTERN}$')
        ],
        VIEW_TRACKS: [
            CallbackQueryHandler(view_single_tracking, pattern=f'^{VIEW_TRACKS}:{UUID_PATTERN}$')
        ],
        RESERVED: [
            CallbackQueryHandler(show_reserved, pattern=f'^{REFRESH_RESERVED_DATA}/{UUID_PATTERN}$'),
            CallbackQueryHandler(set_reserve, pattern=f'^{CANCEL_RESERVATION_DATA}/{UUID_PATTERN}$')
        ],
        CLEAR: [
            CallbackQueryHandler(rejected_clear, pattern=f'{CLEAR}:{NO_DATA}$'),
            CallbackQueryHandler(confirmed_clear, pattern=f'{CLEAR}:{YES_DATA}$')
        ]
    },
    fallbacks=[
        CommandHandler('start', start),
        CommandHandler('login_logout', login_or_logout),
        CommandHandler('login', set_email),
        CommandHandler('logout', logout_ktmb),
        CommandHandler('profile', manage_profiles),
        CommandHandler('shortcut', manage_shortcuts),
        CommandHandler('clear', clear),
        CommandHandler('backup', upload_conversation_data),
        CommandHandler('restore', download_conversation_data),
        MessageHandler(filters.Text([TRACK_NEW_TRAIN]), set_from_state),
        MessageHandler(filters.Text([VIEW_TRACKING]), view_trackings),
        # CallbackQueryHandler(print_unknown_callback),
        MessageHandler(filters.ALL, print_unknown_message)
    ],
    name='ktmb_conversation',
    persistent=True
)

# Add ConversationHandler to application that will be used for handling updates
application.add_handler(conv_handler)

if ENV == 'DEBUG':
    # Run the bot until the user presses Ctrl-C
    # Opens a long-running thread, not supported in Hugging Face Spaces, use webhooks instead
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    # if not scheduler.running:
    #     scheduler.start()

    # Ensure cleanup on shutdown
    # application.stop()  # Stops the bot gracefully
    # scheduler.shutdown()  # Stops the scheduler
