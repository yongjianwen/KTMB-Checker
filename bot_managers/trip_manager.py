import json
import re
import uuid
from datetime import datetime

import requests
from telegram import InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes
)

from services.ktmb import (
    get_trips
)
from utils.bot_helper import (
    show_error_inline, enable_strikethrough
)
from utils.constants import (
    BACK_DATA
)
from utils.constants import (
    SET_FROM_STATE,
    SET_TO_STATION,
    SET_DATE,
    SET_TRIP,
    SET_TRACK,
    Title
)
from utils.constants import (
    UUID_PATTERN, COOKIE, TOKEN, LAST_MESSAGE, STATE, TO_STRIKETHROUGH, TO_HIDE_KEYBOARD,
    SHORTCUTS,
    TRANSACTION, VOLATILE, STATIONS_DATA, FROM_STATE_NAME, FROM_STATION_ID, FROM_STATION_NAME,
    TO_STATE_NAME, TO_STATION_ID, TO_STATION_NAME,
    DATE, DEPARTURE_TIME, ARRIVAL_TIME, SEARCH_DATA, TRIPS_DATA, PARTIAL_CONTENT
)
from utils.keyboard_helper import (
    build_dates_keyboard, build_times_keyboard,
)
from utils.ktmb_helper import (
    get_station_by_id
)
from utils.message_helper import (
    get_tracking_content
)


async def set_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data != f'{SET_TRIP}:' + BACK_DATA:
        match = re.search(f'{SET_TO_STATION}:(.*)', query.data)
        if match:
            context.user_data.get(TRANSACTION, {})[TO_STATION_ID] = match.group(1)
            context.user_data.get(TRANSACTION, {})[TO_STATION_NAME] = get_station_by_id(
                context.user_data.get(STATIONS_DATA, []), context.user_data.get(TRANSACTION, {})[TO_STATION_ID]
            ).get('Description')
        else:
            match = re.search(f'{SET_FROM_STATE}:({UUID_PATTERN})', query.data)
            if match:
                shortcut_uuid = match.group(1)
                t = context.user_data.get(SHORTCUTS, {}).get(uuid.UUID(shortcut_uuid))
                context.user_data.get(TRANSACTION, {})[FROM_STATE_NAME] = t.get(FROM_STATE_NAME)
                context.user_data.get(TRANSACTION, {})[FROM_STATION_ID] = t.get(FROM_STATION_ID)
                context.user_data.get(TRANSACTION, {})[FROM_STATION_NAME] = t.get(FROM_STATION_NAME)
                context.user_data.get(TRANSACTION, {})[TO_STATE_NAME] = t.get(TO_STATE_NAME)
                context.user_data.get(TRANSACTION, {})[TO_STATION_ID] = t.get(TO_STATION_ID)
                context.user_data.get(TRANSACTION, {})[TO_STATION_NAME] = t.get(TO_STATION_NAME)
            else:
                return context.user_data.get(STATE)

    enable_strikethrough(context.user_data)
    context.user_data.get(TRANSACTION, {}).pop(DATE, None)

    reply_markup = InlineKeyboardMarkup(build_dates_keyboard(f'{SET_DATE}:', True))
    message = (
        f'{get_tracking_content(
            context.user_data.get(TRANSACTION, {}),
            context.user_data.get(VOLATILE, {}),
            Title.CREATE_TRACKING_DATE.value
        )}'
        '\n'
        'What date? (YYYY-MM-DD, e.g. 2025-01-31)'
    )

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    context.user_data[STATE] = SET_DATE
    return SET_DATE


async def set_trip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        # From inline keyboard
        query = update.callback_query
        await query.answer()
        if query.data != f'{SET_TRACK}:' + BACK_DATA:
            match = re.search(f'{SET_DATE}:(.*)', query.data)
            if match:
                context.user_data.get(TRANSACTION, {})[DATE] = match.group(1)
            else:
                return context.user_data.get(STATE)
    else:
        # From normal keyboard
        context.user_data.get(TRANSACTION, {})[DATE] = update.message.text

    year, month, day = context.user_data.get(TRANSACTION, {}).get(DATE).split('-')

    enable_strikethrough(context.user_data)
    context.user_data.get(TRANSACTION, {}).pop(DEPARTURE_TIME, None)
    context.user_data.get(TRANSACTION, {}).pop(ARRIVAL_TIME, None)
    context.user_data.get(VOLATILE, {}).pop(PARTIAL_CONTENT, None)

    session = requests.Session()
    if COOKIE in context.user_data:
        session.cookies.update(context.user_data.get(COOKIE))

    res = get_trips(
        session,
        datetime(int(year), int(month), int(day)),
        get_station_by_id(
            context.user_data.get(STATIONS_DATA, []),
            context.user_data.get(TRANSACTION, {}).get(FROM_STATION_ID)
        ),
        get_station_by_id(
            context.user_data.get(STATIONS_DATA, []),
            context.user_data.get(TRANSACTION, {}).get(TO_STATION_ID)
        ),
        context.user_data.get(TOKEN)
    )
    if not res.get('status'):
        context.user_data[TO_STRIKETHROUGH] = True
        context.user_data[TO_HIDE_KEYBOARD] = False
        await show_error_inline(context, res, InlineKeyboardMarkup(build_dates_keyboard(f'{SET_DATE}:', True)))
        context.user_data.get(TRANSACTION, {}).pop(DATE, None)
        context.user_data[STATE] = SET_DATE
        return SET_DATE

    context.user_data.get(VOLATILE, {})[SEARCH_DATA] = res.get(SEARCH_DATA)
    context.user_data.get(VOLATILE, {})[TRIPS_DATA] = json.loads(json.dumps(res.get(TRIPS_DATA)))

    reply_markup = InlineKeyboardMarkup(
        build_times_keyboard(
            context.user_data.get(VOLATILE, {}).get(TRIPS_DATA),
            f'{SET_TRIP}:',
            True
        )
    )
    message = (
        f'{get_tracking_content(
            context.user_data.get(TRANSACTION, {}),
            context.user_data.get(VOLATILE, {}),
            Title.CREATE_TRACKING_TIME.value
        )}'
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

    context.user_data[STATE] = SET_TRIP
    return SET_TRIP
