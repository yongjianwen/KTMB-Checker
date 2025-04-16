from datetime import timedelta, datetime

from telegram import InlineKeyboardButton

from ktmb import stations_data


def generate_state_keyboard(back=False):
    keyboard = []
    row = []

    for state in stations_data:
        button = InlineKeyboardButton(
            state['State'],
            callback_data=state['State']
        )

        if len(state['State']) < 10:
            row.append(button)
            if len(row) == 2:
                keyboard.append(row)
                row = []
        else:
            if row:  # Add any accumulated buttons first
                keyboard.append(row)
                row = []
            keyboard.append([button])  # Add current button as new row

    # Add any remaining buttons in temp_row
    if row:
        keyboard.append(row)

    if back:
        keyboard.append([
            InlineKeyboardButton('↩️ Back', callback_data='Back')
        ])

    return keyboard


def generate_station_keyboard(state_selected, back=False):
    keyboard = []
    row = []

    for station in next(state['Stations'] for state in stations_data if state['State'] == state_selected):
        button = InlineKeyboardButton(
            station['Description'],
            callback_data=station['Id']
        )

        if len(station['Description']) < 8:
            row.append(button)
            if len(row) == 2:
                keyboard.append(row)
                row = []
        else:
            if row:  # Add any accumulated buttons first
                keyboard.append(row)
                row = []
            keyboard.append([button])  # Add current button as new row

    # Add any remaining buttons in temp_row
    if row:
        keyboard.append(row)

    if back:
        keyboard.append([
            InlineKeyboardButton('↩️ Back', callback_data='Back')
        ])

    return keyboard


def generate_friday_keyboard(back=False):
    keyboard = []

    today = datetime.today()
    today_str = today.strftime('%Y-%m-%d')

    f1 = next_friday(today)
    f1_str = f1.strftime('%Y-%m-%d')

    f2 = next_friday(f1)
    f2_str = f2.strftime('%Y-%m-%d')

    f3 = next_friday(f2)
    f3_str = f3.strftime('%Y-%m-%d')

    if today.weekday() == 4:  # Friday
        keyboard.extend([
            [InlineKeyboardButton(f'Today {today_str}', callback_data=today_str)],
            [InlineKeyboardButton(f'Next Friday {f1_str}', callback_data=f1_str)],
            [InlineKeyboardButton(f'Next Next Friday {f2_str}', callback_data=f2_str)]
        ])
    elif today.weekday() == 5:  # Saturday
        keyboard.extend([
            [InlineKeyboardButton(f'Next Friday {f1_str}', callback_data=f1_str)],
            [InlineKeyboardButton(f'Next Next Friday {f2_str}', callback_data=f2_str)],
            [InlineKeyboardButton(f'Next Next Next Friday {f3_str}', callback_data=f3_str)]
        ])
    else:  # Sunday - Thursday
        keyboard.extend([
            [InlineKeyboardButton(f'This Friday: {f1_str}', callback_data=f1_str)],
            [InlineKeyboardButton(f'Next Friday: {f2_str}', callback_data=f2_str)],
            [InlineKeyboardButton(f'Next Next Friday: {f3_str}', callback_data=f3_str)]
        ])

    if back:
        keyboard.append([
            InlineKeyboardButton('↩️ Back', callback_data='Back')
        ])

    return keyboard


def next_friday(from_date):
    days_ahead = 4 - from_date.weekday()  # Friday is 4
    if days_ahead <= 0:  # Friday, Saturday, Sunday
        days_ahead += 7
    return from_date + timedelta(days=days_ahead)


def generate_tracking_keyboard(back=False):
    keyboard = [[
        InlineKeyboardButton('✅ Start Tracking!', callback_data='Start Tracking!')
    ]]

    if back:
        keyboard.append([
            InlineKeyboardButton('↩️ Back', callback_data='Back')
        ])

    return keyboard


def generate_reserve_keyboard():
    keyboard = [[
        InlineKeyboardButton('Reserve', callback_data='Reserve')
    ]]

    return keyboard
