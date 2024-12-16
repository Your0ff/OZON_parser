import asyncio
import emoji
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.filters import CommandStart, StateFilter
from Parser import OZON_Parser
from database.database import show_saved, write_in_db, delete_article
from Statuse.states import UserStates
from handlers.other_handlers import show_main_menu
from lexicon.lexicon import (LEXICON, LEXICON_show_saved, LEXICON_delete, LEXICON_right, LEXICON_input,
                             LEXICON_parser, LEXICON_left, LEXICON_help)


router = Router()
user_messages = {}
current_article_indices = {}


@router.message(CommandStart())
async def process_start_command(message: Message):
    await show_main_menu(message.bot, message.chat.id)


@router.message(F.text == '/help')
async def help_command(message: Message):
    await message.answer(LEXICON_help['help'])


@router.callback_query(F.data == 'show_saved')
async def show_saved_articles(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await callback_query.message.delete()

    saved_articles = await show_saved(user_id)

    if user_id not in current_article_indices:
        current_article_indices[user_id] = 0

    if saved_articles:
        current_index = current_article_indices[user_id]

        if current_index < 0:
            current_index = 0
        elif current_index >= len(saved_articles):
            current_index = len(saved_articles) - 1

        article = saved_articles[current_index]
        article_id = article[2]
        product_name = article[3]
        old_price_card = article[5]

        try:
            data = OZON_Parser.get_articule(article_id)
            new_price_card = data['allprice'][1]

            if int(new_price_card[:-2].replace(' ', '')) > int(old_price_card):
                emoji_indicator = emoji.emojize(':up_arrow:')
            elif int(new_price_card[:-2].replace(' ', '')) < int(old_price_card):
                emoji_indicator = emoji.emojize(':down_arrow:')
            else:
                emoji_indicator = emoji.emojize(':heavy_equals_sign:')
            response_message = (f"Артикул: {article[2]};\n"
                                f"Название товара: {product_name};\n"
                                f"Цена с OZON картой: {old_price_card} ₽ {emoji_indicator} {new_price_card}\n")
        except Exception as e:
            response_message = "Ошибка при получении актуальной цены."

        inline_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=emoji.emojize(':left_arrow:'), callback_data='left'),
                InlineKeyboardButton(text=LEXICON['btn_1'], callback_data='menu'),
                InlineKeyboardButton(text=emoji.emojize(':right_arrow:'), callback_data='right')
            ],
            [
                InlineKeyboardButton(text=LEXICON_show_saved['btn_1'], callback_data=f'delete_{article_id}')
            ]
        ])

        await callback_query.message.answer(response_message, reply_markup=inline_kb)
    else:
        await callback_query.message.answer(LEXICON_show_saved['text_none'])
        await show_main_menu(callback_query.message.bot, user_id)


@router.callback_query(F.data.startswith('delete_'))
async def handle_delete_article_id(callback_query: types.CallbackQuery):
    article_id = int(callback_query.data.split('_')[1])
    await delete_article(article_id, user_id=callback_query.from_user.id)
    await callback_query.answer(LEXICON_delete['text_delete'])
    await show_saved_articles(callback_query)


@router.callback_query(F.data == 'right')
async def next_article(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    saved_articles = await show_saved(user_id)

    if user_id in current_article_indices:
        current_index = current_article_indices[user_id]

        if current_index < len(saved_articles) - 1:
            current_article_indices[user_id] += 1
            await show_saved_articles(callback_query)
        else:
            await callback_query.answer(LEXICON_right['text_right'])


@router.callback_query(F.data == 'left')
async def previous_article(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    if user_id in current_article_indices:
        current_index = current_article_indices[user_id]

        if current_index > 0:
            current_article_indices[user_id] -= 1
            await show_saved_articles(callback_query)
        else:
            await callback_query.answer(LEXICON_left['text_left'])


@router.callback_query(F.data == 'input_article')
async def handle_input_article(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_for_article)
    request_message = await (callback_query.message.answer
                             (LEXICON_input['text_input']))
    await state.update_data(request_message_id=request_message.message_id)


@router.message(StateFilter(UserStates.waiting_for_article))
async def parser(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    article_id = message.text.strip()

    if not article_id.isdigit() or len(article_id) < 9 or len(article_id) > 12:
        await message.answer(LEXICON_parser['text_parser'])
        return

    try:
        article_id = int(article_id)
        data = OZON_Parser.get_articule(article_id)

        product_info = (
            f"<b>Название:</b> {data['name']}\n"
            f"<b>Продавец:</b> {data['seller']}\n"
            f"<b>Артикул:</b> {data['article']}\n"
            f"<b>Цена с OZON картой:</b> {data['allprice'][1]}\n"
            f"<b>Цена без OZON картой:</b> {data['allprice'][0]}"
        )

        await state.update_data(
            user_id=user_id,
            article_id=article_id,
            product_name=data['name'],
            price=data['allprice'][0],
            price_card=data['allprice'][1]
        )

        inline_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=LEXICON_parser['btn_save_article'],
                    callback_data='save_article'
                ),
                InlineKeyboardButton(
                    text=LEXICON['btn_1'],
                    callback_data='menu'
                )
            ]
        ])
        await message.answer_photo(data['img'], caption=product_info, reply_markup=inline_kb, parse_mode='HTML')

    except TypeError:
        await message.answer(LEXICON_parser['parser_error'])


@router.callback_query(F.data == 'save_article')
async def save_article(callback_query: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()

    user_id = user_data.get('user_id')
    article_id = user_data.get('article_id')
    product_name = user_data.get('product_name')
    price = user_data.get('price').replace(' ', '').replace('₽', '')
    price_card = user_data.get('price_card').replace(' ', '').replace('₽', '')

    await write_in_db(user_id=user_id,
                      article_id=article_id,
                      product_name=product_name,
                      price=int(price),
                      price_card=int(price_card))

    saved_message = await callback_query.message.answer(f"Артикул {article_id} сохранен!")
    await asyncio.sleep(2)
    await callback_query.message.bot.delete_message(chat_id=callback_query.message.chat.id,
                                                    message_id=saved_message.message_id)


@router.callback_query(F.data == 'menu')
async def return_to_menu(callback_query: types.CallbackQuery, state: FSMContext):
    chat_id = callback_query.from_user.id
    await callback_query.message.delete()
    await state.clear()
    await show_main_menu(callback_query.message.bot, chat_id)

