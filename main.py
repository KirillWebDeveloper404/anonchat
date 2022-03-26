# -*- coding: utf-8 -*-
import logging
import asyncio
import os
import random

# aiogram и всё утилиты для коректной работы с Telegram API
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils.markdown import text, italic
from aiogram.types import ParseMode
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import aiogram.utils.exceptions
from aiogram.types.message import ContentTypes
from aiogram.dispatcher import FSMContext
from aiogram_broadcaster import MessageBroadcaster
from aiogram.types import Message

import config
from database import dbworker

db = dbworker('database.db')

async def broadcast_command_handler(msg: Message, state: FSMContext):
    if msg.chat.id in config.ADMIN_LIST:
        await msg.answer('Введите текст для начала рассылки:')
        await state.set_state('broadcast_text')

async def users_command_handler(msg: Message, state: FSMContext):
    if msg.chat.id in config.ADMIN_LIST:
        await msg.answer(f'В боте уже {int(db.count_user())} пользователей')

async def start_broadcast(msg: Message, state: FSMContext):
    await state.finish()
    users = db.get_users_id()
    await MessageBroadcaster(users, msg).run()
    button_search = KeyboardButton('🔎Начать поиск')
    button_info_project = KeyboardButton('📖Правила')
    ranked = KeyboardButton('⭐Рейтинг')
    count_users = KeyboardButton(f'В боте уже {int(db.count_user())} пользователей🥳')
    mark_menu = ReplyKeyboardMarkup(True, True)
    if msg.chat.id in config.ADMIN_LIST:
        mark_menu.add(button_search, button_info_project, ranked, count_users)
    else:
        mark_menu.add(button_search, button_info_project, ranked)
    await msg.answer('Рассылка закончена!', reply_markup=mark_menu)


async def main():

    bot = Bot(token=config.TOKEN)
    dp = Dispatcher(bot, storage=MemoryStorage())

    logging.basicConfig(filename="all_log.log", level=logging.INFO, format='%(asctime)s - %(levelname)s -%(message)s')
    warning_log = logging.getLogger("warning_log")
    warning_log.setLevel(logging.WARNING)
    fh = logging.FileHandler("warning_log.log")
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    warning_log.addHandler(fh)
    hellomsg = '''👋 Привет!
    
Я бот для анонимного общения!
И чего ты ждёшь, давай начнём!
    
Тыкай на кнопки внизу, а там разберёмся😎'''
    dp.register_message_handler(broadcast_command_handler, commands='broadcast')
    dp.register_message_handler(users_command_handler, commands='users')
    dp.register_message_handler(start_broadcast, state='broadcast_text', content_types=types.ContentTypes.ANY)


    @dp.message_handler(commands=['start'], state='*')
    async def start(message: types.Message, state: FSMContext):
        await state.finish()
        count_users = KeyboardButton(f'В боте уже {int(db.count_user())} пользователей🥳')
        button_search = KeyboardButton('🔎Начать поиск')
        button_info_project = KeyboardButton('📖Правила')
        ranked = KeyboardButton('⭐Рейтинг')
        mark_menu = ReplyKeyboardMarkup(True, True)
        if message.chat.id in config.ADMIN_LIST:
            mark_menu.add(button_search, button_info_project, ranked, count_users)
        else:
            mark_menu.add(button_search, button_info_project, ranked)
        if not db.user_exists(message.from_user.id):
            db.add_user(message.from_user.username, message.from_user.id)
        await bot.send_message(message.chat.id,
                               hellomsg,
                               reply_markup=mark_menu)

    @dp.message_handler(
        lambda message: message.text == f'В боте уже {int(db.count_user())} пользователей🥳',
        state='*')
    async def stat_text(message: types.Message):
        count_users = KeyboardButton(f'В боте уже {int(db.count_user())} пользователей🥳')
        button_search = KeyboardButton('🔎Начать поиск')
        button_info_project = KeyboardButton('📖Правила')
        ranked = KeyboardButton('⭐Рейтинг')
        mark_menu = ReplyKeyboardMarkup(True, True)
        if message.chat.id in config.ADMIN_LIST:
            mark_menu.add(button_search, button_info_project, ranked, count_users)
        else:
            mark_menu.add(button_search, button_info_project, ranked)
        await bot.send_message(message.chat.id,
                              hellomsg,
                               reply_markup=mark_menu)

    @dp.message_handler(commands=['rules'], state='*')
    @dp.message_handler(lambda message: message.text == '📖Правила')
    async def rules(message: types.Message):
        await message.answer('''📌Правила общения в данном анонимном чате\n1. Любые упоминания психоактивных веществ. (наркотиков)\n2. Детская порнография. ("ЦП")\n3. Мошенничество. (Scam)\n4. Любая реклама, спам.\n5. Продажи чего либо. (например - продажа интимных фотографий, видео)\n6. Любые действия, нарушающие правила Telegram.\n7. Оскорбительное поведение.\n8. Обмен, распространение любых 18+ материалов\n\n''')

    @dp.message_handler(commands=['search'], state='*')
    @dp.message_handler(lambda message: message.text == '🔎Начать поиск', state='*')
    async def search(message: types.Message):
        try:
            if not db.user_exists(message.from_user.id):
                db.add_user(message.from_user.username, message.from_user.id)
            male = KeyboardButton('Парня')
            wooman = KeyboardButton('Девушку')
            back = KeyboardButton('Назад')
            sex_menu = ReplyKeyboardMarkup(True, True)
            sex_menu.add(male, wooman, back)

            await message.answer('Выбери пол собеседника!\nКого вы ищете?)', reply_markup=sex_menu)
        except Exception as e:
            warning_log.warning(e)

    @dp.message_handler(lambda message: message.text == '⭐Рейтинг')
    async def ranked(message: types.Message, state: FSMContext):
        try:
            final_top = ''
            top_count = 0
            for i in db.top_rating():
                for d in i:
                    top_count += 1
                    if db.get_name_user(d) == None:
                        rofl_list = ['\nебааа#ь ты жёсткий😳', '\nвасап👋', '\nбро полегче там😮', '\nгений🧠',
                                     '\nреспект🤟']
                        final_top = final_top + str(top_count) + 'место - :(нету ника' + ' - ' + str(
                            db.get_count_all_msg(d)) + ' cообщений' + rofl_list[top_count - 1] + '\n'
                    else:
                        rofl_list = ['\nебааа#ь ты жёсткий😳', '\nвасап👋', '\nбро полегче там😮', '\nгений🧠',
                                     '\nреспект🤟']
                        final_top = final_top + str(top_count) + 'место - @' + str(db.get_name_user(d)) + ' - ' + str(
                            db.get_count_all_msg(d)) + ' cообщений' + rofl_list[top_count - 1] + '\n'
            await message.answer(
                f'Рейтинг самых п#здатых в этом чат боте\nОчки рейтинга получаются с помощью активностей в боте😎\n\n{final_top}')
        except Exception as e:
            warning_log.warning(e)

    class Chating(StatesGroup):
        msg = State()

    @dp.message_handler(lambda message: message.text == 'Парня' or message.text == 'Девушку', state='*')
    async def chooce_sex(message: types.Message, state: FSMContext):
        ''' Выбор пола для поиска '''
        try:
            if db.queue_exists(message.from_user.id):
                db.delete_from_queue(message.from_user.id)

                # update the random number to stop previous search
                db.update_random_number_user(message.from_user.id)
                randomNumber = db.get_random_number_user(message.from_user.id)[0]

                # check if previous search is stopped
                while db.get_random_number_user(message.from_user.id)[0] == randomNumber:
                    await asyncio.sleep(0.5)



            if message.text == 'Парня':
                db.edit_sex(True, message.from_user.id)
                db.add_to_queue(message.from_user.id, True)
            elif message.text == 'Девушку':
                db.edit_sex(False, message.from_user.id)
                db.add_to_queue(message.from_user.id, False)
            else:
                db.add_to_queue(message.from_user.id, db.get_sex_user(message.from_user.id)[0])

            await message.answer('Ищем для вас человечка...')

            stop = KeyboardButton('❌Остановить диалог')
            share_link = KeyboardButton('🏹Отправить ссылку на себя')
            coin = KeyboardButton('🎲Подбросить монетку')

            menu_msg = ReplyKeyboardMarkup(True, True)
            menu_msg.add(stop, share_link, coin)

            userFound = None

            # random number on search start
            randomNumber = db.get_random_number_user(message.from_user.id)[0]

            while True:
                await asyncio.sleep(0.5)

                # the random number has changed - we should stop searching
                if db.get_random_number_user(message.from_user.id)[0] != randomNumber:
                    # update the number to notify the outer code that we have stopped searching
                    db.update_random_number_user(message.from_user.id)
                    return

                if db.select_connect_with(message.from_user.id)[0] != None:  # если пользователь законектился
                    break

                userFound = db.search(db.get_sex_user(message.from_user.id)[0])
                if userFound != None:  # если был найден подходящий юзер в очереди
                    try:
                        db.update_connect_with(userFound[0],
                                               message.from_user.id)
                        db.update_connect_with(message.from_user.id,
                                               userFound[0])

                        # удаляем из очереди
                        db.delete_from_queue(message.from_user.id)
                        db.delete_from_queue(userFound[0])

                        break
                    except Exception as e:
                        print(e)


            await Chating.msg.set()

            await bot.send_message(message.from_user.id, 'Диалог начался!',
                                   reply_markup=menu_msg)
            return
        except Exception as e:
            print(e)
            warning_log.warning(e)
            await send_to_channel_log_exception(message, e)

    @dp.message_handler(content_types=ContentTypes.TEXT)
    @dp.message_handler(state=Chating.msg)
    async def chating(message: types.Message, state: FSMContext):
        try:
            next = KeyboardButton('➡️Следующий диалог')
            back = KeyboardButton('Назад')
            menu_msg_chating = ReplyKeyboardMarkup(True, True)
            menu_msg_chating.add(next, back)
            await state.update_data(msg=message.text)
            user_data = await state.get_data()
            if user_data['msg'] == '🏹Отправить ссылку на себя':
                if message.from_user.username == None:
                    await bot.send_message(db.select_connect_with_self(message.from_user.id)[0],
                                           'Пользователь не заполнил никнейм в настройках телеграма!')
                    await message.answer('Вы не заполнили никнейм в настройках телеграма!')
                else:
                    await bot.send_message(db.select_connect_with_self(message.from_user.id)[0],
                                           '@' + message.from_user.username)
                    await message.answer('@' + message.from_user.username)
            elif user_data['msg'] == '❌Остановить диалог':
                keys = InlineKeyboardMarkup()
                keys.add(InlineKeyboardButton(text='Администратор', url=config.ADMIN_LINK))
                await message.answer('Диалог закончился!', reply_markup=menu_msg_chating)
                await message.answer('Если вы заметили нарушителя, то можете обратится к администратору', reply_markup=keys)
                await bot.send_message(db.select_connect_with(message.from_user.id)[0], 'Диалог закончился!',
                                       reply_markup=menu_msg_chating)
                await bot.send_message(db.select_connect_with(message.from_user.id)[0], 'Если вы заметили нарушителя, то можете обратится к администратору',
                                     reply_markup=keys)

                db.update_connect_with(None, db.select_connect_with(message.from_user.id)[0])
                db.update_connect_with(None, message.from_user.id)
            elif user_data['msg'] == '➡️Следующий диалог':
                await chooce_sex(message, state)
            elif user_data['msg'] == '🎲Подбросить монетку':
                coin = random.randint(1, 2)
                if coin == 1:
                    coin = text(italic('Решка'))
                else:
                    coin = text(italic('Орёл'))
                await message.answer(coin, parse_mode=ParseMode.MARKDOWN)
                await bot.send_message(db.select_connect_with(message.from_user.id)[0], coin,
                                       parse_mode=ParseMode.MARKDOWN)
            elif user_data['msg'] == 'Назад':
                await start(message, state)
                await state.finish()
            else:
                await bot.send_message(db.select_connect_with(message.from_user.id)[0],
                                       user_data['msg'])  # отправляем сообщения пользователя
                db.log_msg(message.from_user.id, user_data['msg'])  # отправка сообщений юзеров в бд
                db.add_count_msg(message.from_user.id)  # добавление кол-ва сообщений в бд для рейтинга
                await send_to_channel_log(message)
        except aiogram.utils.exceptions.ChatIdIsEmpty:
            await state.finish()
            await start(message, state)
        except aiogram.utils.exceptions.BotBlocked:
            await message.answer('Пользователь вышел из чат бота!')
            await state.finish()
            await start(message, state)
        except Exception as e:
            warning_log.warning(e)
            await send_to_channel_log_exception(message, e)

    @dp.message_handler(content_types=ContentTypes.PHOTO, state=Chating.msg)
    async def chating_photo(message: types.Message, state: FSMContext):
        ''' Функция где и происходить общения и обмен ФОТОГРАФИЯМИ '''
        try:
            await message.photo[-1].download('photo_user/' + str(message.from_user.id) + '.jpg')
            with open('photo_user/' + str(message.from_user.id) + '.jpg', 'rb') as photo:
                await bot.send_photo(db.select_connect_with(message.from_user.id)[0], photo, caption=message.text)
            await os.remove('photo_user/' + str(message.from_user.id) + '.jpg')
        except Exception as e:
            warning_log.warning(e)
            await send_to_channel_log_exception(message, e)

    @dp.message_handler(content_types=ContentTypes.STICKER, state=Chating.msg)
    async def chating_sticker(message: types.Message):
        ''' Функция где и происходить общения и обмен CТИКЕРАМИ '''
        try:
            await bot.send_sticker(db.select_connect_with(message.from_user.id)[0], message.sticker.file_id)
        except Exception as e:
            warning_log.warning(e)
            await send_to_channel_log_exception(message, e)

    @dp.message_handler(commands=['back'])
    @dp.message_handler(lambda message: message.text == 'Назад', state='*')
    async def back(message: types.Message, state: FSMContext):
        await state.finish()
        await start(message, state)

    async def send_to_channel_log(message: types.Message):
        await bot.send_message(-1001422742707,
                               f'ID - {str(message.from_user.id)}\nusername - {str(message.from_user.username)}\nmessage - {str(message.text)}')

    async def send_to_channel_log_exception(message: types.Message, except_name):
        await bot.send_message(-1001422742707, f'Ошибка\n\n{except_name}')

    try:
        await dp.start_polling()
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
