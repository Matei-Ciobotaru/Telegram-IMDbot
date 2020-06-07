#!/opt/Telegram-IMDbot/venv/bin/python3

"""

This is a Telegram bot that enables users to query IMDb.com for
a given title and set an alert for the respective title based on
its air date.

Author: Matei Ciobotaru

"""

import logging
from uuid import uuid4
from datetime import datetime
from telegram import InlineQueryResultArticle, ParseMode, \
     InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, \
     CallbackQueryHandler, ChosenInlineResultHandler, MessageHandler, Filters
from telegram.ext.dispatcher import run_async
from utils import movie


# Global vars
TOKEN = 'YOUR_BOT_TOKEN_HERE'
DATABASE = '/opt/Telegram-IMDbot/database/imdbot_db.sqlite3'
LOG_FILE = '/var/log/imdbot.log'
JOB_TIME = (9, 30) # time at which notifications are sent (UTC)


# Setup log file and rotation handler
LOG_ROTATE = logging.handlers.RotatingFileHandler(LOG_FILE, mode='a',
                                                  maxBytes=5242880,
                                                  backupCount=3,
                                                  delay=False)

logging.basicConfig(format='%(asctime)s - %(name)s - ' \
                           '%(levelname)s - %(message)s',
                    level=logging.INFO,
                    handlers=[LOG_ROTATE])

# Disable info level logging from below module as it spams
logging.getLogger('imdb.parser.http.piculet').setLevel(logging.ERROR)

LOG = logging.getLogger(__name__)


def notify_users(context):
    """
    Notify users upon title release
    """

    alert = movie.Alert(DATABASE)
    results = alert.notify()
    for result in results:
        user_id, message = result[0], result[1]
        context.bot.send_message(chat_id=user_id,
                                 text=message,
                                 parse_mode=ParseMode.HTML)


def result_id(title_id):
    """
    Generate UUID containig IMDb title ID
    """

    uuid4_str = str(uuid4())
    my_uuid = uuid4_str + '-' + str(title_id)
    return my_uuid


@run_async
def help_cmd(update, context):
    """
    Reply with help message when the command /help is issued.
    """

    bot_name = context.bot.getMe().username
    update.message.reply_text(text='Search for a title by typing @{0} "movie name", '
                                   'pick a result from the list and set an alert to '
                                   'receive a notification when the movie or series '
                                   'episode is out!\n\nType /alerts to view your act'
                                   'ive alerts.'.format(bot_name))


@run_async
def alerts_cmd(update, context):
    """
    Reply with list of enabled alerts when the command /alerts is issued
    """

    user_id = update.message.from_user.id
    alert = movie.Alert(DATABASE)
    message = alert.title_name(user_id)
    update.message.reply_html(message)


@run_async
def unknown_cmd(update, context):
    """
    Unsupported command message handler
    """

    chatid = update.effective_chat.id
    is_bot = update.effective_user.is_bot
    if not is_bot:
        context.bot.send_message(chat_id=chatid, text='Unrecognized command, ' \
                                                      'type /help or /alerts')


@run_async
def chosen_result(update, context):
    """
    Get chosen inline result
    """

    result = update.chosen_inline_result
    resultid = result.result_id
    title_id = resultid.split('-')[-1]
    user_id = result.from_user.id
    # Store chosen result's title_id in context
    context.user_data[user_id] = title_id


def imdb_url_button(title_id, message):
    """
    After chosing enable/disable alert create IMDb URL button
    """

    imdb_url = 'https://www.imdb.com/title/tt' + str(title_id)
    message = str(message) + ' (IMDb link)'
    keyboard = [[InlineKeyboardButton(text=str(message),
                                      url=imdb_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


@run_async
def enable_alert(update, context):
    """
    Enable Alert for chosen inline result.
    """

    query = update.callback_query
    query.answer(text='Searching release date...')
    # Get user info
    user = ['id', 'first_name', 'last_name', 'username']
    user_info = [query.from_user[i] for i in user if query.from_user[i]]
    user_name = ' '.join(user_info[1:])
    # Retrieve chosen title
    title_id = context.user_data[user_info[0]]
    # Remove buttons and enable alert
    query.edit_message_reply_markup(reply_markup=None)
    alert = movie.Alert(DATABASE)
    result = alert.enable(user_info[0], user_name, title_id)
    # Respond with IMDb link button
    new_reply_markup = imdb_url_button(title_id, result)
    query.edit_message_reply_markup(reply_markup=new_reply_markup)


@run_async
def disable_alert(update, context):
    """
    Disable alert for chosen inline result.
    """

    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    title_id = context.user_data[user_id]
    # disable alert
    alert = movie.Alert(DATABASE)
    result = alert.disable(user_id, title_id)
    # send response as button
    new_reply_markup = imdb_url_button(title_id, result)
    query.edit_message_reply_markup(reply_markup=new_reply_markup)


@run_async
def dismiss(update, context):
    """
    Dismiss chosen inline result
    """

    query = update.callback_query
    query.answer()
    query.edit_message_reply_markup(reply_markup=None)


def create_reply_markup(title, current_year, user_titles):
    """
    Create reply markup for result based on title and user alerts
    """

    keyboard = [[InlineKeyboardButton("Enable alert",
                                      callback_data=str(enable_alert)),
                 InlineKeyboardButton("Disable alert",
                                      callback_data=str(disable_alert)),
                 InlineKeyboardButton("Dismiss",
                                      callback_data=str(dismiss))]]
    # check if series has ended
    if 'series' in title['kind']:
        if title['end_year']:
            message = 'Series ended in {0}'.format(title['end_year'])
            reply_markup = imdb_url_button(title['id'], message)
            return reply_markup
    # check if movie was released
    elif title['year']:
        if current_year > title['year']:
            message = 'Movie released in {0}'.format(title['year'])
            reply_markup = imdb_url_button(title['id'], message)
            return reply_markup

    # remove enable/disable button based on user's existing alerts
    if str(title['id']) in user_titles:
        del keyboard[0][0]
    else:
        del keyboard[0][1]

    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


@run_async
def in_line_query(update, context):
    """
    Handle the inline query.
    """

    query = update.inline_query.query
    is_bot = update.inline_query.from_user.is_bot
    if not is_bot:

        current_year = int(datetime.now().strftime('%Y'))

        # get user's alert title IDs
        user_id = update.inline_query.from_user.id
        user_titles = movie.Alert(DATABASE).title_id(user_id)

        # search IMDb for titles
        titles = movie.search(query)
        results = []

        for title in titles:

            reply_markup = create_reply_markup(title, current_year, user_titles)

            result = InlineQueryResultArticle(id=result_id(title['id']),
                                              title=title['long imdb title'],
                                              input_message_content=InputTextMessageContent(
                                                  message_text=movie.reply_message(title),
                                                  parse_mode=ParseMode.HTML),
                                              description=title['plot'],
                                              thumb_url=title['cover url'],
                                              reply_markup=reply_markup)
            results.append(result)

        update.inline_query.answer(results, cache_time=4)


def log_error(update, context):
    """
    Log Errors caused by Updates.
    """

    LOG.error('Update "%s" caused error: "%s"', update, context.error)


def main():
    """
    Create the updater and dispatcher handlers
    """

    # Create the bot's alert database
    movie.Alert(DATABASE).create_db()

    # Create the updater and pass the bot's token.
    updater = Updater(TOKEN, use_context=True, workers=32)

    # Create repeating job to notify users
    job_start_time = datetime.time(datetime.now().replace(hour=int(JOB_TIME[0]),
                                                          minute=int(JOB_TIME[1])))
    job = updater.job_queue
    job.run_repeating(notify_users, interval=86400, first=job_start_time)

    # Get the dispatcher to register handlers
    dispatch = updater.dispatcher

    # On different commands - answer in Telegram
    dispatch.add_handler(CommandHandler("start", help_cmd))
    dispatch.add_handler(CommandHandler("help", help_cmd))
    dispatch.add_handler(CommandHandler("alerts", alerts_cmd))

    # Add the inline query handler
    dispatch.add_handler(InlineQueryHandler(in_line_query))

    # On chosing result, get its ID
    dispatch.add_handler(ChosenInlineResultHandler(chosen_result))

    # On button selection call appropriate function
    dispatch.add_handler(CallbackQueryHandler(enable_alert, pattern='^'+str(enable_alert)+'$'))
    dispatch.add_handler(CallbackQueryHandler(disable_alert, pattern='^'+str(disable_alert)+'$'))
    dispatch.add_handler(CallbackQueryHandler(dismiss, pattern='^'+str(dismiss)+'$'))

    # Answer to non-commands
    dispatch.add_handler(MessageHandler((~ Filters.entity('url')) &
                                        (~ Filters.entity('text_link')), unknown_cmd))

    # Log all errors
    dispatch.add_error_handler(log_error)

    # Start the Bot
    updater.start_polling()

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
