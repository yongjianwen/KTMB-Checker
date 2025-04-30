import logging

from .constants import (
    COOKIE,
    TOKEN,
    LAST_MESSAGE,
    TO_STRIKETHROUGH, TO_HIDE_KEYBOARD,
    SEARCH_DATA, TRIPS_DATA,
    TRIP_DATA, LAYOUT_DATA, STATIONS_DATA
)
from .ktmb_helper import get_tracking_content

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logging.getLogger('httpx').setLevel(logging.INFO)
logger = logging.getLogger(__name__)


async def strikethrough_last_message(context):
    last_message = context.user_data.get(LAST_MESSAGE)
    if last_message:
        try:
            if context.user_data.get(TO_STRIKETHROUGH):
                context.user_data[LAST_MESSAGE] = await context.bot.edit_message_text(
                    chat_id=last_message.chat_id,
                    message_id=last_message.message_id,
                    text=f'<s>{last_message.text_html}</s>\n\n<b><i>Transaction cancelled</i></b>',
                    reply_markup=None,
                    parse_mode='HTML'
                )
            elif context.user_data.get(TO_HIDE_KEYBOARD):
                await context.bot.edit_message_reply_markup(
                    chat_id=last_message.chat_id,
                    message_id=last_message.message_id,
                    reply_markup=None
                )
        except Exception as e:
            logger.info(e)


async def show_error_inline(context, res, reply_markup=None):
    last_message = context.user_data.get(LAST_MESSAGE)
    if last_message:
        message = (
            f'{get_tracking_content(context.user_data.get('transaction', {}), context.user_data.get('volatile', {}))}'
            '\n'
            f'❌ We encountered an error. Please try again later.\n\n👾 For dev: {res.get('error')}'
        )
        if message != last_message.text_html:
            context.user_data[LAST_MESSAGE] = await context.bot.edit_message_text(
                chat_id=last_message.chat_id,
                message_id=last_message.message_id,
                text=message,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )


async def show_error_reply(update, context, res):
    disable_strikethrough(context.user_data)
    context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
        f'❌ We encountered an error. Please try again later.\n\n👾 For dev: {res.get('error')}',
        reply_markup=None,
        parse_mode='HTML'
    )


def enable_strikethrough(data):
    data[TO_STRIKETHROUGH] = True
    data[TO_HIDE_KEYBOARD] = True


def enable_hide_keyboard_only(data):
    data[TO_STRIKETHROUGH] = False
    data[TO_HIDE_KEYBOARD] = True


def disable_strikethrough(data):
    data[TO_STRIKETHROUGH] = False
    data[TO_HIDE_KEYBOARD] = False


def clear_session_data(context, auto_logout=False):
    if not auto_logout:
        context.user_data.pop('email', None)
        context.user_data.pop('password', None)
    context.user_data.pop(COOKIE, None)
    context.user_data.pop(TOKEN, None)


# def clear_temp_data(context, auto_logout=False):
#     if not auto_logout:
#         context.user_data.pop(FROM_STATE_NAME, None)
#         context.user_data.pop(FROM_STATION_ID, None)
#         context.user_data.pop(FROM_STATION_NAME, None)
#         context.user_data.pop(TO_STATE_NAME, None)
#         context.user_data.pop(TO_STATION_ID, None)
#         context.user_data.pop(TO_STATION_NAME, None)
#         context.user_data.pop(DATE, None)
#         context.user_data.pop(DEPARTURE_TIME, None)
#         context.user_data.pop(ARRIVAL_TIME, None)
#
#     context.user_data.pop(STATIONS_DATA, None)
#     context.user_data.pop(PARTIAL_CONTENT, None)
#     context.user_data.pop(SEARCH_DATA, None)
#     context.user_data.pop(TRIPS_DATA, None)
#     context.user_data.pop(TRIP_DATA, None)
#     context.user_data.pop(LAYOUT_DATA, None)
#     context.user_data.pop(PRICE, None)


def clear_volatile_data(context):
    context.user_data.pop(STATIONS_DATA, None)
    context.user_data.pop(SEARCH_DATA, None)
    context.user_data.pop(TRIPS_DATA, None)
    context.user_data.pop(TRIP_DATA, None)
    context.user_data.pop(LAYOUT_DATA, None)
