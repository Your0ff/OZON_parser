import asyncio

from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from lexicon.lexicon import LEXICON_menu

router = Router()
user_states = {}


@router.message()
async def handle_unexpected_message(message: types.Message):
    current_state = user_states.get(message.from_user.id)

    if current_state != 'waiting_for_article':
        sent_message = await message.answer("Пожалуйста, используйте кнопку 'Ввести артикул' в главном меню.")
        await asyncio.sleep(5)
        await message.bot.delete_message(chat_id=message.chat.id, message_id=sent_message.message_id)


async def show_main_menu(bot, chat_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LEXICON_menu['but_1'], callback_data='input_article')],
        [InlineKeyboardButton(text=LEXICON_menu['but_2'], callback_data='show_saved')]
    ])
    menu_message = await bot.send_message(chat_id,
                                          text=LEXICON_menu['text'],
                                          reply_markup=keyboard)
    return menu_message

