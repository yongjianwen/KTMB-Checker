import logging
import re
import uuid

import requests
from telegram import InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes
)

from jobs.tracking_job_manager import (
    start_tracking_job, check_active_jobs
)
from services.ktmb import (
    reserve_by_price,
    cancel_reservation
)
from utils.bot_helper import (
    show_error_inline, enable_hide_keyboard_only
)
from utils.constants import (
    LOW_SEAT_COUNT
)
from utils.constants import (
    RESERVE_DATA, REFRESH_TRACKING_DATA, REFRESH_RESERVED_DATA, CANCEL_RESERVATION_DATA
)
from utils.constants import (
    SET_TRACK,
    VIEW_TRACK,
    RESERVED,
    Title
)
from utils.constants import (
    UUID_PATTERN, COOKIE, TOKEN, LAST_MESSAGE, STATE, TO_STRIKETHROUGH, TO_HIDE_KEYBOARD,
    TRANSACTION, VOLATILE, TRACKING_LIST,
    FROM_STATE_NAME, FROM_STATION_ID, FROM_STATION_NAME,
    TO_STATE_NAME, TO_STATION_ID, TO_STATION_NAME,
    DATE, DEPARTURE_TIME, ARRIVAL_TIME, PRICE,
    SEARCH_DATA, TRIP_DATA, LAYOUT_DATA, BOOKING_DATA, OVERALL_PRICES, PARTIAL_CONTENT,
    TRACKING_UUID,
    RESERVED_SEAT,
    SEATS_LEFT_BY_PRICES,
    LAST_REMINDED,
    INTERVALS_INDEX,
    IS_DANGEROUS
)
from utils.keyboard_helper import (
    build_tracking_prices_keyboard,
    build_tracked_actions_keyboard,
    build_reserved_actions_keyboard
)
from utils.ktmb_helper import (
    get_seats_contents
)
from utils.message_helper import (
    get_tracking_content
)
from utils.utils import (
    malaysia_now_datetime
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger('bot')


async def set_reserve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    is_refresh = False
    is_cancel = False
    if re.compile(f'^{REFRESH_TRACKING_DATA}/{UUID_PATTERN}$').match(query.data):
        tracking_uuid = re.search(UUID_PATTERN, query.data).group(0)
        is_refresh = True
    elif re.compile(f'^{CANCEL_RESERVATION_DATA}/{UUID_PATTERN}$').match(query.data):
        tracking_uuid = re.search(UUID_PATTERN, query.data).group(0)
        is_cancel = True
    else:
        match = re.search(f'{SET_TRACK}:(.*)', query.data)
        if match:
            context.user_data.get(TRANSACTION, {})[PRICE] = int(match.group(1))
        else:
            return context.user_data.get(STATE)
        # context.user_data.get(TRANSACTION, {})[PRICE] = int(query.data)
        if TRACKING_LIST not in context.user_data:
            context.user_data[TRACKING_LIST] = []
        tracking_uuid = uuid.uuid4()
        context.user_data[TRACKING_LIST].append(
            {
                TRACKING_UUID: tracking_uuid,
                FROM_STATE_NAME: context.user_data.get(TRANSACTION, {}).get(FROM_STATE_NAME),
                FROM_STATION_ID: context.user_data.get(TRANSACTION, {}).get(FROM_STATION_ID),
                FROM_STATION_NAME: context.user_data.get(TRANSACTION, {}).get(FROM_STATION_NAME),
                TO_STATE_NAME: context.user_data.get(TRANSACTION, {}).get(TO_STATE_NAME),
                TO_STATION_ID: context.user_data.get(TRANSACTION, {}).get(TO_STATION_ID),
                TO_STATION_NAME: context.user_data.get(TRANSACTION, {}).get(TO_STATION_NAME),
                DATE: context.user_data.get(TRANSACTION, {}).get(DATE),
                DEPARTURE_TIME: context.user_data.get(TRANSACTION, {}).get(DEPARTURE_TIME),
                ARRIVAL_TIME: context.user_data.get(TRANSACTION, {}).get(ARRIVAL_TIME),
                PRICE: context.user_data.get(TRANSACTION, {}).get(PRICE),
                RESERVED_SEAT: None,
                SEATS_LEFT_BY_PRICES: [],
                LAST_REMINDED: malaysia_now_datetime(),
                INTERVALS_INDEX: 0,
                IS_DANGEROUS: False
            }
        )

    enable_hide_keyboard_only(context.user_data)

    session = requests.Session()
    if COOKIE in context.user_data:
        session.cookies.update(context.user_data.get(COOKIE))

    if is_cancel:
        res = cancel_reservation(
            session,
            context.user_data.get(VOLATILE, {}).get(SEARCH_DATA),
            context.user_data.get(VOLATILE, {}).get(BOOKING_DATA),
            context.user_data.get(TOKEN)
        )
        if not res.get('status'):
            context.user_data[TO_STRIKETHROUGH] = False
            context.user_data[TO_HIDE_KEYBOARD] = True
            await show_error_inline(
                context,
                res.get('error'),
                InlineKeyboardMarkup(build_reserved_actions_keyboard(tracking_uuid))
            )
            context.user_data[STATE] = VIEW_TRACK
            return VIEW_TRACK
        else:
            context.user_data[COOKIE] = session.cookies
        for index, t in enumerate(context.user_data.get(TRACKING_LIST, [])):
            if t.get(TRACKING_UUID) == uuid.UUID(tracking_uuid):
                t[RESERVED_SEAT] = None
                context.user_data[TRACKING_LIST][index] = t
                break
        title = Title.CANCEL_RESERVATION.value
    # elif is_refresh:
    #     title = Title.REFRESH_TRACKING.value
    else:
        title = Title.ADDED_TRACKING.value

    # res = await get_seats_contents(context.user_data, session)
    res = await get_seats_contents(
        context.user_data.get(VOLATILE, {}).get(SEARCH_DATA),
        context.user_data.get(VOLATILE, {}).get(TRIP_DATA),
        session,
        context.user_data.get(TOKEN)
    )
    if not res.get('status') and not is_refresh:
        context.user_data[TO_STRIKETHROUGH] = True
        context.user_data[TO_HIDE_KEYBOARD] = False
        context.user_data.get(VOLATILE, {}).pop(PARTIAL_CONTENT, None)
        context.user_data[TRACKING_LIST].pop()
        await show_error_inline(
            context,
            res.get('error'),
            InlineKeyboardMarkup(
                build_tracking_prices_keyboard(
                    context.user_data.get(VOLATILE, {})[OVERALL_PRICES],
                    f'{SET_TRACK}:',
                    True
                )
            )
        )
        context.user_data[STATE] = SET_TRACK
        return SET_TRACK
    elif not res.get('status') and is_refresh:
        await show_error_inline(
            context,
            res.get('error'),
            InlineKeyboardMarkup(
                build_tracking_prices_keyboard(
                    context.user_data.get(VOLATILE, {})[OVERALL_PRICES],
                    f'{SET_TRACK}:',
                    True
                )
            )
        )
        context.user_data[STATE] = VIEW_TRACK
        return VIEW_TRACK
    elif res.get('status'):
        context.user_data[COOKIE] = session.cookies

    context.user_data.get(VOLATILE, {})[PARTIAL_CONTENT] = res.get(PARTIAL_CONTENT)
    for index, t in enumerate(context.user_data.get(TRACKING_LIST, [])):
        if t.get(TRACKING_UUID) == tracking_uuid:
            seats_left_by_prices = res.get(SEATS_LEFT_BY_PRICES)
            if t.get(PRICE) == -1:
                seats_left_by_tracking_price = sum(seats_left_by_prices.values())
            else:
                seats_left_by_tracking_price = seats_left_by_prices.get(str(t.get(PRICE)))
            t = {
                **t,
                SEATS_LEFT_BY_PRICES: res.get(SEATS_LEFT_BY_PRICES),
                IS_DANGEROUS: seats_left_by_tracking_price <= LOW_SEAT_COUNT
            }
            context.user_data[TRACKING_LIST][index] = t
            break
    # logger.info(context.user_data.get(TRACKING_LIST, []))

    if not is_refresh and not check_active_jobs():
        try:
            # year, month, day = context.user_data.get(TRANSACTION, {}).get(DATE).split('-')
            # hour, minute = context.user_data.get(TRANSACTION, {}).get(DEPARTURE_TIME).split(':')

            start_tracking_job(context, update.effective_message.chat_id)

            # scheduler.add_job(
            #     sync_alarm_wrapper,
            #     'interval',
            #     seconds=30,
            #     start_date=get_next_half_minute(),
            #     end_date=utc_to_malaysia_time(datetime(int(year), int(month), int(day), int(hour), int(minute))),
            #     args=[],
            #     kwargs={
            #         'context': context,
            #         # 'data': {
            #         #     COOKIE: context.user_data.get(COOKIE),
            #         #     TOKEN: context.user_data.get(TOKEN),
            #         #     'data': next(
            #         #         t for t in context.user_data.get(TRACKING_LIST, []) if
            #         #         t.get(TRACKING_UUID) == tracking_uuid
            #         #     )
            #         # },
            #         'chat_id': update.effective_message.chat_id
            #     },
            #     id=str(tracking_uuid)
            # )
            # scheduler.start()
        except Exception as e:
            logger.error(e)
            context.user_data[TO_STRIKETHROUGH] = False
            context.user_data[TO_HIDE_KEYBOARD] = True
            await show_error_inline(
                context,
                'Job scheduling error',
                InlineKeyboardMarkup(
                    build_tracking_prices_keyboard(
                        context.user_data.get(VOLATILE, {})[OVERALL_PRICES],
                        'set_track:',
                        True
                    )
                )
            )
            context.user_data[STATE] = SET_TRACK
            return SET_TRACK

    # logger.info('Number of jobs: ' + str(len(context.job_queue.jobs())))

    reply_markup = InlineKeyboardMarkup(build_tracked_actions_keyboard(tracking_uuid))
    price_message = 'any price' \
        if context.user_data.get(TRANSACTION, {}).get(PRICE) == -1 \
        else f'RM {context.user_data.get(TRANSACTION, {}).get(PRICE)}'
    message = (
        f'{get_tracking_content(
            context.user_data.get(TRANSACTION, {}),
            context.user_data.get(VOLATILE, {}),
            title
        )}'
        '\n'
        f'<i>Refreshed at: {malaysia_now_datetime().strftime('%H:%M:%S')}</i>\n'
        '\n'
        f'<b>Reserve a random seat of {price_message}?</b>'
    )

    if message != context.user_data[LAST_MESSAGE].text_html:
        context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    context.user_data[STATE] = VIEW_TRACK
    return VIEW_TRACK


async def show_reserved(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    is_refresh = False
    # is_cancel = False
    if re.compile(f'^{REFRESH_RESERVED_DATA}/{UUID_PATTERN}$').match(query.data):
        tracking_uuid = re.search(UUID_PATTERN, query.data).group(0)
        is_refresh = True
    elif re.compile(f'^{RESERVE_DATA}/{UUID_PATTERN}$').match(query.data):
        tracking_uuid = re.search(UUID_PATTERN, query.data).group(0)

        # context.user_data[TRACKING_LIST] = [
        #     t for t in context.user_data.get(TRACKING_LIST, []) if t.get(TRACKING_UUID) != uuid.UUID(tracking_uuid)
        # ]
        # job_removed = remove_job_if_exists(tracking_uuid, context)
        # logger.info(job_removed)
    else:
        return context.user_data.get(STATE)

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
        context.user_data.get(VOLATILE, {}).get(SEARCH_DATA),
        context.user_data.get(VOLATILE, {}).get(TRIP_DATA),
        session,
        context.user_data.get(TOKEN)
    )
    if not res.get('status'):
        context.user_data[TO_STRIKETHROUGH] = False
        context.user_data[TO_HIDE_KEYBOARD] = True
        context.user_data.get(VOLATILE, {}).pop(PARTIAL_CONTENT, None)
        await show_error_inline(
            context,
            res.get('error'),
            InlineKeyboardMarkup(build_tracked_actions_keyboard(tracking_uuid))
        )
        context.user_data[STATE] = VIEW_TRACK
        return VIEW_TRACK
    else:
        context.user_data[COOKIE] = session.cookies

    context.user_data.get(VOLATILE, {})[LAYOUT_DATA] = res.get(LAYOUT_DATA)
    context.user_data.get(VOLATILE, {})[PARTIAL_CONTENT] = res.get(PARTIAL_CONTENT)

    if not is_refresh:
        res = reserve_by_price(
            session,
            res.get('seats_data'),
            context.user_data.get(TRANSACTION, {}).get(PRICE),
            context.user_data.get(VOLATILE, {}).get(SEARCH_DATA),
            context.user_data.get(VOLATILE, {}).get(TRIP_DATA),
            context.user_data.get(VOLATILE, {}).get(LAYOUT_DATA),
            context.user_data.get(TOKEN)
        )
        if not res.get('status'):
            context.user_data[TO_STRIKETHROUGH] = False
            context.user_data[TO_HIDE_KEYBOARD] = True
            await show_error_inline(
                context,
                res.get('error'),
                InlineKeyboardMarkup(build_tracked_actions_keyboard(tracking_uuid))
            )
            context.user_data[STATE] = VIEW_TRACK
            return VIEW_TRACK
        else:
            context.user_data[COOKIE] = session.cookies

        context.user_data.get(VOLATILE, {})[BOOKING_DATA] = res.get(BOOKING_DATA)
        coach = res.get('CoachLabel')
        seat = res.get('SeatNo')
        price = res.get('Price')
        for index, t in enumerate(context.user_data.get(TRACKING_LIST, [])):
            if t.get(TRACKING_UUID) == uuid.UUID(tracking_uuid):
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

    t = next(tr for tr in context.user_data.get(TRACKING_LIST, []) if tr.get(TRACKING_UUID) == uuid.UUID(tracking_uuid))

    reply_markup = InlineKeyboardMarkup(build_reserved_actions_keyboard(tracking_uuid))
    message = (
        f'{get_tracking_content(
            context.user_data.get(TRANSACTION, {}),
            context.user_data.get(VOLATILE, {}),
            Title.RESERVED.value
        )}'
        '\n'
        f'<i>Refreshed at: {malaysia_now_datetime().strftime('%H:%M:%S')}</i>\n'
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

    context.user_data[STATE] = RESERVED
    return RESERVED
