import re
import uuid

import requests
from telegram import InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import (
    ContextTypes
)

from services.ktmb import (
    get_stations
)
from utils.bot_helper import (
    strikethrough_last_message, show_error_inline, enable_strikethrough, disable_strikethrough
)
from utils.constants import (
    BACK_DATA
)
from utils.constants import (
    COOKIE, LAST_MESSAGE, STATE, SHORTCUTS,
    TRANSACTION, VOLATILE, STATIONS_DATA, FROM_STATE_NAME, FROM_STATION_ID, FROM_STATION_NAME,
    TO_STATE_NAME, TO_STATION_ID, TO_STATION_NAME
)
from utils.constants import (
    START,
    ADD_FROM_STATE, ADD_FROM_STATION,
    ADD_TO_STATE, ADD_TO_STATION,
    SHORTCUT, SELECTED_SHORTCUT,
    SET_FROM_STATE, SET_FROM_STATION,
    SET_TO_STATE, SET_TO_STATION,
    Title
)
from utils.keyboard_helper import (
    build_shortcuts_keyboard, build_shortcut_actions_keyboard,
    build_states_keyboard, build_stations_keyboard,
)
from utils.ktmb_helper import (
    get_station_by_id
)
from utils.message_helper import (
    get_tracking_content
)


# region Common
async def build_from_state(update, context, state, prefix, show_shortcuts, title):
    query = update.callback_query
    if query is None:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )
        await strikethrough_last_message(context)
    else:
        await query.answer()

    enable_strikethrough(context.user_data)
    context.user_data[TRANSACTION] = {}
    context.user_data[VOLATILE] = {}

    session = requests.Session()
    if COOKIE in context.user_data:
        session.cookies.update(context.user_data.get(COOKIE))

    res = get_stations(session)
    if not res.get('status'):
        enable_strikethrough(context.user_data)
        await show_error_inline(context, res, None)
        context.user_data[STATE] = state
        return state

    context.user_data[STATIONS_DATA] = res.get(STATIONS_DATA)

    reply_markup = InlineKeyboardMarkup(
        build_states_keyboard(
            context.user_data.get(STATIONS_DATA, []),
            context.user_data.get(SHORTCUTS, {}) if show_shortcuts else {},
            prefix
        )
    )
    message = (
        f'{get_tracking_content(
            context.user_data.get(TRANSACTION, {}),
            {},
            title
        )}'
        '\n'
        'Where are you departing from?'
    )

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


async def build_from_station(update, context, prefix, prev_prefix, next_prefix, title):
    query = update.callback_query
    await query.answer()
    if query.data != next_prefix + BACK_DATA:
        match = re.search(f'{prev_prefix}(.*)', query.data)
        if match:
            context.user_data.get(TRANSACTION, {})[FROM_STATE_NAME] = match.group(1)
        else:
            return context.user_data.get(STATE)

    enable_strikethrough(context.user_data)
    context.user_data.get(TRANSACTION, {}).pop(FROM_STATION_ID, None)
    context.user_data.get(TRANSACTION, {}).pop(FROM_STATION_NAME, None)

    reply_markup = InlineKeyboardMarkup(
        build_stations_keyboard(
            context.user_data.get(STATIONS_DATA, []),
            context.user_data.get(TRANSACTION, {}).get(FROM_STATE_NAME),
            prefix,
            True
        )
    )
    message = (
        f'{get_tracking_content(
            context.user_data.get(TRANSACTION, {}),
            {},
            title
        )}'
    )

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def build_to_state(update, context, prefix, prev_prefix, next_prefix, title):
    query = update.callback_query
    await query.answer()
    if query.data != next_prefix + BACK_DATA:
        match = re.search(f'{prev_prefix}(.*)', query.data)
        if match:
            context.user_data.get(TRANSACTION, {})[FROM_STATION_ID] = match.group(1)
            context.user_data.get(TRANSACTION, {})[FROM_STATION_NAME] = get_station_by_id(
                context.user_data.get(STATIONS_DATA, []),
                context.user_data.get(TRANSACTION, {}).get(FROM_STATION_ID)
            ).get('Description')
        else:
            return context.user_data.get(STATE)

    enable_strikethrough(context.user_data)
    context.user_data.get(TRANSACTION, {}).pop(TO_STATE_NAME, None)

    reply_markup = InlineKeyboardMarkup(
        build_states_keyboard(context.user_data.get(STATIONS_DATA, []), {}, prefix, True))
    message = (
        f'{get_tracking_content(
            context.user_data.get(TRANSACTION, {}),
            {},
            title
        )}'
        '\n'
        'Where are you going to?'
    )

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def build_to_station(update, context, prefix, prev_prefix, next_prefix, title):
    query = update.callback_query
    await query.answer()
    if query.data != next_prefix + BACK_DATA:
        match = re.search(f'{prev_prefix}(.*)', query.data)
        if match:
            context.user_data.get(TRANSACTION, {})[TO_STATE_NAME] = match.group(1)
        else:
            return context.user_data.get(STATE)

    enable_strikethrough(context.user_data)
    context.user_data.get(TRANSACTION, {}).pop(TO_STATION_ID, None)
    context.user_data.get(TRANSACTION, {}).pop(TO_STATION_NAME, None)

    reply_markup = InlineKeyboardMarkup(
        build_stations_keyboard(
            context.user_data.get(STATIONS_DATA, []),
            context.user_data.get(TRANSACTION, {}).get(TO_STATE_NAME),
            prefix,
            True
        )
    )
    message = (
        f'{get_tracking_content(
            context.user_data.get(TRANSACTION, {}),
            {},
            title
        )}'
    )

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


# endregion Common


# region Shortcut
async def manage_shortcuts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is None:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )
        await strikethrough_last_message(context)
    else:
        await query.answer()

    enable_strikethrough(context.user_data)

    reply_markup = InlineKeyboardMarkup(
        build_shortcuts_keyboard(context.user_data.get(SHORTCUTS, {}), 'shortcut:', True)
    )
    message = '⬇️ Select a shortcut below to manage, or add a new shortcut' if context.user_data.get(SHORTCUTS) \
        else '⬇️ Click below button to add a new shortcut'

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

    context.user_data[STATE] = SHORTCUT
    return SHORTCUT


async def add_from_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await build_from_state(update, context, ADD_FROM_STATE, 'add_from_state:', False, Title.ADD_SHORTCUT.value)

    context.user_data[STATE] = ADD_FROM_STATE
    return ADD_FROM_STATE


async def add_from_station(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await build_from_station(
        update,
        context,
        'add_from_station:',
        'add_from_state:',
        'add_to_state:',
        Title.ADD_SHORTCUT.value
    )

    context.user_data[STATE] = ADD_FROM_STATION
    return ADD_FROM_STATION


async def add_to_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await build_to_state(
        update,
        context,
        'add_to_state:',
        'add_from_station:',
        'add_to_station:',
        Title.ADD_SHORTCUT.value
    )

    context.user_data[STATE] = ADD_TO_STATE
    return ADD_TO_STATE


async def add_to_station(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await build_to_station(
        update,
        context,
        'add_to_station:',
        'add_to_state:',
        'add_date:',
        Title.ADD_SHORTCUT.value
    )

    context.user_data[STATE] = ADD_TO_STATION
    return ADD_TO_STATION


async def added_shortcut(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    match = re.search('add_to_station:(.*)', query.data)
    if match:
        context.user_data.get(TRANSACTION, {})[TO_STATION_ID] = match.group(1)
        context.user_data.get(TRANSACTION, {})[TO_STATION_NAME] = get_station_by_id(
            context.user_data.get(STATIONS_DATA, []), context.user_data.get(TRANSACTION, {})[TO_STATION_ID]
        ).get('Description')
    else:
        return context.user_data.get(STATE)

    disable_strikethrough(context.user_data)

    if SHORTCUTS not in context.user_data:
        context.user_data[SHORTCUTS] = {}

    temp = context.user_data.get(TRANSACTION, {})
    for shortcut in context.user_data.get(SHORTCUTS, {}).values():
        if shortcut.get(FROM_STATE_NAME) == temp.get(FROM_STATE_NAME) \
                and shortcut.get(FROM_STATION_ID) == temp.get(FROM_STATION_ID) \
                and shortcut.get(FROM_STATION_NAME) == temp.get(FROM_STATION_NAME) \
                and shortcut.get(TO_STATE_NAME) == temp.get(TO_STATE_NAME) \
                and shortcut.get(TO_STATION_ID) == temp.get(TO_STATION_ID) \
                and shortcut.get(TO_STATION_NAME) == temp.get(TO_STATION_NAME):
            reply_markup = InlineKeyboardMarkup(
                build_stations_keyboard(
                    context.user_data.get(STATIONS_DATA, []),
                    context.user_data.get(TRANSACTION, {}).get(TO_STATE_NAME),
                    'add_to_station:',
                    True
                )
            )
            message = (
                f'{get_tracking_content(
                    context.user_data.get(TRANSACTION, {}),
                    {},
                    Title.ADD_SHORTCUT.value
                )}'
                '\n'
                '🔴 Shortcut already exists\n\n🟢 Manage /shortcut instead, or select a different combination'
            )
            if message != context.user_data.get(LAST_MESSAGE).text_html:
                context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
                    message,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            context.user_data[STATE] = ADD_TO_STATION
            return ADD_TO_STATION

    shortcut_uuid = uuid.uuid4()
    shortcut = {
        FROM_STATE_NAME: context.user_data.get(TRANSACTION, {})[FROM_STATE_NAME],
        FROM_STATION_ID: context.user_data.get(TRANSACTION, {})[FROM_STATION_ID],
        FROM_STATION_NAME: context.user_data.get(TRANSACTION, {})[FROM_STATION_NAME],
        TO_STATE_NAME: context.user_data.get(TRANSACTION, {})[TO_STATE_NAME],
        TO_STATION_ID: context.user_data.get(TRANSACTION, {})[TO_STATION_ID],
        TO_STATION_NAME: context.user_data.get(TRANSACTION, {})[TO_STATION_NAME]
    }
    context.user_data.get(SHORTCUTS, {})[shortcut_uuid] = shortcut
    context.user_data.pop(TRANSACTION, None)

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        f'{get_tracking_content(
            shortcut,
            {},
            Title.ADDED_SHORTCUT.value
        )}',
        reply_markup=None,
        parse_mode='HTML'
    )

    context.user_data[STATE] = START
    return START


async def selected_shortcut(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    match = re.search('shortcut:(.*)', query.data)
    if match:
        shortcut_uuid = match.group(1)
    else:
        return context.user_data.get(STATE)

    enable_strikethrough(context.user_data)

    reply_markup = InlineKeyboardMarkup(build_shortcut_actions_keyboard(shortcut_uuid, 'selected_shortcut:', True))

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        (
            f'{get_tracking_content(
                context.user_data.get(SHORTCUTS, {}).get(uuid.UUID(shortcut_uuid)),
                {},
                Title.MANAGE_SHORTCUT.value
            )}'
            '\n'
            '⬇️ Choose an action below'
        ),
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    context.user_data[STATE] = SELECTED_SHORTCUT
    return SELECTED_SHORTCUT


async def deleted_shortcut(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    query = update.callback_query
    match = re.search('Delete Shortcut/(.*)', query.data)
    if match:
        shortcut_uuid = match.group(1)
    else:
        return context.user_data.get(STATE)

    shortcut = context.user_data.get(SHORTCUTS, {}).get(uuid.UUID(shortcut_uuid))

    disable_strikethrough(context.user_data)
    context.user_data.get(SHORTCUTS, {}).pop(uuid.UUID(shortcut_uuid), None)

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        f'{get_tracking_content(
            shortcut,
            {},
            Title.DELETED_SHORTCUT.value
        )}',
        reply_markup=None,
        parse_mode='HTML'
    )

    context.user_data[STATE] = START
    return START


# endregion Shortcut


# region Tracking
async def set_from_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await build_from_state(
        update,
        context,
        SET_FROM_STATE,
        'set_from_state:',
        True,
        Title.CREATE_TRACKING_FROM_STATE.value
    )

    context.user_data[STATE] = SET_FROM_STATE
    return SET_FROM_STATE


async def set_from_station(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await build_from_station(
        update,
        context,
        'set_from_station:',
        'set_from_state:',
        'set_to_state:',
        Title.CREATE_TRACKING_FROM_STATION.value
    )

    context.user_data[STATE] = SET_FROM_STATION
    return SET_FROM_STATION


async def set_to_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await build_to_state(
        update,
        context,
        'set_to_state:',
        'set_from_station:',
        'set_to_station:',
        Title.CREATE_TRACKING_TO_STATE.value
    )

    context.user_data[STATE] = SET_TO_STATE
    return SET_TO_STATE


async def set_to_station(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await build_to_station(
        update,
        context,
        'set_to_station:',
        'set_to_state:',
        'set_date:',
        Title.CREATE_TRACKING_TO_STATION.value
    )

    context.user_data[STATE] = SET_TO_STATION
    return SET_TO_STATION

# endregion Tracking
