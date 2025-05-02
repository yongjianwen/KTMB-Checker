import asyncio
import json
import logging
import os
import random
import re
import uuid
from datetime import datetime, timedelta, time

import pytz
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from flask import Flask, request
from telegram import InlineKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler, PicklePersistence, MessageHandler, filters
)

from bot_managers.profile_manager import (
    manage_profiles, add_email, add_password, added_profile, selected_profile, change_password, deleted_profile
)
from bot_managers.station_manager import (
    manage_shortcuts, add_from_state, add_from_station, add_to_state, add_to_station,
    added_shortcut, selected_shortcut, deleted_shortcut,
    set_from_state, set_from_station, set_to_state, set_to_station
)
from services.ktmb import (
    login, logout,
    get_stations,
    get_trips,
    reserve_by_price,
    cancel_reservation
)
from utils.bot_helper import (
    strikethrough_last_message, show_error_inline, show_error_reply,
    enable_strikethrough, enable_hide_keyboard_only, disable_strikethrough,
    is_logged_in
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
    REFRESH_TRACKING_DATA,
    CANCEL_TRACKING_DATA,
    REFRESH_RESERVED_DATA,
    CANCEL_RESERVATION_DATA
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
    RESERVED,
    CLEAR,
    Title,
    RANDOM_REPLIES
)
from utils.constants import (
    UUID_PATTERN, DATE_PATTERN,
    COOKIE, TOKEN, LAST_MESSAGE, STATE, TO_STRIKETHROUGH, TO_HIDE_KEYBOARD,
    PROFILES, SHORTCUTS,
    TRANSACTION, VOLATILE, STATIONS_DATA, TRACKING_LIST,
    FROM_STATE_NAME, FROM_STATION_ID, FROM_STATION_NAME,
    TO_STATE_NAME, TO_STATION_ID, TO_STATION_NAME,
    DATE, DEPARTURE_TIME, ARRIVAL_TIME, PRICE,
    SEARCH_DATA, TRIPS_DATA, TRIP_DATA, LAYOUT_DATA, BOOKING_DATA, OVERALL_PRICES, PARTIAL_CONTENT,
    TRACKING_UUID,
    RESERVED_SEAT,
    SEATS_LEFT_BY_PRICES,
    LAST_REMINDED
)
from utils.file_manager import (
    upload_file_to_s3, download_file_from_s3
)
from utils.keyboard_helper import (
    build_bottom_reply_markup,
    build_profiles_keyboard, build_dates_keyboard, build_times_keyboard,
    build_tracking_prices_keyboard,
    build_tracked_actions_keyboard,
    build_reserved_actions_keyboard,
)
from utils.ktmb_helper import (
    get_station_by_id, get_seats_contents
)
from utils.message_helper import (
    get_tracking_content
)
from bot_managers.trip_manager import (
    set_date, set_trip
)
from bot_managers.reservation_manager import (
    set_reserve, show_reserved
)
from utils.utils import (
    utc_to_malaysia_time
)
from bot_managers.account_manager import (
    login_or_logout, set_email, set_password, login_ktmb, logout_ktmb, clear, rejected_clear, confirmed_clear
)
from bot_managers.tracking_manager import (
    set_track, cancel_tracking, view_tracking
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

scheduler = BackgroundScheduler()
scheduler.start()


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
                # restore_jobs(application)
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
            '⬇️ Select a profile below to log in, or enter your KTMB email', reply_markup=reply_markup)
        context.user_data[STATE] = SET_EMAIL
        return SET_EMAIL

    context.user_data[STATE] = START
    return START


INTERVALS = [15, 15, 30, 30, 60, 60, 120, 120, 300, 300, 600, 600, 900, 900, 1800, 1800]
INTERVALS = [i - 5 for i in INTERVALS]
DANGER_NUM = 50
LESS_THAN_50 = 600
LESS_THAN_10 = 60


def sync_alarm_wrapper(*args, **kwargs):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(alarm(*args, **kwargs))
    finally:
        loop.close()


async def alarm(context: ContextTypes.DEFAULT_TYPE, data, chat_id) -> None:
    logger.info('Job run')

    now_time = datetime.now().time()
    start_time = time(0, 0)
    end_time = time(15, 37)
    if start_time <= now_time <= end_time:
        logger.info('Skipped job')
        return

    # job = context.job

    session = requests.Session()
    # session.cookies.update(job.data.get(COOKIE))
    session.cookies.update(data.get(COOKIE))

    res = get_stations(session)
    if not res.get('status'):
        logger.info('get_stations error')
        return

    stations_data = res.get(STATIONS_DATA)

    # t = job.data.get('data')
    t = data.get('data')
    tracking_uuid = t.get(TRACKING_UUID)
    from_state_name = t.get(FROM_STATE_NAME)
    from_station_id = t.get(FROM_STATION_ID)
    from_station_name = t.get(FROM_STATION_NAME)
    to_state_name = t.get(TO_STATE_NAME)
    to_station_id = t.get(TO_STATION_ID)
    to_station_name = t.get(TO_STATION_NAME)
    date = t.get(DATE)
    departure_time = t.get(DEPARTURE_TIME)
    arrival_time = t.get(ARRIVAL_TIME)
    price = t.get(PRICE)
    reserved_seat = t.get(RESERVED_SEAT)
    initial_seats_left_by_prices = t.get(SEATS_LEFT_BY_PRICES)
    last_reminded = t.get(LAST_REMINDED)

    year, month, day = date.split('-')

    res = get_trips(
        session,
        datetime(int(year), int(month), int(day)),
        get_station_by_id(stations_data, from_station_id),
        get_station_by_id(stations_data, to_station_id),
        # job.data.get(TOKEN)
        data.get(TOKEN)
    )
    if not res.get('status'):
        logger.info('get_trips error')
        return
        # logger.info('trips_res:', trips_res)

    search_data = res.get('search_data')
    trips_data = json.loads(json.dumps(res.get('trips_data')))
    trip = next(t for t in trips_data if t.get('departure_time') == departure_time)
    trip_data = trip.get(TRIP_DATA)

    res = await get_seats_contents(
        search_data,
        trip_data,
        session,
        # job.data.get(TOKEN),
        data.get(TOKEN)
    )
    if not res.get('status'):
        logger.info('get_seats_contents error')
        return

    partial_content = res.get(PARTIAL_CONTENT)
    new_seats_left_by_prices = res.get(SEATS_LEFT_BY_PRICES)

    # logger.info('initial:', initial_seats_left_by_prices)
    # logger.info('new:', new_seats_left_by_prices)

    to_remind = False
    reason = ''
    # selected a price and initial was 0
    if price != -1 and str(price) not in initial_seats_left_by_prices:
        logger.info('A')
        if str(price) in new_seats_left_by_prices:
            logger.info('B')
            to_remind = True
            reason = '‼️ New seat(s) has appeared!'
    # selected any price and initial was 0
    elif price == -1 and not initial_seats_left_by_prices:
        logger.info('C')
        if new_seats_left_by_prices:
            logger.info('D')
            to_remind = True
            reason = '‼️ New seat(s) has appeared!'
    else:
        logger.info('E')
        # selected a price and initial was not 0
        for p, s in new_seats_left_by_prices.items():
            logger.info('F')
            # logger.info(type(p))
            # logger.info(type(price))
            if p == str(price) and s < initial_seats_left_by_prices.get(p):
                logger.info('G')
                to_remind = True
                reason = '‼️ Tickets are selling out!'
                break
        # selected any price and initial was not 0
        for p, s in new_seats_left_by_prices.items():
            logger.info('H')
            if price == -1 and s < initial_seats_left_by_prices.get(p, 0):
                logger.info('I')
                to_remind = True
                reason = '‼️ Tickets are selling out!'
                break
    # logger.info('to_remind:', to_remind)
    # logger.info(last_reminded + timedelta(seconds=60*15) < datetime.now())

    if not to_remind:
        t['intervals_index'] = 0

    count = t.get('intervals_index', 0)

    logger.info('to_remind: ' + str(to_remind))
    logger.info('intervals_index: ' + str(t.get('intervals_index')))
    logger.info('intervals: ' + str(INTERVALS[count]))
    logger.info('last_reminded: ' + str(last_reminded))
    logger.info(str(initial_seats_left_by_prices))

    if to_remind and last_reminded + timedelta(seconds=INTERVALS[count]) < datetime.now():
        logger.info('remind success')
        t[LAST_REMINDED] = datetime.now()
        t['intervals_index'] = t.get('intervals_index', 0) + 1
        if reserved_seat is None:
            price_message = 'any price' if price == -1 else f'RM {price}'
            await context.bot.send_message(
                # job.chat_id,
                chat_id,
                text=(
                    f'{get_tracking_content(
                        t,
                        {PARTIAL_CONTENT: partial_content},
                        reason
                    )}'
                    '\n'
                    f'<i>Refreshed at: {utc_to_malaysia_time(datetime.now()).strftime('%H:%M:%S')}</i>\n'
                    '\n'
                    f'<b>Reserve a random seat of {price_message}?</b>'
                ),
                reply_markup=None,
                parse_mode='HTML'
            )
        else:
            await context.bot.send_message(
                # job.chat_id,
                chat_id,
                text=(
                    f'{get_tracking_content(
                        {
                            **t,
                            PARTIAL_CONTENT: partial_content
                        },
                        {},
                        'Alarm'
                    )}'
                    '\n'
                    'Seat reserved successfully!\n'
                    '\n'
                    f'Coach: <b>{reserved_seat.get('CoachLabel')}</b>\n'
                    f'Seat: <b>{reserved_seat.get('SeatNo')}</b>\n'
                    f'Price: <b>RM {reserved_seat.get('Price')}</b>'
                ),
                reply_markup=None,
                parse_mode='HTML'
            )


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


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
            CallbackQueryHandler(show_reserved, pattern=f'^{RESERVE_DATA}/{UUID_PATTERN}$'),
            CallbackQueryHandler(set_reserve, pattern=f'^{REFRESH_TRACKING_DATA}/{UUID_PATTERN}$'),
            CallbackQueryHandler(cancel_tracking, pattern=f'^{CANCEL_TRACKING_DATA}/{UUID_PATTERN}$')
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
        MessageHandler(filters.Text([VIEW_TRACKING]), view_tracking),
        CallbackQueryHandler(print_unknown_callback),
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
