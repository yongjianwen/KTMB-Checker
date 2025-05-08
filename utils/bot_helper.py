import logging

from .constants import (
    COOKIE, LAST_MESSAGE, TO_STRIKETHROUGH, TO_HIDE_KEYBOARD, TRANSACTION, VOLATILE
)
from .message_helper import get_tracking_content

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
                if last_message != context.user_data.get(LAST_MESSAGE).text_html:
                    context.user_data[LAST_MESSAGE] = await context.bot.edit_message_text(
                        chat_id=last_message.chat_id,
                        message_id=last_message.message_id,
                        text=f'<s>{last_message.text_html}</s>\n\n<b><i>Transaction cancelled</i></b>',
                        reply_markup=None,
                        parse_mode='HTML'
                    )
            elif context.user_data.get(TO_HIDE_KEYBOARD):
                context.user_data[LAST_MESSAGE] = await context.bot.edit_message_reply_markup(
                    chat_id=last_message.chat_id,
                    message_id=last_message.message_id,
                    reply_markup=None
                )
        except Exception as e:
            logger.info(e)


async def show_error_inline(context, error_message, reply_markup=None):
    last_message = context.user_data.get(LAST_MESSAGE)
    if last_message:
        message = (
            f'{get_tracking_content(
                context.user_data.get(TRANSACTION, {}),
                context.user_data.get(VOLATILE, {}),
                'Don\'t know what title'
            )}'
            '\n'
            f'❌ We encountered an error. Please try again later.\n\n👾 For dev: {error_message}'
        )
        if message != last_message.text_html:
            context.user_data[LAST_MESSAGE] = await context.bot.edit_message_text(
                chat_id=last_message.chat_id,
                message_id=last_message.message_id,
                text=message,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )


async def show_error_reply(update, context, error_message):
    disable_strikethrough(context.user_data)
    context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
        f'❌ We encountered an error. Please try again later.\n\n👾 For dev: {error_message}',
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


def is_logged_in(data):
    logged_in = False
    if data.get(COOKIE):
        logged_in = True
    return logged_in
