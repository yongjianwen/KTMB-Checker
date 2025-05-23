import json
import logging
import re
import uuid
from datetime import datetime

import requests
from apscheduler.jobstores.base import JobLookupError
from telegram import InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import (
    ContextTypes
)

from jobs.tracking_job_manager import (
    scheduler
)
from services.ktmb import (
    get_stations,
    get_trips,
    login, logout
)
from utils.bot_helper import (
    strikethrough_last_message, show_error_inline, show_error_reply,
    enable_strikethrough, enable_hide_keyboard_only, disable_strikethrough
)
from utils.constants import (
    START,
    SET_TRIP,
    SET_TRACK,
    VIEW_TRACK,
    VIEW_TRACKS,
    TRACKING_JOB_ID,
    Title
)
from utils.constants import (
    UUID_PATTERN, COOKIE, TOKEN, EMAIL, PASSWORD, LAST_MESSAGE, STATE, TO_STRIKETHROUGH, TO_HIDE_KEYBOARD,
    TRANSACTION, VOLATILE, STATIONS_DATA, TRACKING_LIST,
    FROM_STATE_NAME, FROM_STATION_ID, FROM_STATION_NAME,
    TO_STATE_NAME, TO_STATION_ID, TO_STATION_NAME,
    DATE, DEPARTURE_TIME, ARRIVAL_TIME, PRICE,
    SEARCH_DATA, TRIPS_DATA, TRIP_DATA, LAYOUT_DATA, OVERALL_PRICES, PARTIAL_CONTENT,
    TRACKING_UUID,
    RESERVED_SEAT
)
from utils.keyboard_helper import (
    build_times_keyboard,
    build_tracking_prices_keyboard,
    build_tracked_actions_keyboard,
    build_view_trackings_keyboard,
    build_reserved_actions_keyboard
)
from utils.ktmb_helper import (
    get_station_by_id, get_seats_contents
)
from utils.message_helper import (
    get_tracking_content
)
from utils.utils import (
    malaysia_now_datetime, get_number_emoji_from
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger('bot')


async def set_track(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    match = re.search(f'{SET_TRIP}:(.*)', query.data)
    if match:
        index = int(match.group(1))
        trip = context.user_data.get(VOLATILE, {}).get(TRIPS_DATA)[index]
        context.user_data.get(VOLATILE, {})[TRIP_DATA] = trip.get(TRIP_DATA)
        context.user_data.get(TRANSACTION, {})[DEPARTURE_TIME] = trip.get(DEPARTURE_TIME)
        context.user_data.get(TRANSACTION, {})[ARRIVAL_TIME] = trip.get(ARRIVAL_TIME)
    else:
        return context.user_data.get(STATE)

    enable_strikethrough(context.user_data)

    if any(
            t for t in context.user_data.get(TRACKING_LIST, []) if
            t.get(FROM_STATE_NAME) == context.user_data.get(TRANSACTION, {}).get(FROM_STATE_NAME) and
            t.get(FROM_STATION_NAME) == context.user_data.get(TRANSACTION, {}).get(FROM_STATION_NAME) and
            t.get(TO_STATE_NAME) == context.user_data.get(TRANSACTION, {}).get(TO_STATE_NAME) and
            t.get(TO_STATION_NAME) == context.user_data.get(TRANSACTION, {}).get(TO_STATION_NAME) and
            t.get(DATE) == context.user_data.get(TRANSACTION, {}).get(DATE) and
            t.get(DEPARTURE_TIME) == context.user_data.get(TRANSACTION, {}).get(DEPARTURE_TIME) and
            t.get(ARRIVAL_TIME) == context.user_data.get(TRANSACTION, {}).get(ARRIVAL_TIME)
    ):
        context.user_data[TO_STRIKETHROUGH] = True
        context.user_data[TO_HIDE_KEYBOARD] = False
        await show_error_inline(
            context,
            'Same tracking already exists',
            InlineKeyboardMarkup(
                build_times_keyboard(
                    context.user_data.get(VOLATILE, {}).get(TRIPS_DATA),
                    f'{SET_TRIP}:',
                    True
                )
            )
        )
        context.user_data.get(TRANSACTION, {}).pop(DEPARTURE_TIME, None)
        context.user_data.get(TRANSACTION, {}).pop(ARRIVAL_TIME, None)
        context.user_data.get(VOLATILE, {}).pop(PARTIAL_CONTENT, None)
        context.user_data[STATE] = SET_TRIP
        return SET_TRIP

    session = requests.Session()
    if COOKIE in context.user_data:
        session.cookies.update(context.user_data.get(COOKIE))

    res = await get_seats_contents(
        context.user_data.get(VOLATILE, {}).get(SEARCH_DATA),
        context.user_data.get(VOLATILE, {}).get(TRIP_DATA),
        session,
        context.user_data.get(TOKEN)
    )
    if not res.get('status'):
        context.user_data[TO_STRIKETHROUGH] = True
        context.user_data[TO_HIDE_KEYBOARD] = False
        await show_error_inline(
            context,
            res.get('error'),
            InlineKeyboardMarkup(
                build_times_keyboard(
                    context.user_data.get(VOLATILE, {}).get(TRIPS_DATA),
                    f'{SET_TRIP}:',
                    True
                )
            )
        )
        context.user_data.get(TRANSACTION, {}).pop(DEPARTURE_TIME, None)
        context.user_data.get(TRANSACTION, {}).pop(ARRIVAL_TIME, None)
        context.user_data.get(VOLATILE, {}).pop(PARTIAL_CONTENT, None)
        context.user_data[STATE] = SET_TRIP
        return SET_TRIP
    else:
        context.user_data[COOKIE] = session.cookies

    context.user_data.get(VOLATILE, {})[LAYOUT_DATA] = res.get(LAYOUT_DATA)
    context.user_data.get(VOLATILE, {})[OVERALL_PRICES] = res.get(OVERALL_PRICES)
    context.user_data.get(VOLATILE, {})[PARTIAL_CONTENT] = res.get(PARTIAL_CONTENT)

    reply_markup = InlineKeyboardMarkup(
        build_tracking_prices_keyboard(context.user_data.get(VOLATILE, {})[OVERALL_PRICES], f'{SET_TRACK}:', True))
    message = (
        f'{get_tracking_content(
            context.user_data.get(TRANSACTION, {}),
            context.user_data.get(VOLATILE, {}),
            Title.CREATE_TRACKING_PRICE.value
        )}'
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

    context.user_data[STATE] = SET_TRACK
    return SET_TRACK


async def cancel_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    tracking_uuid = re.search(UUID_PATTERN, query.data).group(0)
    context.user_data[TRACKING_LIST] = [
        t for t in context.user_data.get(TRACKING_LIST, []) if t.get(TRACKING_UUID) != uuid.UUID(tracking_uuid)
    ]

    if not context.user_data.get(TRACKING_LIST, []):
        try:
            scheduler.remove_job(f'{TRACKING_JOB_ID}_{update.effective_message.chat_id}')
        except JobLookupError:
            logger.info('>> Cancel tracking error - job may have already been cancelled')

    enable_strikethrough(context.user_data)

    await strikethrough_last_message(context)

    disable_strikethrough(context.user_data)

    context.user_data[STATE] = START
    return START


async def view_trackings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is None:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )
        await strikethrough_last_message(context)
    else:
        await query.answer()

    enable_hide_keyboard_only(context.user_data)

    if TRACKING_LIST not in context.user_data or len(context.user_data.get(TRACKING_LIST, [])) == 0:
        context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
            'No tracking found',
            reply_markup=None,
            parse_mode='HTML'
        )
        context.user_data[STATE] = START
        return START

    count = len(context.user_data.get(TRACKING_LIST, []))

    reply_markup = InlineKeyboardMarkup(
        build_view_trackings_keyboard(context.user_data.get(TRACKING_LIST, []), f'{VIEW_TRACKS}:')
    )
    message = f'<b>👀 You currently have {count} tracking{'' if count == 1 else 's'}</b>\n\n'

    for index, t in enumerate(context.user_data.get(TRACKING_LIST, [])):
        message = message + get_tracking_content(
            t,
            {},
            f'⬇️ Tracking {get_number_emoji_from(index + 1)}'
        ) + '\n'

    if query is None:
        context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    context.user_data[STATE] = VIEW_TRACKS
    return VIEW_TRACKS


async def view_single_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if re.compile(f'^{VIEW_TRACKS}:{UUID_PATTERN}$').match(query.data):
        tracking_uuid = re.search(UUID_PATTERN, query.data).group(0)
        index, t = next(
            (index, t) for index, t in enumerate(context.user_data.get(TRACKING_LIST, []))
            if t.get(TRACKING_UUID) == uuid.UUID(tracking_uuid)
        )
    else:
        return context.user_data.get(STATE)

    enable_hide_keyboard_only(context.user_data)

    session = requests.Session()
    if COOKIE in context.user_data:
        session.cookies.update(context.user_data.get(COOKIE))

    res = get_stations(session)
    if not res.get('status'):
        await show_error_reply(update, context, res.get('error'))
        context.user_data[STATE] = START
        return START
    else:
        context.user_data[COOKIE] = session.cookies

    stations_data = res.get(STATIONS_DATA)

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

    year, month, day = date.split('-')

    res = get_trips(
        session,
        datetime(int(year), int(month), int(day)),
        get_station_by_id(stations_data, from_station_id),
        get_station_by_id(stations_data, to_station_id),
        context.user_data.get(TOKEN)
    )
    if not res.get('status'):
        logout(session)
        session = requests.Session()
        res = login(session, context.user_data.get(EMAIL), context.user_data.get(PASSWORD))
        if res.get('status'):
            context.user_data[COOKIE] = session.cookies
            context.user_data[TOKEN] = res.get(TOKEN)

            res = get_trips(
                session,
                datetime(int(year), int(month), int(day)),
                get_station_by_id(stations_data, from_station_id),
                get_station_by_id(stations_data, to_station_id),
                context.user_data.get(TOKEN)
            )

            if not res.get('status'):
                context.user_data[TO_STRIKETHROUGH] = True
                context.user_data[TO_HIDE_KEYBOARD] = False
                await show_error_inline(
                    context,
                    res.get('error'),
                    None
                )
                context.user_data.get(TRANSACTION, {}).pop(DATE, None)
                context.user_data[STATE] = START
                return START
            else:
                context.user_data[COOKIE] = session.cookies
        else:
            context.user_data[TO_STRIKETHROUGH] = True
            context.user_data[TO_HIDE_KEYBOARD] = False
            await show_error_inline(
                context,
                res.get('error'),
                None
            )
            context.user_data.get(TRANSACTION, {}).pop(DATE, None)
            context.user_data[STATE] = START
            return START
        # await show_error_reply(update, context, res.get('error'))
        # context.user_data[STATE] = START
        # return START
    # logger.info('trips_res:', trips_res)
    else:
        context.user_data[COOKIE] = session.cookies

    search_data = res.get(SEARCH_DATA)
    trips_data = json.loads(json.dumps(res.get(TRIPS_DATA)))
    if trips_data:
        trip = next(tr for tr in trips_data if tr.get(DEPARTURE_TIME) == departure_time)
        trip_data = trip.get(TRIP_DATA)

        res = await get_seats_contents(
            search_data,
            trip_data,
            session,
            context.user_data.get(TOKEN)
        )
        if not res.get('status'):
            await show_error_reply(update, context, res.get('error'))
            context.user_data[STATE] = START
            return START
        else:
            context.user_data[COOKIE] = session.cookies

        partial_content = res.get(PARTIAL_CONTENT)
    else:
        partial_content = 'No trips found\n'

    if reserved_seat is None:
        reply_markup = InlineKeyboardMarkup(build_tracked_actions_keyboard(tracking_uuid, f'{VIEW_TRACK}:', True))
        price_message = 'any price' if price == -1 else f'RM {price}'
        context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
            (
                f'{get_tracking_content(
                    t,
                    {PARTIAL_CONTENT: partial_content},
                    f'{Title.TRACKING_NUM.value} {get_number_emoji_from(index + 1)}'
                )}'
                '\n'
                f'<i>Refreshed at: {malaysia_now_datetime().strftime('%H:%M:%S')}</i>\n'
                '\n'
                f'<b>Reserve a random seat of {price_message}?</b>'
            ),
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        reply_markup = InlineKeyboardMarkup(build_reserved_actions_keyboard(tracking_uuid, f'{VIEW_TRACK}:', True))
        context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
            (
                f'{get_tracking_content(
                    t,
                    {PARTIAL_CONTENT: partial_content},
                    f'{Title.TRACKING_NUM.value} {get_number_emoji_from(index + 1)}'
                )}'
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

    context.user_data[STATE] = VIEW_TRACK
    return VIEW_TRACK
