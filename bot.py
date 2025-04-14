import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler, PicklePersistence, MessageHandler, filters,
)

from config import bot_token
import ktmb

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger('httpx').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Stages
START, SET_FROM, SET_TO, SET_DATE = range(4)
# Callback data
TRACK_NEW_TRAIN, VIEW_TRACKING = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send message on `/start`."""
    # Get user that sent /start and log his name
    user = update.message.from_user
    logger.info('User %s started the conversation.', user.first_name)
    # Build InlineKeyboard where each button has a displayed text
    # and a string as callback_data
    # The keyboard is a list of button rows, where each row is in turn
    # a list (hence `[[...]]`).
    # keyboard = [
    #     [
    #         InlineKeyboardButton('Track New Train', callback_data=TRACK_NEW_TRAIN),
    #         InlineKeyboardButton('View Tracking', callback_data=VIEW_TRACKING),
    #     ]
    # ]
    keyboard = [
        ['Track New Train', 'View Tracking']
    ]
    # reply_markup = InlineKeyboardMarkup(keyboard)
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    # Send message with text and appended InlineKeyboard
    await update.message.reply_text('What do you want to do?', reply_markup=reply_markup)
    # Tell ConversationHandler that we're in state `FIRST` now
    return START


async def set_from(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message
    # test = await update.message.reply_text(
    #     "Ok, track new train",
    #     reply_markup=ReplyKeyboardRemove(),  # Hides the reply keyboard
    # )
    keyboard = [
        [
            InlineKeyboardButton('JB Sentral', callback_data='JB Sentral1')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("OK, where do you start?", reply_markup=reply_markup)
    # await query.edit_message_text("OK, where do you start?", reply_markup=reply_markup)
    # await context.bot.edit_message_text(
    #     chat_id=update.effective_chat.id,
    #     message_id=test.message_id,
    #     text="Edited text!",
    #     reply_markup=InlineKeyboardMarkup(keyboard)
    # )
    return SET_FROM


async def set_to(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['from'] = query.data
    keyboard = [
        [
            InlineKeyboardButton('Bahau', callback_data='Bahau')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = f'From: {context.user_data['from']}'
    await query.edit_message_text(message, reply_markup=reply_markup)
    return SET_TO


async def set_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['to'] = query.data
    keyboard = [
        [
            InlineKeyboardButton('This Friday', callback_data='1'),
            InlineKeyboardButton('Next Friday', callback_data='2'),
            InlineKeyboardButton('Next Friday', callback_data='3')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = f'From: {context.user_data['from']}\nTo: {context.user_data['to']}'
    await query.edit_message_text(message, reply_markup=reply_markup)
    return SET_DATE


async def show_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the gathered info."""
    query = update.callback_query
    await query.answer()
    # res = await ktmb.ktmb()
    context.user_data['date'] = query.data
    message = (f'From: {context.user_data['from']}\n'
               f'To: {context.user_data['to']}\n'
               f'Date: {context.user_data['date']}\n'
               f'\n'
               f'{ktmb.ktmb()}')
    await update.callback_query.edit_message_text(message)


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    persistence = PicklePersistence(filepath="ktmb_conversation_data")
    application = Application.builder().token(bot_token).persistence(
        persistence).build()

    # Setup conversation handler with the states FIRST and SECOND
    # Use the pattern parameter to pass CallbackQueries with specific
    # data pattern to the corresponding handlers.
    # ^ means "start of line/string"
    # $ means "end of line/string"
    # So ^ABC$ will only allow 'ABC'
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START: [
                # CallbackQueryHandler(set_from, pattern=f'^{TRACK_NEW_TRAIN}$'),
                # CallbackQueryHandler(start, pattern=f'^{VIEW_TRACKING}$')
                MessageHandler(filters.Regex(f'^(Track New Train|View Tracking)$'), set_from)
            ],
            SET_FROM: [
                CallbackQueryHandler(set_to)
            ],
            SET_TO: [
                CallbackQueryHandler(set_date)
            ],
            SET_DATE: [
                CallbackQueryHandler(show_data)
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
