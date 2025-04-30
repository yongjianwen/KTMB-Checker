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