import re

from telegram import InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import (
    ContextTypes
)

from utils.bot_helper import (
    strikethrough_last_message,
    enable_strikethrough, enable_hide_keyboard_only, disable_strikethrough,
    is_logged_in
)
from utils.constants import (
    EMAIL, PASSWORD,
    LAST_MESSAGE, STATE,
    PROFILES,
    TEMP
)
from utils.constants import (
    START,
    ADD_EMAIL, ADD_PASSWORD,
    PROFILE, SELECTED_PROFILE, CHANGE_PASSWORD,
    Title
)
from utils.keyboard_helper import (
    build_profiles_keyboard, build_profile_actions_keyboard,
)


async def manage_profiles(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is None:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )
        await strikethrough_last_message(context)
    else:
        await query.answer()

    enable_hide_keyboard_only(context.user_data)

    reply_markup = InlineKeyboardMarkup(
        build_profiles_keyboard(context.user_data.get(PROFILES, {}), f'{PROFILE}:', True)
    )
    message = '⬇️ Select a profile below to manage, or add a new profile' if context.user_data.get(PROFILES) \
        else '⬇️ Click below button to add a new profile'

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

    context.user_data[STATE] = PROFILE
    return PROFILE


async def add_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    enable_strikethrough(context.user_data)
    context.user_data[TEMP] = {}

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        (
            f'<b>{Title.ADD_PROFILE.value}</b>\n'
            '\n'
            'Enter your KTMB email'
        ),
        reply_markup=None,
        parse_mode='HTML'
    )

    context.user_data[STATE] = ADD_EMAIL
    return ADD_EMAIL


async def add_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text
    context.user_data.get(TEMP, {})[EMAIL] = email

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    enable_strikethrough(context.user_data)

    message = (
        f'<b>{Title.ADD_PROFILE.value}</b>\n'
        '\n'
        f'Email: <b>{context.user_data.get(TEMP, {}).get(EMAIL)}</b>\n'
        '\n'
    )
    if context.user_data.get(PROFILES, {}).get(email):
        message = message + '🔴 Email already exists\n\n🟢 Enter your new password to update the old one'
    else:
        message = message + 'Enter your password'

    context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
        message,
        reply_markup=None,
        parse_mode='HTML'
    )

    context.user_data[STATE] = ADD_PASSWORD
    return ADD_PASSWORD


async def added_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    password = update.message.text
    context.user_data.get(TEMP, {})[PASSWORD] = password

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    disable_strikethrough(context.user_data)

    email = context.user_data.get(TEMP, {}).get(EMAIL)
    title = Title.UPDATED_PROFILE.value if context.user_data.get(PROFILES, {}).get(email) else Title.ADDED_PROFILE.value

    if PROFILES not in context.user_data:
        context.user_data[PROFILES] = {}

    context.user_data.get(PROFILES, {})[email] = password
    context.user_data.pop(TEMP, None)

    message = (
        f'<b>{title}</b>\n'
        '\n'
        f'Email: <b>{email}</b>\n'
        # f'🔑 Password: <b><span class="tg-spoiler">🙈🙉🙊</span></b>\n'
        '\n'
    )
    if is_logged_in(context.user_data):
        message = message + 'You are logged in as:\n' + context.user_data.get(EMAIL)
    else:
        message = message + 'Do you wish to /login now?'

    context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
        message,
        reply_markup=None,
        parse_mode='HTML'
    )

    context.user_data[STATE] = START
    return START


async def selected_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    match = re.search(f'{PROFILE}:(.*)', query.data)
    if match:
        context.user_data[TEMP] = {}
        context.user_data.get(TEMP, {})[EMAIL] = match.group(1)
    else:
        return context.user_data.get(STATE)

    enable_strikethrough(context.user_data)

    reply_markup = InlineKeyboardMarkup(
        build_profile_actions_keyboard(context.user_data.get(TEMP, {}).get(EMAIL), f'{SELECTED_PROFILE}:', True)
    )

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        (
            f'<b>{Title.MANAGE_PROFILE.value}</b>\n'
            '\n'
            f'Email: <b>{context.user_data.get(TEMP, {}).get(EMAIL)}</b>\n'
            # f'🔑 Password: <b><span class="tg-spoiler">🙈🙉🙊</span></b>\n'
            '\n'
            '⬇️ Choose an action below'
        ),
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

    context.user_data[STATE] = SELECTED_PROFILE
    return SELECTED_PROFILE


async def change_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    enable_strikethrough(context.user_data)

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        (
            f'<b>{Title.MANAGE_PROFILE.value}</b>\n'
            '\n'
            f'Email: <b>{context.user_data.get(TEMP, {}).get(EMAIL)}</b>\n'
            # f'🔑 Password: <b><span class="tg-spoiler">🙈🙉🙊</span></b>\n'
            '\n'
            'Enter your new password'
        ),
        reply_markup=None,
        parse_mode='HTML'
    )

    context.user_data[STATE] = CHANGE_PASSWORD
    return CHANGE_PASSWORD


async def deleted_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    disable_strikethrough(context.user_data)

    email = context.user_data.get(TEMP, {}).get(EMAIL)

    context.user_data.get(PROFILES, {}).pop(email, None)
    context.user_data.pop(TEMP, None)

    context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
        (
            f'<b>{Title.DELETED_PROFILE.value}</b>\n'
            '\n'
            f'Email: <s><b>{email}</b></s>'
        ),
        reply_markup=None,
        parse_mode='HTML'
    )

    context.user_data[STATE] = START
    return START
