import logging
import os

from telegram import InlineKeyboardMarkup, Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler, PicklePersistence, MessageHandler, filters,
)

from ktmb import session, get_station_by_id
from utils import generate_state_keyboard, generate_station_keyboard, generate_friday_keyboard, \
    generate_tracking_keyboard, generate_reserve_keyboard

BOT_TOKEN = os.getenv('BOT_TOKEN')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger('httpx').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Stages
START, SET_FROM_STATE, SET_FROM_STATION, SET_TO_STATE, SET_TO_STATION, SET_DATE, SHOW_DATA = range(7)
# Callback data
TRACK_NEW_TRAIN, VIEW_TRACKING = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send message on `/start`."""
    # Get user that sent /start and log his name
    user = update.message.from_user
    logger.info('User %s started the conversation.', user.first_name)

    context.user_data['to_deactivate'] = False

    keyboard = [
        ['🚂 Track New Train', '👀 View Tracking']
    ]
    # reply_markup = InlineKeyboardMarkup(keyboard)
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
    # Send message with text and appended InlineKeyboard
    context.user_data['last_message'] = await update.message.reply_text(
        'Hello there 👋 I am KTMB Bot 🤖\n'
        '\n'
        'You can use me to track train 🚂 seat availability', reply_markup=reply_markup)
    # Tell ConversationHandler that we're in state `START` now
    return START


async def set_from_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data['last_message'] and context.user_data.get('to_deactivate'):
        last_message = context.user_data['last_message']
        await context.bot.edit_message_text(chat_id=last_message.chat_id, message_id=last_message.message_id,
                                            text=f'<s>{last_message.text_html}</s>',
                                            reply_markup=None, parse_mode='HTML')
        context.user_data['to_deactivate'] = False

    context.user_data['to_deactivate'] = True

    reply_markup = InlineKeyboardMarkup(generate_state_keyboard())
    message = ('<b>📍 Creating new tracking...</b>\n'
               '\n'
               'Where are you departing from?')

    if update.message:
        context.user_data['last_message'] = await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        context.user_data['last_message'] = await update.effective_message.edit_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    return SET_FROM_STATE


async def set_from_station(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data != 'Back':
        context.user_data['from_state'] = query.data

    reply_markup = InlineKeyboardMarkup(generate_station_keyboard(context.user_data['from_state'], True))
    message = ('<b>📍 Creating new tracking...</b>\n'
               '\n'
               f'Departure: <b>{context.user_data['from_state']}</b>')

    # await query.edit_message_text(
    #     message,
    #     reply_markup=reply_markup,
    #     parse_mode='HTML'
    # )
    context.user_data['last_message'] = await update.effective_message.edit_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    return SET_FROM_STATION


async def set_to_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data != 'Back':
        context.user_data['from_station'] = query.data

    reply_markup = InlineKeyboardMarkup(generate_state_keyboard(True))
    message = ('<b>📍 Creating new tracking...</b>\n'
               '\n'
               f'Departure: <b>{get_station_by_id(context.user_data['from_station'])['Description']}, {context.user_data['from_state']}</b>\n'
               '\n'
               'Where are you going to?')

    context.user_data['last_message'] = await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    return SET_TO_STATE


async def set_to_station(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data != 'Back':
        context.user_data['to_state'] = query.data

    keyboard = generate_station_keyboard(context.user_data['to_state'], True)
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = ('<b>📍 Creating new tracking...</b>\n'
               '\n'
               f'Departure: <b>{get_station_by_id(context.user_data['from_station'])['Description']}, {context.user_data['from_state']}</b>\n'
               f'Destination: <b>{context.user_data['to_state']}</b>')

    context.user_data['last_message'] = await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    return SET_TO_STATION


async def set_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data != 'Back':
        context.user_data['to_station'] = query.data

    keyboard = generate_friday_keyboard(True)
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = ('<b>📍 Creating new tracking...</b>\n'
               '\n'
               f'Departure: <b>{get_station_by_id(context.user_data['from_station'])['Description']}, {context.user_data['from_state']}</b>\n'
               f'Destination: <b>{get_station_by_id(context.user_data['to_station'])['Description']}, {context.user_data['to_state']}</b>\n'
               '\n'
               'What date? (YYYY-MM-DD, e.g. 2025-01-01)')

    context.user_data['last_message'] = await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    return SET_DATE


async def show_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data['date'] = query.data

    keyboard = generate_tracking_keyboard(True)
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = ('<b>📍 Creating new tracking...</b>\n'
               '\n'
               f'Departure: <b>{get_station_by_id(context.user_data['from_station'])['Description']}, {context.user_data['from_state']}</b>\n'
               f'Destination: <b>{get_station_by_id(context.user_data['to_station'])['Description']}, {context.user_data['to_state']}</b>\n'
               f'Date: <b>{context.user_data['date']}</b>\n'
               '\n'
               # f'{ktmb}\n'
               '\n'
               '<b>Confirm to track this train?</b>\n'
               '\n'
               'You will be notified when:\n'
               '😱 Tickets are rapidly vanishing, or\n'
               '😁 A seat/coach suddenly becomes available')

    context.user_data['last_message'] = await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    return SHOW_DATA


async def add_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data['tracking_list'] = context.user_data.get('tracking_list', []).append(
        {
            'from_state': context.user_data['from_state'],
            'from_station': context.user_data['from_station'],
            'to_state': context.user_data['to_state'],
            'to_station': context.user_data['to_station'],
            'date': context.user_data['date'],
        }
    )

    keyboard = generate_reserve_keyboard()
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = ('<b>✅ New tracking added!</b>\n'
               '\n'
               f'Departure: <b>{get_station_by_id(context.user_data['from_station'])['Description']}, {context.user_data['from_state']}</b>\n'
               f'Destination: <b>{get_station_by_id(context.user_data['to_station'])['Description']}, {context.user_data['to_state']}</b>\n'
               f'Date: <b>{context.user_data['date']}</b>\n'
               '\n'
               # f'{ktmb}\n'
               '\n'
               '<b>Reserve a seat?</b>')

    context.user_data['last_message'] = await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
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
                MessageHandler(filters.Regex(f'^(🚂 Track New Train|👀 View Tracking)$'), set_from_state)
            ],
            SET_FROM_STATE: [
                CallbackQueryHandler(set_from_station),
                MessageHandler(filters.Regex(f'^(🚂 Track New Train|👀 View Tracking)$'), set_from_state)
            ],
            SET_FROM_STATION: [
                CallbackQueryHandler(set_from_state, pattern='^Back$'),
                CallbackQueryHandler(set_to_state),
                MessageHandler(filters.Regex(f'^(🚂 Track New Train|👀 View Tracking)$'), set_from_state)
            ],
            SET_TO_STATE: [
                CallbackQueryHandler(set_from_station, pattern='^Back$'),
                CallbackQueryHandler(set_to_station),
                MessageHandler(filters.Regex(f'^(🚂 Track New Train|👀 View Tracking)$'), set_from_state)
            ],
            SET_TO_STATION: {
                CallbackQueryHandler(set_to_state, pattern='^Back$'),
                CallbackQueryHandler(set_date),
                MessageHandler(filters.Regex(f'^(🚂 Track New Train|👀 View Tracking)$'), set_from_state)
            },
            SET_DATE: [
                CallbackQueryHandler(set_to_station, pattern='^Back$'),
                CallbackQueryHandler(show_data),
                MessageHandler(filters.Regex(f'^(🚂 Track New Train|👀 View Tracking)$'), set_from_state)
            ],
            SHOW_DATA: [
                CallbackQueryHandler(set_date, pattern='^Back$'),
                CallbackQueryHandler(add_tracking, pattern='^Start Tracking!$'),
                MessageHandler(filters.Regex(f'^(🚂 Track New Train|👀 View Tracking)$'), set_from_state)
            ]
        },
        fallbacks=[CommandHandler("start", start)],
        name='ktmb_conversation',
        persistent=True
    )

    # Add ConversationHandler to application that will be used for handling updates
    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
