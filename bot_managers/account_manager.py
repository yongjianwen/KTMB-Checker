import re

import requests
from telegram import InlineKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.constants import ChatAction
from telegram.ext import (
    ContextTypes
)

from services.ktmb import (
    login, logout
)
from utils.bot_helper import (
    strikethrough_last_message,
    enable_hide_keyboard_only, disable_strikethrough,
    is_logged_in
)
from utils.constants import (
    COOKIE, TOKEN, EMAIL, PASSWORD, LAST_MESSAGE, STATE, PROFILES, TRANSACTION
)
from utils.constants import (
    START,
    SET_EMAIL, SET_PASSWORD,
    CLEAR
)
from utils.keyboard_helper import (
    build_bottom_reply_markup,
    build_profiles_keyboard,
    build_clear_actions_keyboard
)


async def login_or_logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_logged_in(context.user_data):
        return await set_email(update, context)
    else:
        return await logout_ktmb(update, context)


async def set_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await strikethrough_last_message(context)

    enable_hide_keyboard_only(context.user_data)

    if is_logged_in(context.user_data):
        context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
            'Already logged in as:\n' + context.user_data.get(EMAIL) + '\n\nDo you want to /logout?',
            reply_markup=None
        )
        context.user_data[STATE] = START
        return START
    else:
        reply_markup = InlineKeyboardMarkup(
            build_profiles_keyboard(context.user_data.get(PROFILES, {}), f'{SET_EMAIL}:')
        )
        context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
            '⬇️ Select a profile below to log in, or enter your KTMB email' if context.user_data.get(PROFILES, {})
            else 'Enter your KTMB email',
            reply_markup=reply_markup
        )
        context.user_data[STATE] = SET_EMAIL
        return SET_EMAIL


async def set_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[EMAIL] = update.message.text

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await strikethrough_last_message(context)

    disable_strikethrough(context.user_data)

    context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
        'Enter your password',
        reply_markup=None
    )

    context.user_data[STATE] = SET_PASSWORD
    return SET_PASSWORD


async def login_ktmb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is None:
        email = context.user_data.get(EMAIL)
        password = update.message.text
    else:
        await query.answer()
        match = re.search(f'{SET_EMAIL}:(.*)', query.data)
        if match:
            email = match.group(1)
            context.user_data[EMAIL] = email
            password = context.user_data.get(PROFILES, {}).get(email)
        else:
            return context.user_data.get(STATE)

    context.user_data[PASSWORD] = password

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await strikethrough_last_message(context)

    disable_strikethrough(context.user_data)

    session = requests.Session()
    res = login(session, email, password)

    if res.get('status'):
        context.user_data[COOKIE] = session.cookies
        context.user_data[TOKEN] = res.get(TOKEN)
        message = f'Logged in as {email} successfully'
        if password != context.user_data.get(PROFILES, {}).get(email):
            context.user_data.get(PROFILES, {})[email] = password
            message = message + '\n\n✅ Profile password updated'
        context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
            message,
            reply_markup=build_bottom_reply_markup()
        )
        context.user_data[STATE] = START
        return START
    else:
        context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
            (
                f'Could not log in as: {email}\n'
                '\n'
                'Re-enter your password, or /login again'
            ),
            reply_markup=None
        )
        context.user_data[STATE] = SET_PASSWORD
        return SET_PASSWORD


async def logout_ktmb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await strikethrough_last_message(context)

    disable_strikethrough(context.user_data)

    session = requests.Session()
    if COOKIE in context.user_data:
        session.cookies.update(context.user_data.get(COOKIE))

        temp_email = context.user_data.get(EMAIL)

        clear_session_data(context)
        context.user_data.pop(TRANSACTION, None)

        res = logout(session)

        context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
            f'Logged out {temp_email}\n\nDo you wish to /login again?' if res.get('status') else res.get('error'),
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        clear_session_data(context)
        context.user_data.pop(TRANSACTION, None)

        context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
            'Already logged out\n\nDo you wish to /login again?',
            reply_markup=ReplyKeyboardRemove()
        )

    context.user_data[STATE] = START
    return START


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await strikethrough_last_message(context)

    enable_hide_keyboard_only(context.user_data)

    reply_markup = InlineKeyboardMarkup(build_clear_actions_keyboard(f'{CLEAR}:'))

    context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
        'Are you sure to clear all user data?',
        reply_markup=reply_markup
    )

    context.user_data[STATE] = CLEAR
    return CLEAR


async def rejected_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await strikethrough_last_message(context)

    disable_strikethrough(context.user_data)

    context.user_data[STATE] = START
    return START


async def confirmed_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    await strikethrough_last_message(context)

    disable_strikethrough(context.user_data)

    session = requests.Session()
    if COOKIE in context.user_data:
        session.cookies.update(context.user_data.get(COOKIE))

        res = logout(session)

        temp_email = context.user_data.get(EMAIL)

        context.user_data[LAST_MESSAGE] = await update.effective_message.edit_text(
            f'Logged out {temp_email}\n\nDo you wish to /login again?' if res.get('status') else res.get('error'),
            reply_markup=None
        )

    context.user_data.clear()
    for job in context.job_queue.jobs():
        job.schedule_removal()

    context.user_data[LAST_MESSAGE] = await update.effective_message.reply_text(
        'Cleared all user data',
        reply_markup=ReplyKeyboardRemove()
    )

    context.user_data[STATE] = START
    return START


def clear_session_data(context, auto_logout=False):
    if not auto_logout:
        context.user_data.pop(EMAIL, None)
        context.user_data.pop(PASSWORD, None)
    context.user_data.pop(COOKIE, None)
    context.user_data.pop(TOKEN, None)
