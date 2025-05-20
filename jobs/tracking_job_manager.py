import asyncio
import json
import logging
from datetime import datetime, timedelta, time

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from telegram.constants import ChatAction

from services.ktmb import (
    get_stations,
    get_trips,
    login,
    logout
)
from utils.bot_helper import (
    strikethrough_last_message
)
from utils.constants import (
    COOKIE, TOKEN,
    EMAIL, PASSWORD,
    STATIONS_DATA,
    TRACKING_LIST,
    FROM_STATE_NAME, FROM_STATION_ID, FROM_STATION_NAME,
    TO_STATE_NAME, TO_STATION_ID, TO_STATION_NAME,
    DATE, DEPARTURE_TIME, ARRIVAL_TIME, PRICE,
    SEARCH_DATA, TRIPS_DATA, TRIP_DATA, PARTIAL_CONTENT,
    TRACKING_UUID,
    RESERVED_SEAT,
    SEATS_LEFT_BY_PRICES,
    LAST_REMINDED,
    INTERVALS_INDEX,
    IS_DANGEROUS,
    LAST_RUN, LAST_API_RUN
)
from utils.constants import (
    TRACKING_JOB_ID,
    TRIGGER_INTERVAL_IN_SECONDS, LOW_SEAT_COUNT,
    DEFAULT_TRIGGER_INTERVAL_IN_SECONDS
)
from utils.ktmb_helper import (
    get_station_by_id, get_seats_contents
)
from utils.message_helper import (
    get_tracking_content, get_seats_left_by_prices_content
)
from utils.utils import (
    malaysia_now_datetime, get_next_time_by_interval
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# scheduler = AsyncIOScheduler()
scheduler = BackgroundScheduler()


def start_tracking_job(context, chat_id):
    logger.info(
        f'>> {chat_id} -- start_date: {get_next_time_by_interval(context.bot_data.get(TRIGGER_INTERVAL_IN_SECONDS, DEFAULT_TRIGGER_INTERVAL_IN_SECONDS))}'
    )
    scheduler.add_job(
        sync_alarm_wrapper,
        trigger='interval',
        id=f'{TRACKING_JOB_ID}_{chat_id}',
        name=f'{TRACKING_JOB_ID}_{chat_id}',
        seconds=context.bot_data.get(TRIGGER_INTERVAL_IN_SECONDS, DEFAULT_TRIGGER_INTERVAL_IN_SECONDS),
        start_date=get_next_time_by_interval(
            context.bot_data.get(TRIGGER_INTERVAL_IN_SECONDS, DEFAULT_TRIGGER_INTERVAL_IN_SECONDS)
        ),
        args=[],
        kwargs={
            'context': context,
            'chat_id': chat_id
        }
    )
    if not scheduler.running:
        scheduler.start()


def sync_alarm_wrapper(*args, **kwargs):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(alarm(*args, **kwargs))
    finally:
        pass
        # logger.info('>> Loop closed!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        # loop.close()


async def alarm(context, chat_id) -> None:
    # load_dotenv(override=True)
    # trigger_interval_in_seconds = int(os.getenv('TRIGGER_INTERVAL_IN_SECONDS'))
    # low_seat_count = int(os.getenv('LOW_SEAT_COUNT'))
    trigger_interval_in_seconds = context.bot_data.get(TRIGGER_INTERVAL_IN_SECONDS, 30)
    low_seat_count = context.bot_data.get(LOW_SEAT_COUNT, 20)
    intervals = [
        trigger_interval_in_seconds,  # 5 minutes
        trigger_interval_in_seconds,
        trigger_interval_in_seconds * 2,  # 10 minutes
        trigger_interval_in_seconds * 2,
        trigger_interval_in_seconds * 4,  # 20 minutes
        trigger_interval_in_seconds * 4,
        trigger_interval_in_seconds * 6,  # 30 minutes
        trigger_interval_in_seconds * 6,
        trigger_interval_in_seconds * 8,  # 40 minutes
        trigger_interval_in_seconds * 8,
        trigger_interval_in_seconds * 10,  # 50 minutes
        trigger_interval_in_seconds * 10,
        trigger_interval_in_seconds * 12,  # 60 minutes
        trigger_interval_in_seconds * 12,
        # trigger_interval_in_seconds * 16,  # 8 minutes
        # trigger_interval_in_seconds * 16,
        # trigger_interval_in_seconds * 32,  # 16 minutes
        # trigger_interval_in_seconds * 32,
        # trigger_interval_in_seconds * 64,  # 32 minutes
        # trigger_interval_in_seconds * 64
    ]

    logger.info(f'>> {chat_id} -- trigger_interval_in_seconds: {trigger_interval_in_seconds}')
    logger.info(f'>> {chat_id} -- low_seat_count: {low_seat_count}')

    if len(context.user_data.get(TRACKING_LIST, [])) == 0:
        logger.info(f'>> {chat_id} -- Job skipped - no tracking found')
        return

    now_datetime = malaysia_now_datetime()
    now_time = now_datetime.time()
    start_time = time(hour=23, minute=0)
    end_time = time(hour=7, minute=0)
    if (start_time <= now_time) or (now_time <= end_time):
        logger.info(
            f'>> {chat_id} -- Job skipped - time is between {start_time.hour:02d}:{start_time.minute:02d} and {end_time.hour:02d}:{end_time.minute:02d} inclusive'
        )
        return

    session = requests.Session()
    session.cookies.update(context.user_data.get(COOKIE))

    res = get_stations(session)
    if not res.get('status'):
        logger.info(f'>> {chat_id} -- Get stations error')
        return
    else:
        context.user_data[COOKIE] = session.cookies

    stations_data = res.get(STATIONS_DATA)

    for index, t in enumerate(context.user_data.get(TRACKING_LIST, [])):
        t[LAST_RUN] = malaysia_now_datetime()

        logger.info(f'>> {chat_id} -- Tracking {index}')
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
        prev_seats_left_by_prices = t.get(SEATS_LEFT_BY_PRICES)
        last_reminded = t.get(LAST_REMINDED)
        intervals_index = t.get(INTERVALS_INDEX, 0)
        is_dangerous = t.get(IS_DANGEROUS, False)

        year, month, day = date.split('-')
        interval = intervals[intervals_index]
        next_remind_time = (last_reminded + timedelta(seconds=interval)).replace(microsecond=0)

        logger.info(
            f'>> {chat_id} -- Last reminded: {last_reminded}, Intervals index: {intervals_index}, Interval: {interval}, Next remind: {next_remind_time}')
        logger.info(f'>> {chat_id} -- Prev seats left by prices: {prev_seats_left_by_prices}')

        if next_remind_time > malaysia_now_datetime():
            logger.info(
                f'>> {chat_id} -- Job skipped - have not reached next interval at {next_remind_time.strftime('%H:%M:%S')}')
            continue
        # else:
        #     t[LAST_REMINDED] = malaysia_now_datetime()
        #     t[INTERVALS_INDEX] = min(intervals_index + 1, len(INTERVALS) - 1)
        #     return

        res = get_trips(
            session,
            datetime(int(year), int(month), int(day)),
            get_station_by_id(stations_data, from_station_id),
            get_station_by_id(stations_data, to_station_id),
            context.user_data.get(TOKEN)
        )
        if not res.get('status'):
            logger.info(f'>> {chat_id} -- Get trips error')
            logger.info(f'>> {chat_id} -- Retrying...')
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
                    return
                else:
                    context.user_data[COOKIE] = session.cookies
                    logger.info(f'>> {chat_id} -- Retry successful')
            else:
                return
        else:
            context.user_data[COOKIE] = session.cookies

        t[LAST_API_RUN] = malaysia_now_datetime()

        search_data = res.get(SEARCH_DATA)
        trips_data = json.loads(json.dumps(res.get(TRIPS_DATA)))

        if not trips_data:
            logger.info(f'>> {chat_id} -- Job skipped - no trip found')
            continue

        trip = next(t for t in trips_data if t.get(DEPARTURE_TIME) == departure_time)
        trip_data = trip.get(TRIP_DATA)

        res = await get_seats_contents(
            search_data,
            trip_data,
            session,
            context.user_data.get(TOKEN)
        )
        if not res.get('status'):
            logger.info(f'>> {chat_id} -- Get seats contents error')
            return
        else:
            context.user_data[COOKIE] = session.cookies

        partial_content = res.get(PARTIAL_CONTENT)
        new_seats_left_by_prices = res.get(SEATS_LEFT_BY_PRICES)

        logger.info(f'>> {chat_id} -- New seats left by prices: {new_seats_left_by_prices}')

        if price == -1:
            seats_left_by_tracking_price = sum(new_seats_left_by_prices.values())
        else:
            seats_left_by_tracking_price = new_seats_left_by_prices.get(str(price))
        t[IS_DANGEROUS] = (seats_left_by_tracking_price or 0) <= low_seat_count

        logger.info(f'>> {chat_id} -- Is dangerous: {t.get(IS_DANGEROUS)}')

        to_remind = False
        reason = ''
        # selected a price and initial was 0
        if price != -1 and str(price) not in prev_seats_left_by_prices:
            # logger.info(f'>> {chat_id} -- A')
            if str(price) in new_seats_left_by_prices:
                # logger.info(f'>> {chat_id} -- B')
                to_remind = True
                reason = '‼️ New seat(s) has appeared!'
        # selected any price and initial was 0
        elif price == -1 and not prev_seats_left_by_prices:
            # logger.info(f'>> {chat_id} -- C')
            if new_seats_left_by_prices:
                # logger.info(f'>> {chat_id} -- D')
                to_remind = True
                reason = '‼️ New seat(s) has appeared!'
        else:
            logger.info(f'>> {chat_id} -- E')
            # selected a price/any price and initial was not 0, but now sold out
            if not new_seats_left_by_prices:
                logger.info(f'>> {chat_id} -- J')
                to_remind = True
                reason = '‼️ Tickets are sold out!'
            else:
                # # selected a price and initial was not 0
                # for p, s in new_seats_left_by_prices.items():
                #     logger.info(f'>> {chat_id} -- F')
                #     if p == str(price) and s < prev_seats_left_by_prices.get(p):
                #         logger.info(f'>> {chat_id} -- G')
                #         to_remind = True
                #         reason = '‼️ Tickets are selling out!'
                #         break
                # # selected any price and initial was not 0
                # for p, s in new_seats_left_by_prices.items():
                #     logger.info(f'>> {chat_id} -- H')
                #     if price == -1 and s < prev_seats_left_by_prices.get(p, 0):
                #         logger.info(f'>> {chat_id} -- I')
                #         to_remind = True
                #         reason = '‼️ Tickets are selling out!'
                #         break
                if t.get(IS_DANGEROUS):
                    to_remind = True
                    reason = f'‼️ Less than {low_seat_count} tickets!'

        logger.info(f'>> {chat_id} -- To remind: {to_remind}')

        if not to_remind or (not is_dangerous and t.get(IS_DANGEROUS)):  # previously not dangerous, but now dangerous
            t[INTERVALS_INDEX] = 0

        intervals_index = t.get(INTERVALS_INDEX, 0)
        interval = intervals[intervals_index]

        logger.info(f'>> {chat_id} -- Update: {new_seats_left_by_prices}')
        # t[SEATS_LEFT_BY_PRICES] = {**new_seats_left_by_prices}

        if to_remind and last_reminded + timedelta(seconds=interval) < malaysia_now_datetime():
            t[LAST_REMINDED] = now_datetime.replace(microsecond=0)
            t[INTERVALS_INDEX] = min(intervals_index + 1, len(intervals) - 1)
            t[SEATS_LEFT_BY_PRICES] = {**new_seats_left_by_prices}

            await context.bot.send_chat_action(
                chat_id=chat_id,
                action=ChatAction.TYPING
            )
            await strikethrough_last_message(context)

            if reserved_seat is None:
                price_message = 'any price' if price == -1 else f'RM {price}'
                await context.bot.send_message(
                    chat_id,
                    text=(
                        f'{get_tracking_content(
                            t,
                            {PARTIAL_CONTENT: partial_content},
                            reason
                        )}'
                        '\n'
                        f'{get_seats_left_by_prices_content(prev_seats_left_by_prices, new_seats_left_by_prices)}'
                        '\n'
                        f'<i>Refreshed at: {malaysia_now_datetime().strftime('%H:%M:%S')}</i>\n'
                        '\n'
                        f'Price: <b>{price_message}</b>'
                        # f'<b>Reserve a random seat of {price_message}?</b>'
                    ),
                    reply_markup=None,
                    parse_mode='HTML'
                )
            else:
                await context.bot.send_message(
                    chat_id,
                    text=(
                        f'{get_tracking_content(
                            {**t, PARTIAL_CONTENT: partial_content},
                            {},
                            'Alarm'
                        )}'
                        '\n'
                        f'{get_seats_left_by_prices_content(prev_seats_left_by_prices, new_seats_left_by_prices)}'
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


def check_active_jobs(chat_id):
    for job in scheduler.get_jobs():
        if job.next_run_time is not None and job.id == f'{TRACKING_JOB_ID}_{chat_id}':
            return True
    return False


def set_trigger_interval_in_seconds(interval_in_seconds):
    pass
    # global trigger_interval_in_seconds
    # trigger_interval_in_seconds = interval_in_seconds
