#!/usr/bin/env python

"""
Bot for playing tic tac toe game with multiple CallbackQueryHandlers.
"""
from copy import deepcopy
import random
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)
import os

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger('httpx').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# get token using BotFather
# TOKEN = os.getenv('TG_TOKEN')
TOKEN = '6905933127:AAEl6ROhC4Vb31vcXKhPdVNu5IZXLZlb1ig'

CONTINUE_GAME, FINISH_GAME = range(2)

FREE_SPACE = 'Ы'
CROSS = 'X'
ZERO = 'O'

DEFAULT_STATE = [[FREE_SPACE for _ in range(3)] for _ in range(3)]


def get_default_state():
    """Helper function to get default state of the game"""
    return deepcopy(DEFAULT_STATE)


def generate_keyboard(state: list[list[str]]) -> list[list[InlineKeyboardButton]]:
    """Generate tic tac toe keyboard 3x3 (telegram buttons)"""
    return [
        [
            InlineKeyboardButton(state[r][c], callback_data=f'{r}{c}')
            for r in range(3)
        ]
        for c in range(3)
    ]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send message on `/start`."""
    context.user_data['keyboard_state'] = get_default_state()
    keyboard = generate_keyboard(context.user_data['keyboard_state'])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f'X (your) turn! Please, put X to the free place', reply_markup=reply_markup)
    return CONTINUE_GAME


def AI(keyboard: list[list[str]]) -> tuple:
    """Мы проходимся по всем клеткам, запоминаем свободные, а после выбираем из них рандомную"""
    empty_spaces = []
    for i in range(3):
        for j in range(3):
            if keyboard[i][j] == FREE_SPACE:
                empty_spaces.append([i, j])
    if not empty_spaces:
        raise TypeError('Игра уже закончилась(')
    else:
        row, column = random.choice(empty_spaces)

    return (row, column)

    pass


async def game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Main processing of the game"""
    row, column = map(int, context.match.string)
    keyboard = context.user_data['keyboard_state']
    keyboard[row][column] = CROSS

    # создаём новое состояние и выводим его на экран после каждого хода
    new_keyboard = generate_keyboard(keyboard)
    reply_markup = InlineKeyboardMarkup(new_keyboard)
    if won(keyboard):
        await update.effective_message.edit_text('You win!', reply_markup=reply_markup)
        return FINISH_GAME

    try:
        bot_row, bot_column = AI(keyboard)
        keyboard[bot_row][bot_column] = ZERO
    except TypeError:
        # если бот не может сходить,то ничья (мы всегда можем сделать ход т.к. у нас нечётное число клеток)
        await update.effective_message.edit_text('Tie', reply_markup=reply_markup)
        return FINISH_GAME

    # опять обновляем наше поле
    new_keyboard = generate_keyboard(keyboard)
    reply_markup = InlineKeyboardMarkup(new_keyboard)

    # проверка выигрыша бота
    if won(keyboard):
        await update.effective_message.edit_text('Bot win!', reply_markup=reply_markup)
        return FINISH_GAME

    # если никто не победил, игра продолжается

    await update.effective_message.edit_text('X (your) turn! Please, put X to the free place', reply_markup=reply_markup)
    return CONTINUE_GAME


def won(fields: list[list[str]]) -> bool:
    """Check if crosses or zeros have won the game"""
    """Данный код проверяет наличие вертикальных и горизонтальных выйгрышей,
    переменныу hor и vert отвечают за горизонтальный и вертикальный выйгрыш соотв.
    Мы прибавляем +1 когда встречаем крестик и прибавляем -1 когда нолик, тем самым если у нас
    одно из значений равно +3 или -3, то выйгрыш есть"""
    for i in range(3):
        hor = 0
        vert = 0
        for j in range(3):
            if fields[i][j] == CROSS:
                hor += 1
            elif fields[i][j] == ZERO:
                hor -= 1
            if fields[j][i] == CROSS:
                vert += 1
            elif fields[j][i] == ZERO:
                vert -= 1
        if hor == 3 or hor == -3 or vert == 3 or vert == -3:
            return True

    """Этот код проверяет на наличие диагональных выйгрышей, по такому же принципу, как гор. и верт."""
    diag1 = 0
    for i in range(3):
        if fields[i][i] == CROSS:
            diag1 += 1
        elif fields[i][i] == ZERO:
            diag1 -= 1
    if diag1 == 3 or diag1 == -3:
        return True

    diag2 = 0
    for i in range(3):
        if fields[i][2 - i] == CROSS:
            diag2 += 1
        elif fields[i][2 - i] == ZERO:
            diag2 -= 1
    if diag2 == 3 or diag2 == -3:
        return True

    return False


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """
    # reset state to default so you can play again with /start
    context.user_data['keyboard_state'] = get_default_state()
    return ConversationHandler.END


def main() -> None:
    """Run the bot"""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Setup conversation handler with the states CONTINUE_GAME and FINISH_GAME
    # Use the pattern parameter to pass CallbackQueries with specific
    # data pattern to the corresponding handlers.
    # ^ means "start of line/string"
    # $ means "end of line/string"
    # So ^ABC$ will only allow 'ABC'
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CONTINUE_GAME: [
                CallbackQueryHandler(game, pattern='^' + f'{r}{c}' + '$')
                for r in range(3)
                for c in range(3)
            ],
            FINISH_GAME: [
                CallbackQueryHandler(end, pattern='^' + f'{r}{c}' + '$')
                for r in range(3)
                for c in range(3)
            ],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    # Add ConversationHandler to application that will be used for handling updates
    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
