import logging

from ktmb import get_seats
from utils import COOKIE, TOKEN, LAST_MESSAGE, TO_STRIKETHROUGH, FROM_STATE_NAME, FROM_STATION_ID, \
    FROM_STATION_NAME, TO_STATE_NAME, TO_STATION_ID, TO_STATION_NAME, DATE, DEPARTURE_TIME, ARRIVAL_TIME, \
    PARTIAL_CONTENT, SEARCH_DATA, TRIPS_DATA, TRIP_DATA, LAYOUT_DATA, PRICE, get_tracking_content, TO_HIDE_KEYBOARD, \
    STATIONS_DATA


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logging.getLogger('httpx').setLevel(logging.INFO)
logger = logging.getLogger(__name__)


async def get_seats_contents(search_data, trip_data, session, token):
    # logger.info(data)
    res = get_seats(
        session,
        search_data,
        trip_data,
        token
    )
    if not res.get('status'):
        return {
            'status': False,
            'error': res.get('error')
        }

    layout_data = res.get('layout_data')
    seats_data = res.get('seats_data')
    # logger.info(seats_data)

    contents = ''
    overall_prices = set()
    for coach in seats_data:
        line = f'{coach.get('CoachLabel')}: '
        seats_left = coach.get('CoachData').get('SeatsLeft')
        line += f'{seats_left} seats left'
        if seats_left != 0:
            line += ' ('
            for price in coach.get('CoachData').get('Prices'):
                line += f'RM {str(price)} / '
                overall_prices.add(price)
            line = line[:-3] + ')'
        contents += line + '\n'

    return {
        'status': True,
        'layout_data': layout_data,
        'seats_data': seats_data,
        'overall_prices': overall_prices,
        PARTIAL_CONTENT: contents,
        'seats_left_by_prices': res.get('seats_left_by_prices')
    }


async def cancel_last_message(context):
    if context.user_data.get(LAST_MESSAGE):
        last_message = context.user_data.get(LAST_MESSAGE)
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


async def display_error_inline(context, res, reply_markup=None):
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


async def reply_error(update, context, res):
    context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
        f'❌ We encountered an error. Please try again later.\n\n👾 For dev: {res.get('error')}',
        reply_markup=None,
        parse_mode='HTML'
    )
    context.user_data[TO_STRIKETHROUGH] = False


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
