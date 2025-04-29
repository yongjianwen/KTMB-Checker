import asyncio
import json
import logging
import os
import re
import uuid
from datetime import datetime, timedelta, time

import pytz
import requests
from dotenv import load_dotenv
from flask import Flask, request
from telegram import InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler, PicklePersistence, MessageHandler, filters,
)
from apscheduler.schedulers.background import BackgroundScheduler

from bot_helper import get_seats_contents, cancel_last_message, reply_error, clear_session_data, display_error_inline
from ktmb import get_station_by_id, login, get_trips, logout, get_stations, reserve_by_price, cancel_reservation
from utils import BACK_DATA, COOKIE, TOKEN, LAST_MESSAGE, TO_STRIKETHROUGH, STATIONS_DATA, FROM_STATE_NAME, \
    TO_STATE_NAME, FROM_STATION_ID, TO_STATION_ID, FROM_STATION_NAME, TO_STATION_NAME, DATE, PARTIAL_CONTENT, \
    SEARCH_DATA, TRIPS_DATA, TRIP_DATA, DEPARTURE_TIME, ARRIVAL_TIME, LAYOUT_DATA, PRICE, TRACKING_LIST, RESERVED_SEAT, \
    Title, UUID_PATTERN, TO_HIDE_KEYBOARD, build_profile_keyboard, build_manage_profile_keyboard, \
    build_shortcut_keyboard, build_manage_shortcut_keyboard
from utils import build_state_keyboard, generate_station_keyboard, generate_friday_keyboard, generate_trips_keyboard, \
    generate_tracking_keyboard, generate_reserve_keyboard, generate_reserved_keyboard, get_tracking_content

# Environment variables
load_dotenv()
ENV = os.getenv('ENV')
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger('bot')
logger.info('ENV: ' + ENV)

# Stages
(
    START,
    ADD_PROFILE, ADD_PROFILE_PASSWORD,
    MANAGE_PROFILE, SELECTED_PROFILE, CHANGE_PROFILE_PASSWORD,
    ADD_FROM_STATE, ADD_FROM_STATION,
    ADD_TO_STATE, ADD_TO_STATION,
    MANAGE_SHORTCUT, SELECTED_SHORTCUT,
    SET_EMAIL, SET_PASSWORD,
    SET_FROM_STATE, SET_FROM_STATION,
    SET_TO_STATE, SET_TO_STATION,
    SET_DATE,
    SET_TRIP,
    SET_TRACK,
    VIEW_TRACK,
    RESERVED
) = range(23)

# Bottom keyboard
NEW, VIEW = 'Track New Train 🚈', '👀 View Tracking'
bottom_keyboard = [
    [NEW, VIEW]
]
bottom_reply_markup = ReplyKeyboardMarkup(bottom_keyboard, one_time_keyboard=False, resize_keyboard=True)

app = Flask(__name__)

# Initialize only once
initialized = False

MALAYSIA_TZ = pytz.timezone('Asia/Kuala_Lumpur')


def my_job(context, data, chat_id):
    logger.info("Job is running")


scheduler = BackgroundScheduler()
# scheduler.add_job(my_job, 'interval', seconds=10)
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


def is_logged_in(data):
    logged_in = False
    if COOKIE in data and data.get(COOKIE):
        logged_in = True
    return logged_in


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await cancel_last_message(context)

    enable_hide_keyboard_only(context.user_data)

    if 'transaction_temp' not in context.user_data:
        context.user_data['transaction_temp'] = {}

    message = (
        f'Hello {update.message.from_user.first_name} 👋\n'
        '\n'
        'I am KTMB Bot 🤖, you can use me to track train seat availability\n'
        '\n'
        f'{'I need your KTMB account information to get started. Don\'t worry - your information is transmitted and stored securely on Hugging Face 🤗' if not is_logged_in(context.user_data) else 'You are logged in as:\n' + context.user_data.get('email') + '\n\nDo you want to /logout?'}'
    )

    context.user_data[LAST_MESSAGE] = await update.message.reply_text(
        message,
        reply_markup=bottom_reply_markup if is_logged_in(context.user_data) else None
    )

    if not is_logged_in(context.user_data):
        await asyncio.sleep(1)  # 1 second delay
        reply_markup = InlineKeyboardMarkup(
            build_profile_keyboard(context.user_data.get('profiles', {}), 'set_email:')
        )
        context.user_data[LAST_MESSAGE] = await update.message.reply_text(
            'Enter your KTMB email, or select a profile to log in', reply_markup=reply_markup)
        context.user_data['state'] = SET_EMAIL
        return SET_EMAIL

    context.user_data['state'] = START
    return START


async def add_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await cancel_last_message(context)

    disable_any_cancel(context.user_data)

    context.user_data[LAST_MESSAGE] = await update.message.reply_text(
        'Key in email',
        reply_markup=None
    )

    context.user_data['state'] = ADD_PROFILE
    return ADD_PROFILE


async def add_profile_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email_temp = update.message.text
    context.user_data['email_temp'] = email_temp

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await cancel_last_message(context)

    disable_any_cancel(context.user_data)

    if context.user_data.get('profiles', {}).get(email_temp):
        context.user_data[LAST_MESSAGE] = await update.message.reply_text(
            'Email already exists. /manage instead? Or key in new email',
            reply_markup=None
        )
        context.user_data['state'] = ADD_PROFILE
        return ADD_PROFILE
    else:
        context.user_data[LAST_MESSAGE] = await update.message.reply_text(
            'Key in password',
            reply_markup=None
        )
        context.user_data['state'] = ADD_PROFILE_PASSWORD
        return ADD_PROFILE_PASSWORD


async def added_profile_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    password_temp = update.message.text
    context.user_data['password_temp'] = password_temp

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await cancel_last_message(context)

    disable_any_cancel(context.user_data)

    if 'profiles' not in context.user_data:
        context.user_data['profiles'] = {}

    context.user_data.get('profiles', {})[context.user_data.get('email_temp')] = password_temp
    context.user_data.pop('email_temp', None)
    context.user_data.pop('password_temp', None)

    context.user_data[LAST_MESSAGE] = await update.message.reply_text(
        'Success',
        reply_markup=None
    )

    context.user_data['state'] = START
    return START


async def manage_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await cancel_last_message(context)

    enable_hide_keyboard_only(context.user_data)

    reply_markup = InlineKeyboardMarkup(
        build_profile_keyboard(context.user_data.get('profiles', {}), 'manage_profile:')
    )
    message = (
        'Select a profile to manage'
    )

    context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    context.user_data['state'] = MANAGE_PROFILE
    return MANAGE_PROFILE


async def selected_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    match = re.search('manage_profile:(.*)', query.data)
    if match:
        context.user_data['email_temp'] = match.group(1)
    else:
        return context.user_data.get('state')

    await cancel_last_message(context)

    enable_hide_keyboard_only(context.user_data)

    reply_markup = InlineKeyboardMarkup(
        build_manage_profile_keyboard(context.user_data['email_temp'])
    )
    message = (
        'Choose an action'
    )

    context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    context.user_data['state'] = SELECTED_PROFILE
    return SELECTED_PROFILE


async def change_profile_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await cancel_last_message(context)

    disable_any_cancel(context.user_data)

    context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
        'Key in new password',
        reply_markup=None,
        parse_mode='HTML'
    )

    context.user_data['state'] = CHANGE_PROFILE_PASSWORD
    return CHANGE_PROFILE_PASSWORD


async def deleted_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await cancel_last_message(context)

    disable_any_cancel(context.user_data)

    context.user_data.get('profiles', {}).pop(context.user_data.get('email_temp'), None)

    context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
        'Profile deleted',
        reply_markup=None,
        parse_mode='HTML'
    )

    context.user_data['state'] = START
    return START


async def add_from_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is None:
        # From bottom keyboard
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )
        await cancel_last_message(context)
    else:
        await query.answer()

    enable_hide_keyboard_only(context.user_data)
    context.user_data['transaction_temp'] = {}

    session = requests.Session()
    if COOKIE in context.user_data:
        session.cookies.update(context.user_data.get(COOKIE))

    res = get_stations(session)
    if not res.get('status'):
        enable_cancel(context.user_data)
        await display_error_inline(context, res, None)
        context.user_data['state'] = START
        return START

    context.user_data[STATIONS_DATA] = res.get(STATIONS_DATA)

    reply_markup = InlineKeyboardMarkup(
        build_state_keyboard(context.user_data.get(STATIONS_DATA, []), {}, 'add_from_state:'))
    message = (
        f'{get_tracking_content(context.user_data.get('transaction', {}), {})}'
        '\n'
        'Select departure state'
    )

    if query is None:
        # From bottom keyboard
        context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        # From inline keyboard
        context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    context.user_data['state'] = ADD_FROM_STATE
    return ADD_FROM_STATE


async def add_from_station(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data != 'add_to_state:' + BACK_DATA:
        match = re.search('add_from_state:(.*)', query.data)
        if match:
            context.user_data.get('transaction_temp', {})[FROM_STATE_NAME] = match.group(1)
        else:
            return context.user_data.get('state')

    enable_hide_keyboard_only(context.user_data)
    context.user_data.get('transaction_temp', {}).pop(FROM_STATION_ID, None)
    context.user_data.get('transaction_temp', {}).pop(FROM_STATION_NAME, None)

    reply_markup = InlineKeyboardMarkup(
        generate_station_keyboard(
            context.user_data.get(STATIONS_DATA, []),
            context.user_data.get('transaction_temp', {}).get(FROM_STATE_NAME),
            'add_from_station:',
            True
        )
    )
    message = (
        f'{get_tracking_content(context.user_data.get('transaction_temp', {}), {})}'
    )

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    context.user_data['state'] = ADD_FROM_STATION
    return ADD_FROM_STATION


async def add_to_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data != 'add_to_station:' + BACK_DATA:
        match = re.search('add_from_station:(.*)', query.data)
        if match:
            context.user_data.get('transaction_temp', {})[FROM_STATION_ID] = match.group(1)
            context.user_data.get('transaction_temp', {})[FROM_STATION_NAME] = get_station_by_id(
                context.user_data.get(STATIONS_DATA, []),
                context.user_data.get('transaction_temp', {}).get(FROM_STATION_ID)
            ).get('Description')
        else:
            return context.user_data.get('state')

    enable_hide_keyboard_only(context.user_data)
    context.user_data.get('transaction_temp', {}).pop(TO_STATE_NAME, None)

    reply_markup = InlineKeyboardMarkup(
        build_state_keyboard(context.user_data.get(STATIONS_DATA, []), {}, 'add_to_state:', True))
    message = (
        f'{get_tracking_content(context.user_data.get('transaction_temp', {}), {})}'
        '\n'
        'Select destination state'
    )

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    context.user_data['state'] = ADD_TO_STATE
    return ADD_TO_STATE


async def add_to_station(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    match = re.search('add_to_state:(.*)', query.data)
    if match:
        context.user_data.get('transaction_temp', {})[TO_STATE_NAME] = match.group(1)
    else:
        return context.user_data.get('state')

    enable_cancel(context.user_data)
    context.user_data.get('transaction_temp', {}).pop(TO_STATION_ID, None)
    context.user_data.get('transaction_temp', {}).pop(TO_STATION_NAME, None)

    reply_markup = InlineKeyboardMarkup(
        generate_station_keyboard(
            context.user_data.get(STATIONS_DATA, []),
            context.user_data.get('transaction_temp', {}).get(TO_STATE_NAME),
            'add_to_station:',
            True
        )
    )
    message = (
        f'{get_tracking_content(context.user_data.get('transaction_temp', {}), {})}'
    )

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    context.user_data['state'] = ADD_TO_STATION
    return ADD_TO_STATION


async def added_shortcut(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    match = re.search('add_to_station:(.*)', query.data)
    if match:
        context.user_data.get('transaction_temp', {})[TO_STATION_ID] = match.group(1)
        context.user_data.get('transaction_temp', {})[TO_STATION_NAME] = get_station_by_id(
            context.user_data.get(STATIONS_DATA, []), context.user_data.get('transaction_temp', {})[TO_STATION_ID]
        ).get('Description')
    else:
        return context.user_data.get('state')

    enable_hide_keyboard_only(context.user_data)

    if 'shortcuts' not in context.user_data:
        context.user_data['shortcuts'] = {}

    temp = context.user_data.get('transaction_temp', {})
    for shortcut in context.user_data.get('shortcuts', {}).values():
        if shortcut.get(FROM_STATE_NAME) == temp.get(FROM_STATE_NAME) \
                and shortcut.get(FROM_STATION_ID) == temp.get(FROM_STATION_ID) \
                and shortcut.get(FROM_STATION_NAME) == temp.get(FROM_STATION_NAME) \
                and shortcut.get(TO_STATE_NAME) == temp.get(TO_STATE_NAME) \
                and shortcut.get(TO_STATION_ID) == temp.get(TO_STATION_ID) \
                and shortcut.get(TO_STATION_NAME) == temp.get(TO_STATION_NAME):
            reply_markup = InlineKeyboardMarkup(
                generate_station_keyboard(
                    context.user_data.get(STATIONS_DATA, []),
                    context.user_data.get('transaction_temp', {}).get(TO_STATE_NAME),
                    'add_to_station:',
                    True
                )
            )
            message = (
                f'{get_tracking_content(context.user_data.get('transaction_temp', {}), {})}'
                '\n'
                'Shortcut already exists. /manage_shortcut instead? Or select a different one'
            )
            context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
                message,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            context.user_data['state'] = ADD_TO_STATION
            return ADD_TO_STATION

    shortcut_uuid = uuid.uuid4()
    context.user_data.get('shortcuts', {})[shortcut_uuid] = {
        FROM_STATE_NAME: context.user_data.get('transaction_temp', {})[FROM_STATE_NAME],
        FROM_STATION_ID: context.user_data.get('transaction_temp', {})[FROM_STATION_ID],
        FROM_STATION_NAME: context.user_data.get('transaction_temp', {})[FROM_STATION_NAME],
        TO_STATE_NAME: context.user_data.get('transaction_temp', {})[TO_STATE_NAME],
        TO_STATION_ID: context.user_data.get('transaction_temp', {})[TO_STATION_ID],
        TO_STATION_NAME: context.user_data.get('transaction_temp', {})[TO_STATION_NAME]
    }
    context.user_data.pop('transaction_temp', None)

    message = (
        f'{get_tracking_content(context.user_data.get('transaction_temp', {}), {})}'
        '\n'
        'Success'
    )

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        message,
        reply_markup=None,
        parse_mode='HTML'
    )

    context.user_data['state'] = START
    return START


async def manage_shortcut(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await cancel_last_message(context)

    enable_hide_keyboard_only(context.user_data)

    reply_markup = InlineKeyboardMarkup(
        build_shortcut_keyboard(context.user_data.get('shortcuts', {}), 'manage_shortcut:')
    )
    message = (
        'Select a shortcut to manage'
    )

    context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    context.user_data['state'] = MANAGE_SHORTCUT
    return MANAGE_SHORTCUT


async def selected_shortcut(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    match = re.search('manage_shortcut:(.*)', query.data)
    if match:
        shortcut_uuid = match.group(1)
    else:
        return context.user_data.get('state')

    await cancel_last_message(context)

    enable_hide_keyboard_only(context.user_data)

    reply_markup = InlineKeyboardMarkup(
        build_manage_shortcut_keyboard(shortcut_uuid)
    )
    message = (
        'Choose an action'
    )

    context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    context.user_data['state'] = SELECTED_SHORTCUT
    return SELECTED_SHORTCUT


async def deleted_shortcut(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    match = re.search('Delete Shortcut/(.*)', query.data)
    if match:
        shortcut_uuid = match.group(1)
    else:
        return context.user_data.get('state')

    await cancel_last_message(context)

    disable_any_cancel(context.user_data)

    # logger.info(context.user_data.get('shortcuts', {}))
    # logger.info(shortcut_uuid)
    context.user_data.get('shortcuts', {}).pop(uuid.UUID(shortcut_uuid), None)
    # temp = next(t for t in context.user_data.get('shortcuts', {}).keys() if t == uuid.UUID(shortcut_uuid))
    # context.user_data['shortcuts'] = [
    #     shortcut for shortcut in context.user_data.get('shortcuts', {}) if not
    #     (
    #             shortcut.get(FROM_STATE_NAME) == temp.get(FROM_STATE_NAME)
    #             and shortcut.get(FROM_STATION_ID) == temp.get(FROM_STATION_ID)
    #             and shortcut.get(FROM_STATION_NAME) == temp.get(FROM_STATION_NAME)
    #             and shortcut.get(TO_STATE_NAME) == temp.get(TO_STATE_NAME)
    #             and shortcut.get(TO_STATION_ID) == temp.get(TO_STATION_ID)
    #             and shortcut.get(TO_STATION_NAME) == temp.get(TO_STATION_NAME)
    #     )
    # ]
    # context.user_data.get('shortcuts', []).pop(context.user_data.get(uuid.UUID(shortcut_uuid)), None)

    context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
        'Shortcut deleted',
        reply_markup=None,
        parse_mode='HTML'
    )

    context.user_data['state'] = START
    return START


async def set_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await cancel_last_message(context)

    enable_hide_keyboard_only(context.user_data)

    if is_logged_in(context.user_data):
        context.user_data[LAST_MESSAGE] = await update.message.reply_text(
            'Already logged in as:\n' + context.user_data.get('email') + '\n\nDo you want to /logout?',
            reply_markup=None
        )
        context.user_data['state'] = START
        return START
    else:
        reply_markup = InlineKeyboardMarkup(
            build_profile_keyboard(context.user_data.get('profiles', {}), 'set_email:')
        )
        context.user_data[LAST_MESSAGE] = await update.message.reply_text(
            'Enter your KTMB email, or select a profile to log in', reply_markup=reply_markup)
        context.user_data['state'] = SET_EMAIL
        return SET_EMAIL


async def set_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['email'] = update.message.text

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await cancel_last_message(context)

    disable_any_cancel(context.user_data)

    context.user_data[LAST_MESSAGE] = await update.message.reply_text('Enter your KTMB password', reply_markup=None)

    context.user_data['state'] = SET_PASSWORD
    return SET_PASSWORD


async def login_ktmb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is None:
        password = update.message.text
    else:
        await query.answer()
        match = re.search('set_email:(.*)', query.data)  # drty
        if match:
            email = match.group(1)
            context.user_data['email'] = email
            password = context.user_data.get('profiles', {}).get(email)
        else:
            return context.user_data.get('state')

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await cancel_last_message(context)

    disable_any_cancel(context.user_data)

    session = requests.Session()
    res = login(session, context.user_data.get('email'), password)

    if res.get('status'):
        context.user_data[COOKIE] = session.cookies
        context.user_data[TOKEN] = res.get('token')
        context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
            'Logged in successfully',
            reply_markup=bottom_reply_markup
        )
        context.user_data['state'] = START
        return START
    else:
        context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(res.get('error'), reply_markup=None)
        context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text('Re-enter your KTMB password',
                                                                                    reply_markup=None)
        context.user_data['state'] = SET_PASSWORD
        return SET_PASSWORD


async def logout_ktmb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await cancel_last_message(context)

    disable_any_cancel(context.user_data)

    session = requests.Session()
    if COOKIE in context.user_data:
        session.cookies.update(context.user_data.get(COOKIE))

        clear_session_data(context)
        # clear_temp_data(context)
        context.user_data.pop('transaction', None)

        res = logout(session)

        message = 'Logout executed\n\nYou can /login again' if res.get('status') else res.get('error')

        context.user_data[LAST_MESSAGE] = await update.message.reply_text(message, reply_markup=ReplyKeyboardRemove())

        context.user_data['state'] = START
        return START

    clear_session_data(context)
    # clear_temp_data(context)
    context.user_data.pop('transaction', None)

    message = 'Already logged out\n\nYou can /login again'

    context.user_data[LAST_MESSAGE] = await update.message.reply_text(message, reply_markup=ReplyKeyboardRemove())

    context.user_data['state'] = START
    return START


async def set_from_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is None:
        # From bottom keyboard
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )
        await cancel_last_message(context)
    else:
        await query.answer()

    enable_cancel(context.user_data)
    context.user_data['transaction'] = {}
    context.user_data['volatile'] = {}
    # context.user_data.get('transaction', {}).pop(FROM_STATE_NAME, None)

    session = requests.Session()
    if COOKIE in context.user_data:
        session.cookies.update(context.user_data.get(COOKIE))

    res = get_stations(session)
    if not res.get('status'):
        enable_cancel(context.user_data)
        await display_error_inline(context, res, None)
        context.user_data['state'] = SET_FROM_STATE
        return SET_FROM_STATE

    context.user_data[STATIONS_DATA] = res.get(STATIONS_DATA)

    reply_markup = InlineKeyboardMarkup(
        build_state_keyboard(
            context.user_data.get(STATIONS_DATA, []),
            context.user_data.get('shortcuts', {}),
            'set_from_state:'
        )
    )
    message = (
        f'{get_tracking_content(context.user_data.get('transaction', {}), context.user_data.get('volatile', {}))}'
        '\n'
        'Where are you departing from?'
    )

    if query is None:
        # From bottom keyboard
        context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        # From inline keyboard
        context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    context.user_data['state'] = SET_FROM_STATE
    return SET_FROM_STATE


async def set_from_station(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data != 'set_to_state:' + BACK_DATA:
        match = re.search('set_from_state:(.*)', query.data)
        if match:
            context.user_data.get('transaction', {})[FROM_STATE_NAME] = match.group(1)
        else:
            return context.user_data.get('state')

    enable_cancel(context.user_data)
    context.user_data.get('transaction', {}).pop(FROM_STATION_ID, None)
    context.user_data.get('transaction', {}).pop(FROM_STATION_NAME, None)

    reply_markup = InlineKeyboardMarkup(
        generate_station_keyboard(
            context.user_data.get(STATIONS_DATA, []),
            context.user_data.get('transaction', {}).get(FROM_STATE_NAME),
            'set_from_station:',
            True
        )
    )
    message = (
        f'{get_tracking_content(context.user_data.get('transaction', {}), context.user_data.get('volatile', {}))}'
    )

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    context.user_data['state'] = SET_FROM_STATION
    return SET_FROM_STATION


async def set_to_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data != 'set_to_station:' + BACK_DATA:
        match = re.search('set_from_station:(.*)', query.data)
        if match:
            context.user_data.get('transaction', {})[FROM_STATION_ID] = match.group(1)
            context.user_data.get('transaction', {})[FROM_STATION_NAME] = get_station_by_id(
                context.user_data.get(STATIONS_DATA, []), context.user_data.get('transaction', {}).get(FROM_STATION_ID)
            ).get('Description')
        else:
            return context.user_data.get('state')

    enable_cancel(context.user_data)
    context.user_data.get('transaction', {}).pop(TO_STATE_NAME, None)

    reply_markup = InlineKeyboardMarkup(
        build_state_keyboard(
            context.user_data.get(STATIONS_DATA, []),
            {},
            'set_to_state:',
            True
        )
    )
    message = (
        f'{get_tracking_content(context.user_data.get('transaction', {}), context.user_data.get('volatile', {}))}'
        '\n'
        'Where are you going to?'
    )

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    context.user_data['state'] = SET_TO_STATE
    return SET_TO_STATE


async def set_to_station(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data != 'set_date:' + BACK_DATA:
        match = re.search('set_to_state:(.*)', query.data)
        if match:
            context.user_data.get('transaction', {})[TO_STATE_NAME] = match.group(1)
        else:
            return context.user_data.get('state')

    enable_cancel(context.user_data)
    context.user_data.get('transaction', {}).pop(TO_STATION_ID, None)
    context.user_data.get('transaction', {}).pop(TO_STATION_NAME, None)

    reply_markup = InlineKeyboardMarkup(
        generate_station_keyboard(
            context.user_data.get(STATIONS_DATA, []),
            context.user_data.get('transaction', {}).get(TO_STATE_NAME),
            'set_to_station:',
            True
        )
    )
    message = (
        f'{get_tracking_content(context.user_data.get('transaction', {}), context.user_data.get('volatile', {}))}'
    )

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    context.user_data['state'] = SET_TO_STATION
    return SET_TO_STATION


async def set_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data != 'set_trip:' + BACK_DATA:
        match = re.search('set_to_station:(.*)', query.data)
        if match:
            context.user_data.get('transaction', {})[TO_STATION_ID] = match.group(1)
            context.user_data.get('transaction', {})[TO_STATION_NAME] = get_station_by_id(
                context.user_data.get(STATIONS_DATA, []), context.user_data.get('transaction', {})[TO_STATION_ID]
            ).get('Description')
        else:
            match = re.search(f'set_from_state:({UUID_PATTERN})', query.data)
            if match:
                shortcut_uuid = match.group(1)
                t = context.user_data.get('shortcuts', {}).get(uuid.UUID(shortcut_uuid))
                context.user_data.get('transaction', {})[FROM_STATE_NAME] = t.get(FROM_STATE_NAME)
                context.user_data.get('transaction', {})[FROM_STATION_ID] = t.get(FROM_STATION_ID)
                context.user_data.get('transaction', {})[FROM_STATION_NAME] = t.get(FROM_STATION_NAME)
                context.user_data.get('transaction', {})[TO_STATE_NAME] = t.get(TO_STATE_NAME)
                context.user_data.get('transaction', {})[TO_STATION_ID] = t.get(TO_STATION_ID)
                context.user_data.get('transaction', {})[TO_STATION_NAME] = t.get(TO_STATION_NAME)
            else:
                logger.info('test')
                return context.user_data.get('state')

    enable_cancel(context.user_data)
    context.user_data.get('transaction', {}).pop(DATE, None)

    reply_markup = InlineKeyboardMarkup(generate_friday_keyboard('set_date:', True))
    message = (
        f'{get_tracking_content(context.user_data.get('transaction', {}), context.user_data.get('volatile', {}))}'
        '\n'
        'What date? (YYYY-MM-DD, e.g. 2025-01-01)'
    )

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    context.user_data['state'] = SET_DATE
    return SET_DATE


async def set_trip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        # From inline keyboard
        query = update.callback_query
        await query.answer()
        if query.data != 'set_track:' + BACK_DATA:
            match = re.search('set_date:(.*)', query.data)
            if match:
                context.user_data.get('transaction', {})[DATE] = match.group(1)
            else:
                return context.user_data.get('state')
    else:
        # From normal keyboard
        context.user_data.get('transaction', {})[DATE] = update.message.text

    year, month, day = context.user_data.get('transaction', {}).get(DATE).split('-')

    enable_cancel(context.user_data)
    context.user_data.get('transaction', {}).pop(DEPARTURE_TIME, None)
    context.user_data.get('transaction', {}).pop(ARRIVAL_TIME, None)
    context.user_data.get('volatile', {}).pop(PARTIAL_CONTENT, None)

    session = requests.Session()
    if COOKIE in context.user_data:
        session.cookies.update(context.user_data.get(COOKIE))

    res = get_trips(
        session,
        datetime(int(year), int(month), int(day)),
        get_station_by_id(
            context.user_data.get(STATIONS_DATA, []),
            context.user_data.get('transaction', {}).get(FROM_STATION_ID)
        ),
        get_station_by_id(
            context.user_data.get(STATIONS_DATA, []),
            context.user_data.get('transaction', {}).get(TO_STATION_ID)
        ),
        context.user_data.get(TOKEN)
    )
    if not res.get('status'):
        context.user_data[TO_STRIKETHROUGH] = True
        context.user_data[TO_HIDE_KEYBOARD] = False
        await display_error_inline(context, res, InlineKeyboardMarkup(generate_friday_keyboard('set_date:', True)))
        context.user_data.get('transaction', {}).pop(DATE, None)
        context.user_data['state'] = SET_DATE
        return SET_DATE

    context.user_data.get('volatile', {})[SEARCH_DATA] = res.get(SEARCH_DATA)
    context.user_data.get('volatile', {})[TRIPS_DATA] = json.loads(json.dumps(res.get(TRIPS_DATA)))
    # logger.info(context.user_data.get('volatile', {})[SEARCH_DATA])
    # logger.info(context.user_data.get('volatile', {})[TRIPS_DATA])

    reply_markup = InlineKeyboardMarkup(
        generate_trips_keyboard(
            context.user_data.get('volatile', {}).get(TRIPS_DATA),
            'set_trip:',
            True
        )
    )
    message = (
        f'{get_tracking_content(context.user_data.get('transaction', {}), context.user_data.get('volatile', {}))}'
        '\n'
        'What time?'
    )

    last_message = context.user_data.get(LAST_MESSAGE)
    context.user_data[LAST_MESSAGE] = await context.bot.edit_message_text(
        chat_id=last_message.chat_id,
        message_id=last_message.message_id,
        text=message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    context.user_data['state'] = SET_TRIP
    return SET_TRIP


async def set_track(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    # index = int(query.data)
    # trip = context.user_data.get(TRIPS_DATA)[index]
    # context.user_data[TRIP_DATA] = trip.get(TRIP_DATA)
    # context.user_data[DEPARTURE_TIME] = trip.get(DEPARTURE_TIME)
    # context.user_data[ARRIVAL_TIME] = trip.get(ARRIVAL_TIME)
    match = re.search('set_trip:(.*)', query.data)
    if match:
        index = int(match.group(1))
        trip = context.user_data.get('volatile', {}).get(TRIPS_DATA)[index]
        context.user_data.get('volatile', {})[TRIP_DATA] = trip.get(TRIP_DATA)
        context.user_data.get('transaction', {})[DEPARTURE_TIME] = trip.get(DEPARTURE_TIME)
        context.user_data.get('transaction', {})[ARRIVAL_TIME] = trip.get(ARRIVAL_TIME)
    else:
        return context.user_data.get('state')

    enable_cancel(context.user_data)

    session = requests.Session()
    if COOKIE in context.user_data:
        session.cookies.update(context.user_data.get(COOKIE))

    res = await get_seats_contents(
        context.user_data.get('volatile', {}).get(SEARCH_DATA),
        context.user_data.get('volatile', {}).get(TRIP_DATA),
        session,
        context.user_data.get(TOKEN)
    )
    if not res.get('status'):
        context.user_data[TO_STRIKETHROUGH] = True
        context.user_data[TO_HIDE_KEYBOARD] = False
        await display_error_inline(
            context,
            res,
            InlineKeyboardMarkup(
                generate_trips_keyboard(
                    context.user_data.get('volatile', {}).get(TRIPS_DATA),
                    'set_trip:',
                    True
                )
            )
        )
        context.user_data.get('transaction', {}).pop(DEPARTURE_TIME, None)
        context.user_data.get('transaction', {}).pop(ARRIVAL_TIME, None)
        context.user_data.get('volatile', {}).pop(PARTIAL_CONTENT, None)
        context.user_data['state'] = SET_TRIP
        return SET_TRIP

    context.user_data.get('volatile', {})[LAYOUT_DATA] = res.get(LAYOUT_DATA)
    context.user_data.get('volatile', {})['overall_prices'] = res.get('overall_prices')
    context.user_data.get('volatile', {})[PARTIAL_CONTENT] = res.get(PARTIAL_CONTENT)

    reply_markup = InlineKeyboardMarkup(
        generate_tracking_keyboard(context.user_data.get('volatile', {})['overall_prices'], 'set_track:', True))
    message = (
        f'{get_tracking_content(context.user_data.get('transaction', {}), context.user_data.get('volatile', {}))}'
        '\n'
        '<b>Confirm to track this train?</b>\n'
        '\n'
        'You will be notified when:\n'
        '😱 tickets are selling out, or\n'
        '😁 a seat suddenly appears'
    )

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    context.user_data['state'] = SET_TRACK
    return SET_TRACK


async def set_reserve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    is_refresh = False
    is_cancel = False
    if re.compile(f'^Refresh/{UUID_PATTERN}$').match(query.data):
        tracking_uuid = re.search(UUID_PATTERN, query.data).group(0)
        is_refresh = True
    elif re.compile(f'^Cancel Reservation/{UUID_PATTERN}$').match(query.data):
        tracking_uuid = re.search(UUID_PATTERN, query.data).group(0)
        is_cancel = True
    else:
        match = re.search('set_track:(.*)', query.data)
        if match:
            context.user_data.get('transaction', {})[PRICE] = int(match.group(1))
        else:
            return context.user_data.get('state')
        # context.user_data.get('transaction', {})[PRICE] = int(query.data)
        if TRACKING_LIST not in context.user_data:
            context.user_data[TRACKING_LIST] = []
        tracking_uuid = uuid.uuid4()
        context.user_data[TRACKING_LIST].append(
            {
                'uuid': tracking_uuid,
                FROM_STATE_NAME: context.user_data.get('transaction', {}).get(FROM_STATE_NAME),
                FROM_STATION_ID: context.user_data.get('transaction', {}).get(FROM_STATION_ID),
                FROM_STATION_NAME: context.user_data.get('transaction', {}).get(FROM_STATION_NAME),
                TO_STATE_NAME: context.user_data.get('transaction', {}).get(TO_STATE_NAME),
                TO_STATION_ID: context.user_data.get('transaction', {}).get(TO_STATION_ID),
                TO_STATION_NAME: context.user_data.get('transaction', {}).get(TO_STATION_NAME),
                DATE: context.user_data.get('transaction', {}).get(DATE),
                DEPARTURE_TIME: context.user_data.get('transaction', {}).get(DEPARTURE_TIME),
                ARRIVAL_TIME: context.user_data.get('transaction', {}).get(ARRIVAL_TIME),
                PRICE: context.user_data.get('transaction', {}).get(PRICE),
                RESERVED_SEAT: None,
                'seats_left_by_prices': [],
                'last_reminded': datetime.now()
            }
        )

    enable_hide_keyboard_only(context.user_data)

    session = requests.Session()
    if COOKIE in context.user_data:
        session.cookies.update(context.user_data.get(COOKIE))

    if is_cancel:
        res = cancel_reservation(
            session,
            context.user_data.get('volatile', {}).get(SEARCH_DATA),
            context.user_data.get('volatile', {}).get('booking_data'),
            context.user_data.get(TOKEN)
        )
        if not res.get('status'):
            context.user_data[TO_STRIKETHROUGH] = False
            context.user_data[TO_HIDE_KEYBOARD] = True
            await display_error_inline(
                context,
                res,
                InlineKeyboardMarkup(generate_reserved_keyboard(tracking_uuid))
            )
            context.user_data['state'] = VIEW_TRACK
            return VIEW_TRACK
        for index, t in enumerate(context.user_data[TRACKING_LIST]):
            if t.get('uuid') == uuid.UUID(tracking_uuid):
                t[RESERVED_SEAT] = None
                context.user_data[TRACKING_LIST][index] = t
                break
        title = Title.CANCEL_RESERVATION.value
    # elif is_refresh:
    #     title = Title.REFRESH_TRACKING.value
    else:
        title = Title.NEW_TRACKING.value

    # res = await get_seats_contents(context.user_data, session)
    res = await get_seats_contents(
        context.user_data.get('volatile', {}).get(SEARCH_DATA),
        context.user_data.get('volatile', {}).get(TRIP_DATA),
        session,
        context.user_data.get(TOKEN)
    )
    if not res.get('status'):
        context.user_data[TO_STRIKETHROUGH] = True
        context.user_data[TO_HIDE_KEYBOARD] = False
        context.user_data.get('volatile', {}).pop(PARTIAL_CONTENT, None)
        context.user_data[TRACKING_LIST].pop()
        await display_error_inline(
            context,
            res,
            InlineKeyboardMarkup(
                # generate_tracking_keyboard(context.user_data.get('volatile', {})['overall_prices'], True)
                generate_tracking_keyboard(context.user_data.get('volatile', {})['overall_prices'], 'set_track:', True)
            )
        )
        context.user_data['state'] = SET_TRACK
        return SET_TRACK

    context.user_data.get('volatile', {})[PARTIAL_CONTENT] = res.get(PARTIAL_CONTENT)
    for index, t in enumerate(context.user_data.get(TRACKING_LIST, [])):
        if t.get('uuid') == tracking_uuid:
            t = {
                **t,
                'seats_left_by_prices': res.get('seats_left_by_prices')
            }
            context.user_data[TRACKING_LIST][index] = t
            break
    # logger.info(context.user_data.get(TRACKING_LIST, []))

    if not is_refresh:
        chat_id = update.effective_message.chat_id
        try:
            year, month, day = context.user_data.get('transaction', {}).get(DATE).split('-')
            hour, minute = context.user_data.get('transaction', {}).get(DEPARTURE_TIME).split(':')
            date_time = datetime(int(year), int(month), int(day), int(hour), int(minute)).timestamp()

            # scheduler.add_job(my_job, 'interval', seconds=10)

            scheduler.add_job(
                # alarm,
                sync_alarm_wrapper,
                'interval',
                seconds=15,
                start_date=datetime.now() + timedelta(seconds=15),
                end_date=datetime(int(year), int(month), int(day), int(hour), int(minute)),
                args=[],
                kwargs={
                    'context': context,
                    'data': {
                        COOKIE: context.user_data.get(COOKIE),
                        TOKEN: context.user_data.get(TOKEN),
                        'data': next(
                            t for t in context.user_data.get(TRACKING_LIST, []) if t.get('uuid') == tracking_uuid)
                    },
                    'chat_id': chat_id
                },
                id=str(tracking_uuid)
            )

            # scheduler.add_job(
            #     alarm,
            #     'interval',
            #     seconds=15,
            #     start_date=datetime.now() + timedelta(seconds=15),
            #     end_date=datetime(int(year), int(month), int(day), int(hour), int(minute)),
            #     args=[],
            #     kwargs={
            #         'context': context,
            #         'data': {
            #             COOKIE: context.user_data.get(COOKIE),
            #             TOKEN: context.user_data.get(TOKEN),
            #             'data': next(
            #                 t for t in context.user_data.get(TRACKING_LIST, []) if t.get('uuid') == tracking_uuid)
            #         },
            #         'chat_id': chat_id
            #     },
            #     id=str(tracking_uuid)
            # )

            # context.job_queue.run_repeating(
            #     alarm,
            #     interval=15,
            #     first=15,
            #     last=date_time,
            #     data={
            #         COOKIE: context.user_data.get(COOKIE),
            #         TOKEN: context.user_data.get(TOKEN),
            #         'data': next(t for t in context.user_data.get(TRACKING_LIST, []) if t.get('uuid') == tracking_uuid)
            #     },
            #     name=str(tracking_uuid),
            #     chat_id=chat_id
            # )
        except Exception as e:
            logger.error(e)
            context.user_data[TO_STRIKETHROUGH] = False
            context.user_data[TO_HIDE_KEYBOARD] = True
            await display_error_inline(
                context,
                {'error': 'Job scheduling error'},
                InlineKeyboardMarkup(
                    # generate_tracking_keyboard(context.user_data.get('volatile', {})['overall_prices'], True)
                    generate_tracking_keyboard(context.user_data.get('volatile', {})['overall_prices'], 'set_track:',
                                               True)
                )
            )
            context.user_data['state'] = SET_TRACK
            return SET_TRACK

    logger.info('Number of jobs: ' + str(len(context.job_queue.jobs())))

    reply_markup = InlineKeyboardMarkup(generate_reserve_keyboard(tracking_uuid))
    price_message = 'any price' \
        if context.user_data.get('transaction', {}).get(PRICE) == -1 \
        else f'RM {context.user_data.get('transaction', {}).get(PRICE)}'
    message = (
        f'{get_tracking_content(context.user_data.get('transaction', {}), context.user_data.get('volatile', {}), title)}'
        '\n'
        f'<i>Refreshed at: {utc_to_malaysia_time(datetime.now()).strftime('%H:%M:%S')}</i>\n'
        '\n'
        f'<b>Reserve a random seat of {price_message}?</b>'
    )

    if message != context.user_data[LAST_MESSAGE].text_html:
        context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    context.user_data['state'] = VIEW_TRACK
    return VIEW_TRACK


async def show_reserved(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    is_refresh = False
    # is_cancel = False
    if re.compile(f'^Refresh Reserved/{UUID_PATTERN}$').match(query.data):
        tracking_uuid = re.search(UUID_PATTERN, query.data).group(0)
        is_refresh = True
    elif re.compile(f'^Reserve/{UUID_PATTERN}$').match(query.data):
        tracking_uuid = re.search(UUID_PATTERN, query.data).group(0)

        # context.user_data[TRACKING_LIST] = [
        #     t for t in context.user_data.get(TRACKING_LIST, []) if t.get('uuid') != uuid.UUID(tracking_uuid)
        # ]
        job_removed = remove_job_if_exists(tracking_uuid, context)
        logger.info(job_removed)
    else:
        return context.user_data.get('state')

    # query = update.callback_query
    # await query.answer()
    # tracking_uuid = query.data
    # if re.compile(f'^Reserve/{UUID_PATTERN}$').match(query.data):
    #     tracking_uuid = re.search(UUID_PATTERN, query.data).group(0)

    enable_hide_keyboard_only(context.user_data)

    session = requests.Session()
    if COOKIE in context.user_data:
        session.cookies.update(context.user_data.get(COOKIE))

    # res = await get_seats_contents(context.user_data, session)
    res = await get_seats_contents(
        context.user_data.get('volatile', {}).get(SEARCH_DATA),
        context.user_data.get('volatile', {}).get(TRIP_DATA),
        session,
        context.user_data.get(TOKEN)
    )
    if not res.get('status'):
        context.user_data[TO_STRIKETHROUGH] = False
        context.user_data[TO_HIDE_KEYBOARD] = True
        context.user_data.get('volatile', {}).pop(PARTIAL_CONTENT, None)
        await display_error_inline(
            context,
            res,
            InlineKeyboardMarkup(generate_reserve_keyboard(tracking_uuid))
        )
        context.user_data['state'] = VIEW_TRACK
        return VIEW_TRACK

    context.user_data.get('volatile', {})[LAYOUT_DATA] = res.get(LAYOUT_DATA)
    context.user_data.get('volatile', {})[PARTIAL_CONTENT] = res.get(PARTIAL_CONTENT)

    if not is_refresh:
        res = reserve_by_price(
            session,
            res.get('seats_data'),
            context.user_data.get('transaction', {}).get(PRICE),
            context.user_data.get('volatile', {}).get(SEARCH_DATA),
            context.user_data.get('volatile', {}).get(TRIP_DATA),
            context.user_data.get('volatile', {}).get(LAYOUT_DATA),
            context.user_data.get(TOKEN)
        )
        if not res.get('status'):
            context.user_data[TO_STRIKETHROUGH] = False
            context.user_data[TO_HIDE_KEYBOARD] = True
            await display_error_inline(
                context,
                res,
                InlineKeyboardMarkup(generate_reserve_keyboard(tracking_uuid))
            )
            context.user_data['state'] = VIEW_TRACK
            return VIEW_TRACK

        context.user_data.get('volatile', {})['booking_data'] = res.get('booking_data')
        coach = res.get('CoachLabel')
        seat = res.get('SeatNo')
        price = res.get('Price')
        for index, t in enumerate(context.user_data.get(TRACKING_LIST, [])):
            if t.get('uuid') == uuid.UUID(tracking_uuid):
                t = {
                    **t,
                    RESERVED_SEAT: {
                        'CoachLabel': coach,
                        'SeatNo': seat,
                        'Price': price
                    }
                }
                context.user_data[TRACKING_LIST][index] = t
                break
        # logger.info(context.user_data.get(TRACKING_LIST, []))

    t = next(tr for tr in context.user_data.get(TRACKING_LIST, []) if tr.get('uuid') == uuid.UUID(tracking_uuid))

    reply_markup = InlineKeyboardMarkup(generate_reserved_keyboard(tracking_uuid))
    message = (
        f'{get_tracking_content(context.user_data.get('transaction', {}), context.user_data.get('volatile', {}), Title.NEW_RESERVATION.value)}'
        '\n'
        f'<i>Refreshed at: {utc_to_malaysia_time(datetime.now()).strftime('%H:%M:%S')}</i>\n'
        '\n'
        'Seat reserved successfully!\n'
        '\n'
        f'Coach: <b>{t.get(RESERVED_SEAT, {}).get('CoachLabel')}</b>\n'
        f'Seat: <b>{t.get(RESERVED_SEAT, {}).get('SeatNo')}</b>\n'
        f'Price: <b>RM {t.get(RESERVED_SEAT, {}).get('Price')}</b>'
    )

    if message != context.user_data[LAST_MESSAGE].text_html:
        context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    context.user_data['state'] = RESERVED
    return RESERVED


async def cancel_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    tracking_uuid = re.search(UUID_PATTERN, query.data).group(0)
    context.user_data[TRACKING_LIST] = [
        t for t in context.user_data.get(TRACKING_LIST, []) if t.get('uuid') != uuid.UUID(tracking_uuid)
    ]
    job_removed = remove_job_if_exists(tracking_uuid, context)
    logger.info(job_removed)

    enable_cancel(context.user_data)

    await cancel_last_message(context)

    disable_any_cancel(context.user_data)

    context.user_data['state'] = START
    return START


async def view_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await cancel_last_message(context)

    enable_hide_keyboard_only(context.user_data)

    if TRACKING_LIST not in context.user_data or len(context.user_data.get(TRACKING_LIST)) == 0:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )
        context.user_data[LAST_MESSAGE] = await update.message.reply_text(
            'No tracking found',
            reply_markup=None,
            parse_mode='HTML'
        )
        context.user_data['state'] = START
        return START

    session = requests.Session()
    if COOKIE in context.user_data:
        session.cookies.update(context.user_data.get(COOKIE))

    res = get_stations(session)
    if not res.get('status'):
        await reply_error(update, context, res)
        context.user_data['state'] = START
        return START

    # context.user_data[STATIONS_DATA] = res.get(STATIONS_DATA)
    stations_data = res.get(STATIONS_DATA)

    for index, t in enumerate(context.user_data.get(TRACKING_LIST)):
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )
        tracking_uuid = t.get('uuid')
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

        year, month, day = date.split('-')

        res = get_trips(
            session,
            datetime(int(year), int(month), int(day)),
            get_station_by_id(stations_data, from_station_id),
            get_station_by_id(stations_data, to_station_id),
            context.user_data.get(TOKEN)
        )
        if not res.get('status'):
            await reply_error(update, context, res)
            context.user_data['state'] = START
            return START
        # logger.info('trips_res:', trips_res)

        search_data = res.get('search_data')
        trips_data = json.loads(json.dumps(res.get('trips_data')))
        trip = next(tr for tr in trips_data if tr.get('departure_time') == departure_time)
        trip_data = trip.get(TRIP_DATA)

        # res = await get_seats_contents({
        #     SEARCH_DATA: search_data,
        #     TRIP_DATA: trip_data,
        #     TOKEN: context.user_data.get(TOKEN)
        # }, session)
        res = await get_seats_contents(
            search_data,
            trip_data,
            session,
            context.user_data.get(TOKEN)
        )
        if not res.get('status'):
            await reply_error(update, context, res)
            context.user_data['state'] = START
            return START

        partial_content = res.get(PARTIAL_CONTENT)

        if reserved_seat is None:
            reply_markup = InlineKeyboardMarkup(generate_reserve_keyboard(tracking_uuid))
            price_message = 'any price' if price == -1 else f'RM {price}'
            context.user_data[LAST_MESSAGE] = await update.message.reply_text(
                (
                    f'{get_tracking_content(t, {PARTIAL_CONTENT: partial_content}, Title.VIEW.value + str(index + 1))}'
                    '\n'
                    f'<i>Refreshed at: {utc_to_malaysia_time(datetime.now()).strftime('%H:%M:%S')}</i>\n'
                    '\n'
                    f'<b>Reserve a random seat of {price_message}?</b>'
                ),
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            reply_markup = InlineKeyboardMarkup(generate_reserved_keyboard(tracking_uuid))
            context.user_data[LAST_MESSAGE] = await update.message.reply_text(
                (
                    f'{get_tracking_content(t, {PARTIAL_CONTENT: partial_content}, Title.VIEW.value + str(index + 1))}'
                    '\n'
                    'Seat reserved successfully!\n'
                    '\n'
                    f'Coach: <b>{reserved_seat.get('CoachLabel')}</b>\n'
                    f'Seat: <b>{reserved_seat.get('SeatNo')}</b>\n'
                    f'Price: <b>RM {reserved_seat.get('Price')}</b>'
                ),
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

    context.user_data['state'] = VIEW_TRACK
    return VIEW_TRACK


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
    tracking_uuid = t.get('uuid')
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
    initial_seats_left_by_prices = t.get('seats_left_by_prices')
    last_reminded = t.get('last_reminded')

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
    new_seats_left_by_prices = res.get('seats_left_by_prices')

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
        t['last_reminded'] = datetime.now()
        t['intervals_index'] = t.get('intervals_index', 0) + 1
        if reserved_seat is None:
            price_message = 'any price' if price == -1 else f'RM {price}'
            await context.bot.send_message(
                # job.chat_id,
                chat_id,
                text=(
                    f'{get_tracking_content(t, {PARTIAL_CONTENT: partial_content}, reason)}'
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
                    f'{get_tracking_content({
                        **t,
                        PARTIAL_CONTENT: partial_content
                    }, 'Alarm')}'
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


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await cancel_last_message(context)

    disable_any_cancel(context.user_data)

    session = requests.Session()
    if COOKIE in context.user_data:
        session.cookies.update(context.user_data.get(COOKIE))

        res = logout(session)

        message = 'Logout executed\n\nYou can /login again' if res.get('status') else res.get('error')

        context.user_data[LAST_MESSAGE] = await update.message.reply_text(message, reply_markup=ReplyKeyboardRemove())

    context.user_data.clear()
    for job in context.job_queue.jobs():
        job.schedule_removal()

    message = 'Cleared all user data'

    context.user_data[LAST_MESSAGE] = await update.message.reply_text(message, reply_markup=ReplyKeyboardRemove())

    context.user_data['state'] = START
    return START


async def print_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    # await cancel_last_message(context)

    disable_any_cancel(context.user_data)

    message = query.data

    context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(message, reply_markup=None)

    context.user_data['state'] = START
    return START


def enable_cancel(data):
    data[TO_STRIKETHROUGH] = True
    data[TO_HIDE_KEYBOARD] = True


def enable_hide_keyboard_only(data):
    data[TO_STRIKETHROUGH] = False
    data[TO_HIDE_KEYBOARD] = True


def disable_any_cancel(data):
    data[TO_STRIKETHROUGH] = False
    data[TO_HIDE_KEYBOARD] = False


def malaysia_time_to_utc(user_time):
    """Convert naive Malaysia time to UTC"""
    # First localize to Malaysia time, then convert to UTC
    localized = MALAYSIA_TZ.localize(user_time)
    return localized.astimezone(pytz.utc)


def utc_to_malaysia_time(utc_time):
    """Convert UTC time to Malaysia time"""
    return utc_time.astimezone(MALAYSIA_TZ)


# Create the Application and pass it your bot's token.
persistence = PicklePersistence(filepath='ktmb_conversation_data')
application = Application.builder().token(BOT_TOKEN).persistence(persistence).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        START: [
            # CallbackQueryHandler(
            #     show_reserved,
            #     pattern=f'^Reserve/{UUID_PATTERN}$'
            # ),
            # CallbackQueryHandler(
            #     set_reserve,
            #     pattern=f'^Refresh/{UUID_PATTERN}$'
            # ),
            # CallbackQueryHandler(
            #     cancel_tracking,
            #     pattern=f'^Cancel Tracking/{UUID_PATTERN}$'
            # ),
            # CallbackQueryHandler(
            #     set_reserve,
            #     pattern=f'^Cancel Reservation/{UUID_PATTERN}$'
            # ),
        ],
        ADD_PROFILE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, add_profile_password)
        ],
        ADD_PROFILE_PASSWORD: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, added_profile_password)
        ],
        MANAGE_PROFILE: [
            CallbackQueryHandler(selected_profile, pattern='^manage_profile:')
        ],
        SELECTED_PROFILE: [
            CallbackQueryHandler(change_profile_password, pattern='^Change Password/'),
            CallbackQueryHandler(deleted_profile, pattern='^Delete/')
        ],
        CHANGE_PROFILE_PASSWORD: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, added_profile_password)
        ],
        ADD_FROM_STATE: [
            CallbackQueryHandler(add_from_station, pattern='^add_from_state:')
        ],
        ADD_FROM_STATION: [
            CallbackQueryHandler(add_from_state, pattern='add_from_station:Back'),
            CallbackQueryHandler(add_to_state, pattern='^add_from_station:')
        ],
        ADD_TO_STATE: [
            CallbackQueryHandler(add_from_station, pattern='add_to_state:Back'),
            CallbackQueryHandler(add_to_station, pattern='^add_to_state:')
        ],
        ADD_TO_STATION: [
            CallbackQueryHandler(add_to_state, pattern='add_to_station:Back'),
            CallbackQueryHandler(added_shortcut, pattern='^add_to_station:')
        ],
        MANAGE_SHORTCUT: [
            CallbackQueryHandler(selected_shortcut, pattern='^manage_shortcut:')
        ],
        SELECTED_SHORTCUT: [
            CallbackQueryHandler(deleted_shortcut, pattern='^Delete Shortcut/')
        ],
        SET_EMAIL: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, set_password),
            CallbackQueryHandler(login_ktmb, pattern='^set_email:')
        ],
        SET_PASSWORD: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, login_ktmb)
        ],
        SET_FROM_STATE: [
            CallbackQueryHandler(set_date, pattern=f'^set_from_state:{UUID_PATTERN}'),
            CallbackQueryHandler(set_from_station, pattern='^set_from_state:')
        ],
        SET_FROM_STATION: [
            CallbackQueryHandler(set_from_state, pattern='set_from_station:Back'),
            CallbackQueryHandler(set_to_state, pattern='^set_from_station:')
        ],
        SET_TO_STATE: [
            CallbackQueryHandler(set_from_station, pattern='set_to_state:Back'),
            CallbackQueryHandler(set_to_station, pattern='^set_to_state:')
        ],
        SET_TO_STATION: {
            CallbackQueryHandler(set_to_state, pattern='set_to_station:Back'),
            CallbackQueryHandler(set_date, pattern='^set_to_station:')
        },
        SET_DATE: [
            CallbackQueryHandler(set_to_station, pattern='set_date:Back'),
            CallbackQueryHandler(set_trip, pattern='^set_date:'),
            MessageHandler(filters.Regex('^\\d{4}-\\d{2}-\\d{2}$'), set_trip)
        ],
        SET_TRIP: [
            CallbackQueryHandler(set_date, pattern='set_trip:Back'),
            CallbackQueryHandler(set_track, pattern='^set_trip:')
        ],
        SET_TRACK: [
            CallbackQueryHandler(set_trip, pattern='set_track:Back'),
            CallbackQueryHandler(set_reserve, pattern='^set_track:-?\\d+$')
        ],
        VIEW_TRACK: [
            CallbackQueryHandler(
                show_reserved,
                pattern=f'^Reserve/{UUID_PATTERN}$'
            ),
            CallbackQueryHandler(
                set_reserve,
                pattern=f'^Refresh/{UUID_PATTERN}$'
            ),
            CallbackQueryHandler(
                cancel_tracking,
                pattern=f'^Cancel Tracking/{UUID_PATTERN}$'
            )
        ],
        RESERVED: [
            CallbackQueryHandler(
                show_reserved,
                pattern=f'^Refresh Reserved/{UUID_PATTERN}$'
            ),
            CallbackQueryHandler(
                set_reserve,
                pattern=f'^Cancel Reservation/{UUID_PATTERN}$'
            )
        ]
    },
    fallbacks=[
        CommandHandler('start', start),
        CommandHandler('add', add_profile),
        CommandHandler('manage', manage_profile),
        CommandHandler('login', set_email),
        CommandHandler('logout', logout_ktmb),
        CommandHandler('add_shortcut', add_from_state),
        CommandHandler('manage_shortcut', manage_shortcut),
        CommandHandler('clear', clear),
        MessageHandler(filters.Text([NEW]), set_from_state),
        MessageHandler(filters.Text([VIEW]), view_tracking),
        CallbackQueryHandler(print_unknown)
    ],
    name='ktmb_conversation',
    persistent=True
)

# Add ConversationHandler to application that will be used for handling updates
application.add_handler(conv_handler)

# Run the bot until the user presses Ctrl-C
# Opens a long-running thread, not supported in Hugging Face Spaces, use webhooks instead
if ENV == 'DEBUG':
    application.run_polling(allowed_updates=Update.ALL_TYPES)
