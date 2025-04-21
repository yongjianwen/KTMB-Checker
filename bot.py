import json
import os
import re
import uuid
from datetime import datetime

import requests
from telegram import InlineKeyboardMarkup, Update, ReplyKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler, PicklePersistence, MessageHandler, filters,
)

from bot_helper import get_seats_contents, cancel_last_message, reply_error, clear_session_data, clear_temp_data, \
    display_error_inline
from ktmb import get_station_by_id, login, get_trips, logout, get_stations, reserve_by_price, cancel_reservation
from utils import BACK_DATA, COOKIE, TOKEN, LAST_MESSAGE, TO_STRIKETHROUGH, STATIONS_DATA, FROM_STATE_NAME, \
    TO_STATE_NAME, FROM_STATION_ID, TO_STATION_ID, FROM_STATION_NAME, TO_STATION_NAME, DATE, PARTIAL_CONTENT, \
    SEARCH_DATA, TRIPS_DATA, TRIP_DATA, DEPARTURE_TIME, ARRIVAL_TIME, LAYOUT_DATA, PRICE, TRACKING_LIST, RESERVED_SEAT, \
    Title, UUID_PATTERN, TO_HIDE_KEYBOARD
from utils import build_state_keyboard, generate_station_keyboard, generate_friday_keyboard, generate_trips_keyboard, \
    generate_tracking_keyboard, generate_reserve_keyboard, generate_reserved_keyboard, get_tracking_content

BOT_TOKEN = os.getenv('BOT_TOKEN')
# Stages
START, SET_FROM_STATE, SET_FROM_STATION, SET_TO_STATE, SET_TO_STATION, SET_DATE, SET_TRIP, SET_TRACK = range(8)
# Bottom keyboard
NEW, VIEW, LOGIN, LOGOUT = 'Track New Train 🚈', '👀 View Tracking', 'Login (For Debug)', 'Logout (For Debug)'

bottom_keyboard = [
    [NEW, VIEW],
    [LOGIN, LOGOUT],
    ['Reset']
]
bottom_reply_markup = ReplyKeyboardMarkup(bottom_keyboard, one_time_keyboard=False, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await cancel_last_message(context)

    context.user_data[TO_STRIKETHROUGH] = False
    context.user_data[TO_HIDE_KEYBOARD] = False

    context.user_data[LAST_MESSAGE] = await update.message.reply_text(
        text=f'Hello {update.message.from_user.first_name} 👋 I am KTMB Bot 🤖\n'
             '\n'
             'You can use me to track train 🚈 seat availability',
        reply_markup=bottom_reply_markup
    )

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
        # From inline keyboard
        await query.answer()

    clear_temp_data(context)
    context.user_data[TO_STRIKETHROUGH] = True
    context.user_data[TO_HIDE_KEYBOARD] = False
    context.user_data.pop(FROM_STATE_NAME, None)

    reply_markup = InlineKeyboardMarkup(build_state_keyboard(context.user_data.get(STATIONS_DATA, [])))
    message = (
        f'{get_tracking_content(context)}'
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

    return SET_FROM_STATE


async def set_from_station(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data != BACK_DATA:
        context.user_data[FROM_STATE_NAME] = query.data

    context.user_data[TO_STRIKETHROUGH] = True
    context.user_data[TO_HIDE_KEYBOARD] = False
    context.user_data.pop(FROM_STATION_ID, None)
    context.user_data.pop(FROM_STATION_NAME, None)

    reply_markup = InlineKeyboardMarkup(
        generate_station_keyboard(
            context.user_data.get(STATIONS_DATA, []), context.user_data.get(FROM_STATE_NAME), True
        )
    )
    message = (
        f'{get_tracking_content(context)}'
    )

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    return SET_FROM_STATION


async def set_to_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data != BACK_DATA:
        context.user_data[FROM_STATION_ID] = query.data
        context.user_data[FROM_STATION_NAME] = get_station_by_id(
            context.user_data.get(STATIONS_DATA, []), query.data
        ).get('Description')

    context.user_data[TO_STRIKETHROUGH] = True
    context.user_data[TO_HIDE_KEYBOARD] = False
    context.user_data.pop(TO_STATE_NAME, None)

    reply_markup = InlineKeyboardMarkup(build_state_keyboard(context.user_data.get(STATIONS_DATA, []), True))
    message = (
        f'{get_tracking_content(context)}'
        '\n'
        'Where are you going to?'
    )

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    return SET_TO_STATE


async def set_to_station(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data != BACK_DATA:
        context.user_data[TO_STATE_NAME] = query.data

    context.user_data[TO_STRIKETHROUGH] = True
    context.user_data[TO_HIDE_KEYBOARD] = False
    context.user_data.pop(TO_STATION_ID, None)
    context.user_data.pop(TO_STATION_NAME, None)

    reply_markup = InlineKeyboardMarkup(
        generate_station_keyboard(
            context.user_data.get(STATIONS_DATA, []),
            context.user_data.get(TO_STATE_NAME),
            True
        )
    )
    message = (
        f'{get_tracking_content(context)}'
    )

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    return SET_TO_STATION


async def set_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data != BACK_DATA:
        context.user_data[TO_STATION_ID] = query.data
        context.user_data[TO_STATION_NAME] = get_station_by_id(
            context.user_data.get(STATIONS_DATA, []), query.data
        ).get('Description')

    context.user_data[TO_STRIKETHROUGH] = True
    context.user_data[TO_HIDE_KEYBOARD] = False
    context.user_data.pop(DATE, None)

    reply_markup = InlineKeyboardMarkup(generate_friday_keyboard(True))
    message = (
        f'{get_tracking_content(context)}'
        '\n'
        'What date? (YYYY-MM-DD, e.g. 2025-01-01)'
    )

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    return SET_DATE


async def set_trip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        # From inline keyboard
        query = update.callback_query
        await query.answer()
        if query.data != BACK_DATA:
            context.user_data[DATE] = query.data
    else:
        # From normal keyboard
        context.user_data[DATE] = update.message.text

    year, month, day = context.user_data.get(DATE).split('-')

    context.user_data[TO_STRIKETHROUGH] = True
    context.user_data[TO_HIDE_KEYBOARD] = False
    context.user_data.pop(DEPARTURE_TIME, None)
    context.user_data.pop(ARRIVAL_TIME, None)
    context.user_data.pop(PARTIAL_CONTENT, None)

    session = requests.Session()
    if COOKIE in context.user_data:
        session.cookies.update(context.user_data.get(COOKIE))

    res = get_trips(
        session,
        datetime(int(year), int(month), int(day)),
        get_station_by_id(context.user_data.get(STATIONS_DATA, []), context.user_data.get(FROM_STATION_ID)),
        get_station_by_id(context.user_data.get(STATIONS_DATA, []), context.user_data.get(TO_STATION_ID)),
        context.user_data.get(TOKEN)
    )
    if not res.get('status'):
        context.user_data[TO_STRIKETHROUGH] = True
        context.user_data[TO_HIDE_KEYBOARD] = False
        await display_error_inline(context, res, InlineKeyboardMarkup(generate_friday_keyboard(True)))
        context.user_data.pop(DATE, None)
        return SET_DATE

    context.user_data[SEARCH_DATA] = res.get(SEARCH_DATA)
    context.user_data[TRIPS_DATA] = json.loads(json.dumps(res.get(TRIPS_DATA)))
    # print(context.user_data[TRIPS_DATA])

    reply_markup = InlineKeyboardMarkup(generate_trips_keyboard(context.user_data.get(TRIPS_DATA), True))
    message = (
        f'{get_tracking_content(context)}'
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

    return SET_TRIP


async def set_track(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    index = int(query.data)
    trip = context.user_data.get(TRIPS_DATA)[index]
    context.user_data[TRIP_DATA] = trip.get(TRIP_DATA)
    context.user_data[DEPARTURE_TIME] = trip.get(DEPARTURE_TIME)
    context.user_data[ARRIVAL_TIME] = trip.get(ARRIVAL_TIME)

    context.user_data[TO_STRIKETHROUGH] = True
    context.user_data[TO_HIDE_KEYBOARD] = False

    session = requests.Session()
    if COOKIE in context.user_data:
        session.cookies.update(context.user_data.get(COOKIE))

    res = await get_seats_contents(context, session)
    if not res.get('status'):
        context.user_data[TO_STRIKETHROUGH] = True
        context.user_data[TO_HIDE_KEYBOARD] = False
        await display_error_inline(
            context,
            res,
            InlineKeyboardMarkup(generate_trips_keyboard(context.user_data.get(TRIPS_DATA), True))
        )
        context.user_data.pop(DEPARTURE_TIME, None)
        context.user_data.pop(ARRIVAL_TIME, None)
        context.user_data.pop(PARTIAL_CONTENT, None)
        return SET_TRIP

    context.user_data['overall_prices'] = res.get('overall_prices')

    reply_markup = InlineKeyboardMarkup(generate_tracking_keyboard(context.user_data['overall_prices'], True))
    message = (
        f'{get_tracking_content(context)}'
        '\n'
        '<b>Confirm to track this train?</b>\n'
        '\n'
        'You will be notified when:\n'
        '😱 tickets are selling rapidly, or\n'
        '😁 a seat suddenly appears'
    )

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

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
        context.user_data[PRICE] = int(query.data)
        if TRACKING_LIST not in context.user_data:
            context.user_data[TRACKING_LIST] = []
        tracking_uuid = uuid.uuid4()
        context.user_data[TRACKING_LIST].append(
            {
                'uuid': tracking_uuid,
                FROM_STATE_NAME: context.user_data.get(FROM_STATE_NAME),
                FROM_STATION_ID: context.user_data.get(FROM_STATION_ID),
                FROM_STATION_NAME: context.user_data.get(FROM_STATION_NAME),
                TO_STATE_NAME: context.user_data.get(TO_STATE_NAME),
                TO_STATION_ID: context.user_data.get(TO_STATION_ID),
                TO_STATION_NAME: context.user_data.get(TO_STATION_NAME),
                DATE: context.user_data.get(DATE),
                DEPARTURE_TIME: context.user_data.get(DEPARTURE_TIME),
                ARRIVAL_TIME: context.user_data.get(ARRIVAL_TIME),
                PRICE: context.user_data.get(PRICE),
                RESERVED_SEAT: None
            }
        )

    context.user_data[TO_STRIKETHROUGH] = False
    context.user_data[TO_HIDE_KEYBOARD] = True

    session = requests.Session()
    if COOKIE in context.user_data:
        session.cookies.update(context.user_data.get(COOKIE))

    if is_cancel:
        res = cancel_reservation(
            session,
            context.user_data.get(SEARCH_DATA),
            context.user_data.get('booking_data'),
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
            return START
        for index, t in enumerate(context.user_data[TRACKING_LIST]):
            if t.get('uuid') == uuid.UUID(tracking_uuid):
                t[RESERVED_SEAT] = None
                context.user_data[TRACKING_LIST][index] = t
                break
        title = Title.CANCEL_RESERVATION.value
    elif is_refresh:
        title = Title.REFRESH_TRACKING.value
    else:
        title = Title.NEW_TRACKING.value

    res = await get_seats_contents(context, session)
    if not res.get('status'):
        context.user_data[TO_STRIKETHROUGH] = True
        context.user_data[TO_HIDE_KEYBOARD] = False
        context.user_data.pop(PARTIAL_CONTENT, None)
        context.user_data[TRACKING_LIST].pop()
        await display_error_inline(
            context,
            res,
            InlineKeyboardMarkup(generate_tracking_keyboard(context.user_data['overall_prices'], True))
        )
        return SET_TRACK

    reply_markup = InlineKeyboardMarkup(generate_reserve_keyboard(tracking_uuid))
    price_message = 'any price' if context.user_data.get(PRICE) == -1 else f'RM {context.user_data.get(PRICE)}'
    message = (
        f'{get_tracking_content(context, title)}'
        '\n'
        f'<i>Refreshed at: {datetime.now().strftime('%H:%M:%S')}</i>\n'
        '\n'
        f'<b>Reserve a random seat of {price_message}?</b>'
    )

    if message != context.user_data[LAST_MESSAGE].text_html:
        context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    return START


async def show_reserved(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    tracking_uuid = query.data
    if re.compile(f'^Reserve/{UUID_PATTERN}$').match(query.data):
        tracking_uuid = re.search(UUID_PATTERN, query.data).group(0)

    context.user_data[TO_STRIKETHROUGH] = False
    context.user_data[TO_HIDE_KEYBOARD] = True

    session = requests.Session()
    if COOKIE in context.user_data:
        session.cookies.update(context.user_data.get(COOKIE))

    res = await get_seats_contents(context, session)
    if not res.get('status'):
        context.user_data[TO_STRIKETHROUGH] = False
        context.user_data[TO_HIDE_KEYBOARD] = True
        context.user_data.pop(PARTIAL_CONTENT, None)
        await display_error_inline(
            context,
            res,
            InlineKeyboardMarkup(generate_reserve_keyboard(tracking_uuid))
        )
        return START

    res = reserve_by_price(
        session,
        res.get('seats_data'),
        context.user_data.get(PRICE),
        context.user_data.get(SEARCH_DATA),
        context.user_data.get(TRIP_DATA),
        context.user_data.get(LAYOUT_DATA),
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
        return START

    context.user_data['booking_data'] = res.get('booking_data')
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
    print(context.user_data.get(TRACKING_LIST, []))

    reply_markup = InlineKeyboardMarkup(generate_reserved_keyboard(tracking_uuid))
    message = (
        f'{get_tracking_content(context, Title.NEW_RESERVATION.value)}'
        '\n'
        'Seat reserved successfully!\n'
        '\n'
        f'Coach: <b>{coach}</b>\n'
        f'Seat: <b>{seat}</b>\n'
        f'Price: <b>RM {price}</b>'
    )

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    return START


async def cancel_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    tracking_uuid = re.search(UUID_PATTERN, query.data).group(0)
    context.user_data[TRACKING_LIST] = [
        t for t in context.user_data.get(TRACKING_LIST) if t.get('uuid') != uuid.UUID(tracking_uuid)
    ]

    context.user_data[TO_STRIKETHROUGH] = True
    context.user_data[TO_HIDE_KEYBOARD] = False

    await cancel_last_message(context)

    context.user_data[TO_STRIKETHROUGH] = False
    context.user_data[TO_HIDE_KEYBOARD] = False

    return START


async def view_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await cancel_last_message(context)

    context.user_data[TO_STRIKETHROUGH] = False
    context.user_data[TO_HIDE_KEYBOARD] = True

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
        return START

    session = requests.Session()
    if COOKIE in context.user_data:
        session.cookies.update(context.user_data.get(COOKIE))

    res = get_stations(session)
    if not res.get('status'):
        await reply_error(update, context, res)
        return START

    context.user_data[STATIONS_DATA] = res.get(STATIONS_DATA)

    for index, t in enumerate(context.user_data.get(TRACKING_LIST)):
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )
        tracking_uuid = t.get('uuid')
        context.user_data[FROM_STATE_NAME] = t.get(FROM_STATE_NAME)
        context.user_data[FROM_STATION_ID] = t.get(FROM_STATION_ID)
        context.user_data[FROM_STATION_NAME] = t.get(FROM_STATION_NAME)
        context.user_data[TO_STATE_NAME] = t.get(TO_STATE_NAME)
        context.user_data[TO_STATION_ID] = t.get(TO_STATION_ID)
        context.user_data[TO_STATION_NAME] = t.get(TO_STATION_NAME)
        context.user_data[DATE] = t.get(DATE)
        context.user_data[DEPARTURE_TIME] = t.get(DEPARTURE_TIME)
        context.user_data[ARRIVAL_TIME] = t.get(ARRIVAL_TIME)
        context.user_data[PRICE] = t.get(PRICE)
        reserved_seat = t.get(RESERVED_SEAT)

        year, month, day = context.user_data.get(DATE).split('-')

        res = get_trips(
            session,
            datetime(int(year), int(month), int(day)),
            get_station_by_id(context.user_data.get(STATIONS_DATA, []), context.user_data.get(FROM_STATION_ID)),
            get_station_by_id(context.user_data.get(STATIONS_DATA, []), context.user_data.get(TO_STATION_ID)),
            context.user_data.get(TOKEN)
        )
        if not res.get('status'):
            await reply_error(update, context, res)
            return START
        # print('trips_res:', trips_res)

        context.user_data[SEARCH_DATA] = res.get('search_data')
        context.user_data[TRIPS_DATA] = json.loads(json.dumps(res.get('trips_data')))
        trip = next(t for t in context.user_data.get(TRIPS_DATA) if
                    t.get('departure_time') == context.user_data.get(DEPARTURE_TIME))
        context.user_data[TRIP_DATA] = trip.get(TRIP_DATA)

        # print('Search Data:', context.user_data.get(SEARCH_DATA))
        # print('Trip data:', context.user_data.get(TRIP_DATA))
        # print('Token:', context.user_data.get(TOKEN))
        res = await get_seats_contents(context, session)
        if not res.get('status'):
            await reply_error(update, context, res)
            return START

        if reserved_seat is None:
            reply_markup = InlineKeyboardMarkup(generate_reserve_keyboard(tracking_uuid))
            price_message = 'any price' if context.user_data.get(PRICE) == -1 else f'RM {context.user_data.get(PRICE)}'
            context.user_data[LAST_MESSAGE] = await update.message.reply_text(
                (
                    f'{get_tracking_content(context, Title.VIEW.value + str(index + 1))}'
                    '\n'
                    f'<i>Refreshed at: {datetime.now().strftime('%H:%M:%S')}</i>\n'
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
                    f'{get_tracking_content(context, Title.VIEW.value + str(index + 1))}'
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

    return START


async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    await context.bot.send_message(job.chat_id, text=f"Beep! {job.data} seconds are over!")


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def set_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_message.chat_id
    try:
        job_removed = remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_once(alarm, 10, chat_id=chat_id, name=str(chat_id), data=10)

        text = "Timer successfully set!"
        if job_removed:
            text += " Old one was removed."
        await update.effective_message.reply_text(text)

    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /set <seconds>")


async def unset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = "Timer successfully cancelled!" if job_removed else "You have no active timer."
    await update.message.reply_text(text)


async def logout_ktmb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await cancel_last_message(context)

    context.user_data[TO_STRIKETHROUGH] = False
    context.user_data[TO_HIDE_KEYBOARD] = False

    session = requests.Session()
    if COOKIE in context.user_data:
        session.cookies.update(context.user_data.get(COOKIE))

        clear_session_data(context)
        clear_temp_data(context)

        res = logout(session)

        message = 'Logout executed' if res.get('status') else res.get('error')

        context.user_data[LAST_MESSAGE] = await update.message.reply_text(message, reply_markup=None)

        return START

    clear_session_data(context)
    clear_temp_data(context)

    message = 'Already logged out'

    context.user_data[LAST_MESSAGE] = await update.message.reply_text(message, reply_markup=None)

    return START


async def login_ktmb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await cancel_last_message(context)

    context.user_data[TO_STRIKETHROUGH] = False
    context.user_data[TO_HIDE_KEYBOARD] = False

    session = requests.Session()
    if COOKIE in context.user_data:
        session.cookies.update(context.user_data.get(COOKIE))
        context.user_data[LAST_MESSAGE] = await update.message.reply_text(
            'Already logged in',
            reply_markup=None
        )
        return START

    res = login(session)
    context.user_data[COOKIE] = session.cookies
    context.user_data[TOKEN] = res.get('token')
    context.user_data[STATIONS_DATA] = res.get('stations_data')
    # print(context.user_data.get(STATIONS_DATA))

    message = 'Logged in successfully' if res.get('status') else res.get('error')

    context.user_data[LAST_MESSAGE] = await update.message.reply_text(message, reply_markup=None)

    return START


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await cancel_last_message(context)

    context.user_data.clear()
    # context.user_data[TO_STRIKETHROUGH] = False
    # context.user_data[TO_HIDE_KEYBOARD] = False

    context.user_data[LAST_MESSAGE] = await update.message.reply_text(
        text=f'Cleared all user data',
        reply_markup=bottom_reply_markup
    )

    return START


def main():
    # Create the Application and pass it your bot's token.
    persistence = PicklePersistence(filepath="ktmb_conversation_data")
    application = Application.builder().token(BOT_TOKEN).persistence(persistence).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START: [
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
                ),
                CallbackQueryHandler(
                    set_reserve,
                    pattern=f'^Cancel Reservation/{UUID_PATTERN}$'
                ),
                CommandHandler('set', set_timer),
                CommandHandler('unset', unset),
                MessageHandler(filters.Regex('^Reset$'), reset)
            ],
            SET_FROM_STATE: [
                CallbackQueryHandler(set_from_station)
            ],
            SET_FROM_STATION: [
                CallbackQueryHandler(set_from_state, pattern='^Back$'),
                CallbackQueryHandler(set_to_state)
            ],
            SET_TO_STATE: [
                CallbackQueryHandler(set_from_station, pattern='^Back$'),
                CallbackQueryHandler(set_to_station)
            ],
            SET_TO_STATION: {
                CallbackQueryHandler(set_to_state, pattern='^Back$'),
                CallbackQueryHandler(set_date)
            },
            SET_DATE: [
                CallbackQueryHandler(set_to_station, pattern='^Back$'),
                CallbackQueryHandler(set_trip),
                MessageHandler(filters.Regex('^\\d{4}-\\d{2}-\\d{2}$'), set_trip)
            ],
            SET_TRIP: [
                CallbackQueryHandler(set_date, pattern='^Back$'),
                CallbackQueryHandler(set_track)
            ],
            SET_TRACK: [
                CallbackQueryHandler(set_trip, pattern='^Back$'),
                CallbackQueryHandler(set_reserve, pattern='^-?\\d+$')
            ]
        },
        fallbacks=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex(f'^{NEW}$'), set_from_state),
            MessageHandler(filters.Regex(f'^{VIEW}$'), view_tracking),
            MessageHandler(filters.Regex(f'^{re.escape(LOGIN)}$'), login_ktmb),
            MessageHandler(filters.Regex(f'^{re.escape(LOGOUT)}$'), logout_ktmb)
        ],
        name='ktmb_conversation',
        persistent=True
    )
    # Add ConversationHandler to application that will be used for handling updates
    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
