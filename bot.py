import asyncio
import re
import random
import sqlite3
from keep_alive import keep_alive
from health_server import start_health_server
from server import start_server
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery

from config import BOT_TOKEN, ADMIN_GROUP_ID
from database import (
    init_db, get_user, create_user, update_flashgram_data, add_stars, 
    remove_stars, get_stars, add_to_inventory, remove_from_inventory, 
    get_inventory, get_referral_count, add_referral, get_top_refs,
    update_last_free_case, get_last_free_case, add_withdrawal,
    get_promocode, use_promocode, add_promocode,
    add_shop_order, get_shop_order, update_shop_order_price, update_shop_order_link, update_shop_order_status,
    delete_inventory_item_by_id
)
from states import RegisterStates, SettingsStates, PromocodeStates, ShopStates, CasinoStates
from keyboards import (
    main_menu, subscribe_button, back_to_main, referrals_menu,
    rating_back, get_paginated_inventory, get_paginated_cases, settings_menu,
    admin_withdraw_button, get_paginated_shop, get_paginated_colors,
    admin_shop_buttons, admin_shop_actions, user_cancel_button, casino_menu, dice_game_menu,
    nft_action_menu, confirm_sell, donate_menu
)
from utils import FREE_CASE_REWARDS, CASES_DATA, get_random_reward, roll_dice, NFT_SELL_PRICES

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

REQUIRED_CHANNEL = "@alonewho666"
REQUIRED_CHANNEL_2 = "@flashgram_info"

# Глобальные переменные для управления магазином
shop_open = True

# ============ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ============

async def is_subscribed(user_id: int) -> bool:
    try:
        member1 = await bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        member2 = await bot.get_chat_member(REQUIRED_CHANNEL_2, user_id)
        return member1.status in ["member", "administrator", "creator"] and \
               member2.status in ["member", "administrator", "creator"]
    except:
        return False

# Новая реферальная система
async def check_referral_levels(user_id):
    ref_count = get_referral_count(user_id)
    
    level_rewards = {
        2: ["50 Stars"],
        5: ["80 Stars"],
        9: ["130 Stars"],
        15: ["Кейс Фелириум"],
        20: ["Кейс Запах", "Кейс Фелириум"],
        26: ["Кейс Богач", "Кейс Свадьба"],
        32: ["Кейс Шахта", "Кейс Все или ничего"],
        40: ["Кейс Небо", "Кейс Сердечный приступ"],
        50: ["Кейс Время", "Кейс Черный", "Кейс PEPE"],
        75: ["Кейс Мифическая слава", "Кейс alone"]
    }
    
    for level, rewards in level_rewards.items():
        if ref_count >= level:
            for reward in rewards:
                if "Stars" in reward:
                    stars_count = int(re.search(r'\d+', reward).group())
                    add_stars(user_id, stars_count)
                    await bot.send_message(user_id, f"<b>🎉 За достижение уровня {level} (рефералов: {ref_count}) вы получили {reward}!</b>", parse_mode="HTML")
                else:
                    add_to_inventory(user_id, reward)
                    await bot.send_message(user_id, f"<b>🎉 За достижение уровня {level} (рефералов: {ref_count}) вы получили {reward}!</b>", parse_mode="HTML")

# Админ команда для рассылки
@dp.message(Command("news"))
async def news_command(message: Message):
    if message.chat.id != ADMIN_GROUP_ID:
        return
    
    news_text = message.text.replace("/news", "").strip()
    if not news_text:
        await message.reply("❌ Напишите текст рассылки после команды /news")
        return
    
    # Получаем всех пользователей
    conn = sqlite3.connect("flashgram.db")
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = c.fetchall()
    conn.close()
    
    success = 0
    fail = 0
    for user in users:
        try:
            await bot.send_message(user[0], f"<b>📢 Новость от администратора:\n\n{news_text}</b>", parse_mode="HTML")
            success += 1
            await asyncio.sleep(0.05)  # небольшая задержка чтобы не спамить
        except:
            fail += 1
    
    await message.reply(f"✅ Рассылка завершена!\nУспешно: {success}\nОшибок: {fail}")

# Админ команды для управления магазином
@dp.message(Command("closeshop"))
async def close_shop_command(message: Message):
    if message.chat.id != ADMIN_GROUP_ID:
        return
    global shop_open
    shop_open = False
    await message.reply("✅ Магазин закрыт на технический перерыв!")

@dp.message(Command("openshop"))
async def open_shop_command(message: Message):
    if message.chat.id != ADMIN_GROUP_ID:
        return
    global shop_open
    shop_open = True
    await message.reply("✅ Магазин открыт!")

# ============ КОМАНДА /START ============

@dp.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    
    args = message.text.split()
    ref_id = None
    if len(args) > 1 and args[1].isdigit():
        ref_id = int(args[1])
        if ref_id == user_id:
            ref_id = None
    
    user = get_user(user_id)
    
    if user:
        if await is_subscribed(user_id):
            await state.clear()
            await message.answer(
                f"<b><tg-emoji emoji-id='5336860842283515961'>✅</tg-emoji> Вы подписаны на телеграм канал разработчика бота и канал Flashgram, спасибо!\n\n"
                f"<tg-emoji emoji-id='5168379346959729629'>🎮</tg-emoji> В данном боте вы сможете получать NFT подарки и звезды в FLASHGRAM буквально бесплатно!\n\n"
                f"<tg-emoji emoji-id='5262623036946794266'>👤</tg-emoji> Создатель бота - @alonewho666</b>",
                parse_mode="HTML",
                reply_markup=main_menu()
            )
        else:
            await message.answer(
                f"<b><tg-emoji emoji-id='5339113303522161846'>👋</tg-emoji> Приветствуем вас в телеграм боте FlashgramNFT, для использования бота вам нужно быть подписаным на телеграм канал разработчика и канал Flashgram.</b>",
                parse_mode="HTML",
                reply_markup=subscribe_button()
            )
        return
    
    create_user(user_id, username, ref_id)
    if ref_id:
        add_referral(ref_id, user_id)
        await check_referral_levels(ref_id)
    
    await state.clear()
    
    await message.answer(
        f"<b><tg-emoji emoji-id='5339113303522161846'>👋</tg-emoji> Приветствуем вас в телеграм боте FlashgramNFT, для использования бота вам нужно быть подписаным на телеграм канал разработчика и канал Flashgram.</b>",
        parse_mode="HTML",
        reply_markup=subscribe_button()
    )

# ============ ПРОВЕРКА ПОДПИСКИ ============

@dp.callback_query(F.data == "check_subscribe")
async def check_subscribe(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    
    if await is_subscribed(user_id):
        await callback.message.delete()
        await callback.message.answer(
            f"<b><tg-emoji emoji-id='5168379346959729629'>📝</tg-emoji> Напишите свой юзернейм в Flashgram:</b>",
            parse_mode="HTML"
        )
        await state.set_state(RegisterStates.waiting_flashgram_username)
    else:
        await callback.answer("❌ Вы не подписаны на каналы!", show_alert=True)

# ============ РЕГИСТРАЦИЯ ============

@dp.message(RegisterStates.waiting_flashgram_username)
async def get_flashgram_username(message: Message, state: FSMContext):
    flashgram_username = message.text.strip()
    await state.update_data(flashgram_username=flashgram_username)
    
    await message.answer(
        "<b>Напишите свой номер в Flashgram и откройте его в профиле, это нужно для верификации аккаунта и удобного поиска для выдачи NFT.</b>",
        parse_mode="HTML"
    )
    await state.set_state(RegisterStates.waiting_flashgram_phone)

@dp.message(RegisterStates.waiting_flashgram_phone)
async def get_flashgram_phone(message: Message, state: FSMContext):
    flashgram_phone = message.text.strip()
    user_data = await state.get_data()
    flashgram_username = user_data.get("flashgram_username")
    
    user_id = message.from_user.id
    update_flashgram_data(user_id, flashgram_username, flashgram_phone)
    
    await state.clear()
    
    await message.answer(
        f"<b><tg-emoji emoji-id='5336860842283515961'>✅</tg-emoji> Вы подписаны на телеграм канал разработчика бота и канал Flashgram, спасибо!\n\n"
        f"<tg-emoji emoji-id='5168379346959729629'>🎮</tg-emoji> В данном боте вы сможете получать NFT подарки и звезды в FLASHGRAM буквально бесплатно!\n\n"
        f"<tg-emoji emoji-id='5262623036946794266'>👤</tg-emoji> Создатель бота - @alonewho666</b>",
        parse_mode="HTML",
        reply_markup=main_menu()
    )

# ============ ГЛАВНОЕ МЕНЮ ============

@dp.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        f"<b><tg-emoji emoji-id='5336860842283515961'>✅</tg-emoji> Вы подписаны на телеграм канал разработчика бота и канал Flashgram, спасибо!\n\n"
        f"<tg-emoji emoji-id='5168379346959729629'>🎮</tg-emoji> В данном боте вы сможете получать NFT подарки и звезды в FLASHGRAM буквально бесплатно!\n\n"
        f"<tg-emoji emoji-id='5262623036946794266'>👤</tg-emoji> Создатель бота - @alonewho666</b>",
        parse_mode="HTML",
        reply_markup=main_menu()
    )
    await callback.answer()

# ============ ДОНАТ ============

@dp.callback_query(F.data == "donate")
async def donate_handler(callback: CallbackQuery):
    text = f"""<b><tg-emoji emoji-id='5305699699204837855'>💝</tg-emoji> Донат, единственная вещь которая поддержит разработчика бота, а то он сильно уж устал ввхввхвх)

<tg-emoji emoji-id='5363992034728229166'>📍</tg-emoji> Как проходит донат?
- Вы выбираете сколько звезд вы хотите в боте;
- Выбираете способ оплаты;
- Списываетесь со мной по поводу покупки.

<tg-emoji emoji-id='5429263077927300012'>💎</tg-emoji> Оплата звездами в Telegram
200 Stars = 15 Звёзд
450 Stars = 25 Звёзд
700 Stars = 50 Звёзд
1500 Stars = 75 Звёзд
3000 Stars = 100 Звёзд

<tg-emoji emoji-id='5427225953463972959'>🌟</tg-emoji> Оплата звездами в Flashgram
200 Stars = 1000 Звёзд
450 Stars = 3200 Звёзд
700 Stars = 7000 Звёзд
1500 Stars = 13000 Звёзд
3000 Stars = 20000 Звёзд

<tg-emoji emoji-id='5363992034728229166'>📞</tg-emoji> Списаться с создателем по поводу покупки @enclox</b>"""
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=donate_menu()
    )
    await callback.answer()

# ============ БЕСПЛАТНЫЙ КЕЙС ============

@dp.callback_query(F.data == "free_case")
async def free_case(callback: CallbackQuery):
    user_id = callback.from_user.id
    last_case = get_last_free_case(user_id)
    
    if last_case:
        time_diff = datetime.now() - last_case
        if time_diff < timedelta(hours=24):
            hours_left = 24 - time_diff.total_seconds() / 3600
            minutes_left = int((hours_left % 1) * 60)
            hours_left = int(hours_left)
            await callback.answer(f"Для следующего открытия подождите {hours_left} часов {minutes_left} минут!", show_alert=True)
            return
    
    all_slots = ["25 Stars", "30 Stars", "50 Stars", "Lol Pop", "Candy Cane"]
    
    msg = await callback.message.answer("🎰 Крутим...")
    
    for _ in range(10):
        random_slots = [random.choice(all_slots) for _ in range(3)]
        text = f"{random_slots[0]} | {random_slots[1]} | {random_slots[2]}"
        await msg.edit_text(text)
        await asyncio.sleep(0.5)
    
    reward = get_random_reward(FREE_CASE_REWARDS)
    update_last_free_case(user_id)
    
    if "Stars" in reward:
        stars_count = int(re.search(r'\d+', reward).group())
        add_stars(user_id, stars_count)
        await msg.edit_text(
            f"<b><tg-emoji emoji-id='5262517101578443800'>🎉</tg-emoji> Вам выпали звезды в количестве {stars_count}!\n\n"
            f"<tg-emoji emoji-id='5336860842283515961'>✅</tg-emoji> Они появились в вашем балансе!</b>",
            parse_mode="HTML",
            reply_markup=back_to_main()
        )
    else:
        add_to_inventory(user_id, reward)
        await msg.edit_text(
            f"<b><tg-emoji emoji-id='5262517101578443800'>🎉</tg-emoji> Вам выпал NFT «{reward}». Поздравляем!\n\n"
            f"<tg-emoji emoji-id='5336860842283515961'>✅</tg-emoji> Он появиться в вашем инвентаре!</b>",
            parse_mode="HTML",
            reply_markup=back_to_main()
        )
    
    await callback.answer()

# ============ РЕФЕРАЛЫ (НОВЫЕ УРОВНИ) ==========

@dp.callback_query(F.data == "referrals")
async def referrals_menu_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    bot_username = (await bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    ref_count = get_referral_count(user_id)
    
    if ref_count >= 75:
        level = 10
    elif ref_count >= 50:
        level = 9
    elif ref_count >= 40:
        level = 8
    elif ref_count >= 32:
        level = 7
    elif ref_count >= 26:
        level = 6
    elif ref_count >= 20:
        level = 5
    elif ref_count >= 15:
        level = 4
    elif ref_count >= 9:
        level = 3
    elif ref_count >= 5:
        level = 2
    elif ref_count >= 2:
        level = 1
    else:
        level = 0
    
    text = f"""<b><tg-emoji emoji-id='5271604874419647061'>👥</tg-emoji> Реферальная программа. С помощью нее вы можете получать кейсы и звезды!

<tg-emoji emoji-id='5262758886762368240'>📊</tg-emoji> Уровни и награды:

<tg-emoji emoji-id='5210863290846053617'>1️⃣</tg-emoji> 1 уровень (2 реферала) - 50 Stars
<tg-emoji emoji-id='5211195669775157055'>2️⃣</tg-emoji> 2 уровень (5 рефералов) - 80 Stars
<tg-emoji emoji-id='5208724955478401912'>3️⃣</tg-emoji> 3 уровень (9 рефералов) - 130 Stars
<tg-emoji emoji-id='5208538373509125577'>4️⃣</tg-emoji> 4 уровень (15 рефералов) - Кейс Фелириум
<tg-emoji emoji-id='5208966822266706069'>5️⃣</tg-emoji> 5 уровень (20 рефералов) - Кейс Запах, Кейс Фелириум
<tg-emoji emoji-id='5208487890463530182'>6️⃣</tg-emoji> 6 уровень (26 рефералов) - Кейс Богач, Кейс Свадьба
<tg-emoji emoji-id='5208682766014652414'>7️⃣</tg-emoji> 7 уровень (32 реферала) - Кейс Шахта, Кейс Все или ничего
<tg-emoji emoji-id='5208912525290150178'>8️⃣</tg-emoji> 8 уровень (40 рефералов) - Кейс Небо, Кейс Сердечный приступ
<tg-emoji emoji-id='5208919367173048054'>9️⃣</tg-emoji> 9 уровень (50 рефералов) - Кейс Время, Кейс Черный, Кейс PEPE
<tg-emoji emoji-id='5211030386548703968'>🔟</tg-emoji> 10 уровень (75 рефералов) - Кейс Мифическая слава, Кейс alone

<tg-emoji emoji-id='5339113303522161846'>🏆</tg-emoji> Ваш текущий уровень: {level} (рефералов: {ref_count})

<tg-emoji emoji-id='5339113303522161846'>🔗</tg-emoji> Ваша реферальная ссылка: {ref_link}</b>"""
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=referrals_menu()
    )
    await callback.answer()

# ============ РЕЙТИНГ ============

@dp.callback_query(F.data == "rating")
async def rating_handler(callback: CallbackQuery):
    top_users = get_top_refs(10)
    
    text = f"<b><tg-emoji emoji-id='5231200819986047254'>🏆</tg-emoji> Рейтинг пользователей по рефералам:\n\n"
    
    for i, (username, count) in enumerate(top_users, 1):
        if i == 1:
            text += f"<tg-emoji emoji-id='5440539497383087970'>🥇</tg-emoji> "
        elif i == 2:
            text += f"<tg-emoji emoji-id='5447203607294265305'>🥈</tg-emoji> "
        elif i == 3:
            text += f"<tg-emoji emoji-id='5453902265922376865'>🥉</tg-emoji> "
        else:
            text += f"{i}. "
        text += f"@{username or 'NoName'} - {count} рефералов\n"
    
    text += "</b>"
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=rating_back()
    )
    await callback.answer()

# ============ ИНВЕНТАРЬ ==========

@dp.callback_query(F.data == "inventory")
async def inventory_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    items = get_inventory(user_id)
    stars = get_stars(user_id)
    
    await callback.message.edit_text(
        f"<b><tg-emoji emoji-id='5165929450369451797'>📦</tg-emoji> Ваш пользовательский инвентарь:\n\n"
        f"<tg-emoji emoji-id='5440539497383087970'>⭐️</tg-emoji> Количество накопленных звезд: {stars}\n\n"
        f"<tg-emoji emoji-id='5427225953463972959'>⭐️</tg-emoji>Предметы:</b>",
        parse_mode="HTML",
        reply_markup=get_paginated_inventory(items, 0)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("inv_page_"))
async def inventory_page(callback: CallbackQuery):
    page = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    items = get_inventory(user_id)
    
    await callback.message.edit_reply_markup(
        reply_markup=get_paginated_inventory(items, page)
    )
    await callback.answer()

# Просмотр NFT в инвентаре
@dp.callback_query(F.data.startswith("view_nft_"))
async def view_nft(callback: CallbackQuery):
    nft_name = callback.data.replace("view_nft_", "")
    
    await callback.message.edit_text(
        f"<b>🎁 {nft_name}</b>",
        parse_mode="HTML",
        reply_markup=nft_action_menu(nft_name)
    )
    await callback.answer()

# Продажа NFT
@dp.callback_query(F.data.startswith("sell_"))
async def sell_nft(callback: CallbackQuery):
    nft_name = callback.data.replace("sell_", "")
    price = NFT_SELL_PRICES.get(nft_name, 0)
    
    if price == 0:
        await callback.answer("Этот предмет нельзя продать!", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"<b><tg-emoji emoji-id='5197288647275071607'>⭐️</tg-emoji>Вы уверены что хотите продать подарок «{nft_name}» за {price} звезд?</b>",
        parse_mode="HTML",
        reply_markup=confirm_sell(nft_name, price)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("confirm_sell_"))
async def confirm_sell_nft(callback: CallbackQuery):
    nft_name = callback.data.replace("confirm_sell_", "")
    user_id = callback.from_user.id
    price = NFT_SELL_PRICES.get(nft_name, 0)
    
    # Проверяем есть ли NFT у пользователя
    inventory = get_inventory(user_id)
    if nft_name not in inventory:
        await callback.answer("Этого NFT нет в инвентаре!", show_alert=True)
        return
    
    # Удаляем NFT и добавляем звезды
    remove_from_inventory(user_id, nft_name)
    add_stars(user_id, price)
    
    # Обновляем инвентарь
    items = get_inventory(user_id)
    stars = get_stars(user_id)
    
    await callback.message.edit_text(
        f"<b><tg-emoji emoji-id='5165929450369451797'>📦</tg-emoji> Ваш пользовательский инвентарь:\n\n"
        f"<tg-emoji emoji-id='5440539497383087970'>⭐️</tg-emoji> Количество накопленных звезд: {stars}\n\n"
        f"<tg-emoji emoji-id='5427225953463972959'>⭐️</tg-emoji>Предметы:</b>",
        parse_mode="HTML",
        reply_markup=get_paginated_inventory(items, 0)
    )
    await callback.answer(f"<tg-emoji emoji-id='5305699699204837855'>⭐️</tg-emoji>Вы продали {nft_name} за {price} звезд!", show_alert=True)

# ============ ВЫВОД ПОДАРКА ==========

@dp.callback_query(F.data.startswith("withdraw_"))
async def withdraw_item(callback: CallbackQuery):
    item_name = callback.data.replace("withdraw_", "")
    user_id = callback.from_user.id
    user = get_user(user_id)
    
    # Проверяем есть ли предмет
    inventory = get_inventory(user_id)
    if item_name not in inventory:
        await callback.answer("Этого предмета нет в инвентаре!", show_alert=True)
        return
    
    remove_from_inventory(user_id, item_name)
    
    # Создаем тему в админ группе
    try:
        topic = await bot.create_forum_topic(
            chat_id=ADMIN_GROUP_ID,
            name=f"Вывод {item_name}"
        )
        thread_id = topic.message_thread_id
        
        await bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            message_thread_id=thread_id,
            text=f"Выводит: @{callback.from_user.username}\nTelegram ID: {user_id}\nFlashgram юз: {user[2] if user else 'Не указан'}\nFlashgram номер: {user[3] if user else 'Не указан'}\nЧто выводит: {item_name}",
            reply_markup=admin_withdraw_button(1)
        )
    except Exception as e:
        print(f"Ошибка создания темы: {e}")
    
    await callback.message.edit_text(
        "<b><tg-emoji emoji-id='5363992034728229166'>📦</tg-emoji>Вы подали заявку на вывод своего подарка, ожидайте.</b>",
        parse_mode="HTML",
        reply_markup=back_to_main()
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_withdraw_"))
async def admin_withdraw(callback: CallbackQuery):
    # Получаем ID заявки из callback_data (если есть)
    parts = callback.data.split("_")
    withdrawal_id = parts[2] if len(parts) > 2 else 1
    
    # Получаем информацию о выводе из сообщения в теме
    message_text = callback.message.text
    
    # Парсим сообщение чтобы получить имя пользователя и предмет
    # Пример сообщения: "Выводит: @username\nTelegram ID: 12345\n...\nЧто выводит: Jelly Bunny"
    lines = message_text.split("\n")
    username = None
    user_id = None
    item_name = None
    
    for line in lines:
        if line.startswith("Выводит: @"):
            username = line.replace("Выводит: @", "").strip()
        elif line.startswith("Telegram ID:"):
            user_id = int(line.replace("Telegram ID:", "").strip())
        elif line.startswith("Что выводит:"):
            item_name = line.replace("Что выводит:", "").strip()
    
    if user_id and item_name:
        try:
            await bot.send_message(
                user_id,
                f"<b><tg-emoji emoji-id='5197288647275071607'>✅</tg-emoji> Ваш NFT «{item_name}» был выведен вам на аккаунт в Flashgram!\n\n"
                f"<tg-emoji emoji-id='5429263077927300012'>👤</tg-emoji> Проверьте свой профиль, подарок уже должен быть у вас.\n\n"
                f"<tg-emoji emoji-id='5262736024651452318'>🎮</tg-emoji> Спасибо, что пользуетесь ботом!</b>",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Ошибка отправки уведомления пользователю: {e}")
    
    await callback.message.edit_text(
        callback.message.text + "\n\n✅ Выведено администратором! Пользователь уведомлен.",
        reply_markup=None
    )
    await callback.answer("Готово!")

# ============ КЕЙСЫ ==========

@dp.callback_query(F.data == "cases")
async def cases_handler(callback: CallbackQuery):
    keyboard, _ = get_paginated_cases(0)
    await callback.message.edit_text(
        f"<b><tg-emoji emoji-id='5165663102267557505'>🎲</tg-emoji> Кейсы, место, где вы можете открывать боксы и получать из них NFT подарки и звезды!\n\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «Фелириум» — 30 звезд\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «Запах» — 40 звезд\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «Богач» — 50 звезд\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «Свадьба» — 60 звезд\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «Шахта» — 80 звезд\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «Всё или ничего» — 80 звезд\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «Небо» — 100 звезд\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «Сердечный приступ» — 130 звезд\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «Время» — 140 звезд\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «Чёрный» — 150 звезд\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «PEPE» — 200 звезд\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «Мифическая слава» — 210 звезд\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «alone» — 380 звезд\n\n"
        f"Выберите какой кейс вы хотите купить, он появиться у вас в инвентаре!</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("cases_page_"))
async def cases_page(callback: CallbackQuery):
    page = int(callback.data.split("_")[2])
    keyboard, _ = get_paginated_cases(page)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data.startswith("buy_"))
async def buy_case(callback: CallbackQuery):
    case_name = callback.data.replace("buy_", "")
    price = CASES_DATA[case_name]["price"]
    
    user_id = callback.from_user.id
    stars = get_stars(user_id)
    
    if stars < price:
        await callback.answer(f"Недостаточно звезд! Нужно {price} звезд.", show_alert=True)
        return
    
    remove_stars(user_id, price)
    add_to_inventory(user_id, f"Кейс {case_name}")
    
    await callback.answer(f"Вы купили кейс «{case_name}»! Он появился в инвентаре.", show_alert=True)

@dp.callback_query(F.data.startswith("open_case_"))
async def open_case_from_inventory(callback: CallbackQuery):
    case_full_name = callback.data.replace("open_case_", "")
    user_id = callback.from_user.id
    
    inventory = get_inventory(user_id)
    if case_full_name not in inventory:
        await callback.answer("Этого кейса нет в инвентаре!", show_alert=True)
        return
    
    case_name = case_full_name.replace("Кейс ", "")
    
    if case_name not in CASES_DATA:
        await callback.answer(f"Кейс «{case_name}» не найден!", show_alert=True)
        return
    
    remove_from_inventory(user_id, case_full_name)
    
    # Обновляем инвентарь
    items = get_inventory(user_id)
    stars = get_stars(user_id)
    
    await callback.message.edit_text(
        f"<b><tg-emoji emoji-id='5165929450369451797'>📦</tg-emoji> Ваш пользовательский инвентарь:\n\n"
        f"<tg-emoji emoji-id='5440539497383087970'>⭐️</tg-emoji> Количество накопленных звезд: {stars}\n\n"
        f"<tg-emoji emoji-id='5427225953463972959'>⭐️</tg-emoji>Предметы:</b>",
        parse_mode="HTML",
        reply_markup=get_paginated_inventory(items, 0)
    )
    
    # Анимация
    rewards_list = list(CASES_DATA[case_name]["rewards"].keys())
    all_slots = rewards_list[:8] if len(rewards_list) > 8 else rewards_list
    if len(all_slots) < 3:
        all_slots = all_slots * 3
    
    msg = await callback.message.answer(f"<b><tg-emoji emoji-id='5429106865671793190'>🎲</tg-emoji> Открываем кейс {case_name}...</b>", parse_mode="HTML")
    
    for _ in range(8):
        random_slots = [random.choice(all_slots) for _ in range(3)]
        text = f"{random_slots[0]} | {random_slots[1]} | {random_slots[2]}"
        await msg.edit_text(text)
        await asyncio.sleep(0.3)
    
    reward = get_random_reward(CASES_DATA[case_name]["rewards"])
    
    if "Stars" in reward or "stars" in reward:
        stars_count = int(re.search(r'\d+', reward).group())
        add_stars(user_id, stars_count)
        await msg.edit_text(
            f"<b><tg-emoji emoji-id='5262517101578443800'>🎉</tg-emoji> Вам выпали звезды в количестве {stars_count}!</b>",
            parse_mode="HTML",
            reply_markup=back_to_main()
        )
    else:
        add_to_inventory(user_id, reward)
        await msg.edit_text(
            f"<b><tg-emoji emoji-id='5262517101578443800'>🎉</tg-emoji> Вам выпал NFT «{reward}». Поздравляем!\n\n"
            f"<tg-emoji emoji-id='5336860842283515961'>✅</tg-emoji> Он появиться в вашем инвентаре!</b>",
            parse_mode="HTML",
            reply_markup=back_to_main()
        )
    
    await callback.answer()

# ============ НАСТРОЙКИ ==========

@dp.callback_query(F.data == "settings")
async def settings_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = get_user(user_id)
    flashgram_username = user[2] if user else "Не указан"
    flashgram_phone = user[3] if user else "Не указан"
    
    await callback.message.edit_text(
        f"<b><tg-emoji emoji-id='5341715473882955310'>⚙️</tg-emoji> Вы находитесь в настройках.\n\n"
        f"Ваш юзернейм в Flashgram: {flashgram_username}\n"
        f"Ваш номер: {flashgram_phone}\n\n"
        f"<tg-emoji emoji-id='5262623036946794266'>⚙️</tg-emoji>Выберите, что вы хотите сделать:</b>",
        parse_mode="HTML",
        reply_markup=settings_menu()
    )
    await callback.answer()

@dp.callback_query(F.data == "change_username")
async def change_username(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "<b><tg-emoji emoji-id='5229176979856572490'>⚙️</tg-emoji>Напишите свой новый юзернейм в Flashgram:</b>",
        parse_mode="HTML"
    )
    await state.set_state(SettingsStates.waiting_new_username)
    await callback.answer()

@dp.callback_query(F.data == "change_phone")
async def change_phone(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "<b><tg-emoji emoji-id='5229176979856572490'>⚙️</tg-emoji>Напишите свой новый номер в Flashgram:</b>",
        parse_mode="HTML"
    )
    await state.set_state(SettingsStates.waiting_new_phone)
    await callback.answer()

@dp.message(SettingsStates.waiting_new_username)
async def save_new_username(message: Message, state: FSMContext):
    new_username = message.text.strip()
    user_id = message.from_user.id
    
    conn = sqlite3.connect("flashgram.db")
    c = conn.cursor()
    c.execute("UPDATE users SET flashgram_username = ? WHERE user_id = ?", (new_username, user_id))
    conn.commit()
    conn.close()
    
    await state.clear()
    await message.answer(
        "<b><tg-emoji emoji-id='5336860842283515961'>⚙️</tg-emoji>Юзернейм успешно изменен!</b>",
        parse_mode="HTML",
        reply_markup=main_menu()
    )

@dp.message(SettingsStates.waiting_new_phone)
async def save_new_phone(message: Message, state: FSMContext):
    new_phone = message.text.strip()
    user_id = message.from_user.id
    
    conn = sqlite3.connect("flashgram.db")
    c = conn.cursor()
    c.execute("UPDATE users SET flashgram_phone = ? WHERE user_id = ?", (new_phone, user_id))
    conn.commit()
    conn.close()
    
    await state.clear()
    await message.answer(
        "<b><tg-emoji emoji-id='5336860842283515961'>⚙️</tg-emoji>Номер успешно изменен!</b>",
        parse_mode="HTML",
        reply_markup=main_menu()
    )

# ============ ПРОМОКОДЫ ==========

@dp.callback_query(F.data == "promocodes")
async def promocodes_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "<b><tg-emoji emoji-id='5341715473882955310'>⚙️</tg-emoji>Введите актуальный промокод:</b>",
        parse_mode="HTML",
        reply_markup=back_to_main()
    )
    await state.set_state(PromocodeStates.waiting_promocode)
    await callback.answer()

@dp.message(StateFilter(PromocodeStates.waiting_promocode), F.text)
async def check_promocode(message: Message, state: FSMContext):
    code = message.text.strip()
    user_id = message.from_user.id
    
    promo = get_promocode(code)
    
    if not promo:
        await message.answer(
            "<b><tg-emoji emoji-id='5334878195185367136'>⚙️</tg-emoji>Нет такого промокода!</b>",
            parse_mode="HTML",
            reply_markup=back_to_main()
        )
        await state.clear()
        return
    
    if promo[4] <= 0:
        await message.answer(
            "<b><tg-emoji emoji-id='5334878195185367136'>⚙️</tg-emoji>У этого промокода закончились активации!</b>",
            parse_mode="HTML",
            reply_markup=back_to_main()
        )
        await state.clear()
        return
    
    reward_type = promo[2]
    reward_value = promo[3]
    
    if reward_type == "stars":
        add_stars(user_id, int(reward_value))
        await message.answer(
            f"<b><tg-emoji emoji-id='5334789577125147626'>⚙️</tg-emoji>Вы активировали промокод и получили {reward_value} звезд!</b>",
            parse_mode="HTML",
            reply_markup=back_to_main()
        )
    elif reward_type == "nft":
        add_to_inventory(user_id, reward_value)
        await message.answer(
            f"<b><tg-emoji emoji-id='5334789577125147626'>⚙️</tg-emoji>Вы активировали промокод и получили NFT «{reward_value}»!</b>",
            parse_mode="HTML",
            reply_markup=back_to_main()
        )
    elif reward_type == "case":
        add_to_inventory(user_id, f"Кейс {reward_value}")
        await message.answer(
            f"<b><tg-emoji emoji-id='5334789577125147626'>⚙️</tg-emoji>Вы активировали промокод и получили кейс «{reward_value}»!\n\n✅ Он появился в вашем инвентаре!</b>",
            parse_mode="HTML",
            reply_markup=back_to_main()
        )
    
    use_promocode(code)
    await state.clear()

# ============ АДМИН КОМАНДА ДЛЯ ПРОМОКОДОВ ==========

@dp.message(Command("promo"))
async def create_promocode(message: Message):
    if message.chat.id != ADMIN_GROUP_ID:
        return
    
    args = message.text.split()
    if len(args) < 4:
        await message.reply("❌ Использование: /promo <код> <тип> <значение> <активации>\n\n"
                           "Типы:\n"
                           "stars - /promo code stars 100 5\n"
                           "nft - /promo code nft 'Plush Pepe' 1\n"
                           "case - /promo code case 'Фелириум' 3")
        return
    
    code = args[1]
    reward_type = args[2]
    reward_value = ' '.join(args[3:-1]) if len(args) > 4 else args[3]
    uses_left = int(args[-1])
    
    if reward_type not in ["stars", "nft", "case"]:
        await message.reply("❌ Неверный тип! Используй: stars, nft, case")
        return
    
    if reward_type == "stars":
        try:
            int(reward_value)
        except:
            await message.reply("❌ Для stars значение должно быть числом!")
            return
    
    try:
        add_promocode(code, reward_type, reward_value, uses_left, message.from_user.id)
        await message.reply(f"✅ Промокод создан!\n"
                           f"Код: {code}\n"
                           f"Тип: {reward_type}\n"
                           f"Награда: {reward_value}\n"
                           f"Активаций: {uses_left}")
    except Exception as e:
        await message.reply(f"❌ Ошибка: такой код уже существует!")

# ============ МАГАЗИН ==========

user_selected_nft = {}

@dp.callback_query(F.data == "shop")
async def shop_handler(callback: CallbackQuery):
    global shop_open
    if not shop_open:
        await callback.message.edit_text(
            "<b>❌ Магазин закрыт на технический перерыв разработчиком.</b>",
            parse_mode="HTML",
            reply_markup=back_to_main()
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        f"<b><tg-emoji emoji-id='5201691993775818138'>🛒</tg-emoji> Магазин NFT подарков!\n\n"
        f"<tg-emoji emoji-id='5224450179368767019'>📋</tg-emoji> Выберите NFT подарок который вы хотите приобрести ниже. Учтите, некоторые NFT сейчас недоступны.</b>",
        parse_mode="HTML",
        reply_markup=get_paginated_shop(0)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("shop_page_"))
async def shop_page(callback: CallbackQuery):
    page = int(callback.data.split("_")[2])
    await callback.message.edit_reply_markup(reply_markup=get_paginated_shop(page))
    await callback.answer()

@dp.callback_query(F.data.startswith("shop_buy_"))
async def shop_buy_nft(callback: CallbackQuery):
    global shop_open
    if not shop_open:
        await callback.answer("❌ Магазин закрыт на технический перерыв!", show_alert=True)
        return
    
    nft_name = callback.data.replace("shop_buy_", "")
    user_id = callback.from_user.id
    
    user_selected_nft[user_id] = nft_name
    
    await callback.message.edit_text(
        f"<b><tg-emoji emoji-id='5445221832074483553'>🎨</tg-emoji> Выберите цвет фона ниже\n\n"
        f"<tg-emoji emoji-id='5444856076954520455'>⚠️</tg-emoji> Учтите, выбранный фон вам могут отказать, если его не будет в наличии. Также, все цвета мы не можем перечислить, выбор проходит между основными цветами ниже.</b>",
        parse_mode="HTML",
        reply_markup=get_paginated_colors(0)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("color_page_"))
async def color_page(callback: CallbackQuery):
    page = int(callback.data.split("_")[2])
    await callback.message.edit_reply_markup(reply_markup=get_paginated_colors(page))
    await callback.answer()

@dp.callback_query(F.data.startswith("shop_color_"))
async def shop_choose_color(callback: CallbackQuery):
    global shop_open
    if not shop_open:
        await callback.answer("❌ Магазин закрыт на технический перерыв!", show_alert=True)
        return
    
    color = callback.data.replace("shop_color_", "")
    user_id = callback.from_user.id
    nft_name = user_selected_nft.get(user_id, "Unknown")
    
    user = get_user(user_id)
    
    try:
        topic = await bot.create_forum_topic(
            chat_id=ADMIN_GROUP_ID,
            name=f"Покупка {nft_name} {color}"
        )
        thread_id = topic.message_thread_id
        
        order_id = add_shop_order(user_id, nft_name, color, thread_id)
        
        await bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            message_thread_id=thread_id,
            text=f"TG юзернейм: @{callback.from_user.username}\n"
                 f"TG ID: {user_id}\n"
                 f"FG юзернейм: {user[2] if user else 'Не указан'}\n"
                 f"FG номер: {user[3] if user else 'Не указан'}\n\n"
                 f"Что покупает: {nft_name}\n"
                 f"Какой фон: {color}",
            reply_markup=admin_shop_buttons(order_id)
        )
        
        await callback.message.edit_text(
            f"<b><tg-emoji emoji-id='5197371802136892976'>✅</tg-emoji> Вы подали заявку на покупку NFT подарка. Ожидайте ответа администрации.\n\n"
            f"<tg-emoji emoji-id='5197371802136892976'>📢</tg-emoji> Администратор даст вам ответ, какова сумма данного NFT, скинет ссылку на него и выставит на продажу ровно за ту цену что он указал. Ожидайте.</b>",
            parse_mode="HTML",
            reply_markup=back_to_main()
        )
        
    except Exception as e:
        print(f"Ошибка создания темы для магазина: {e}")
        await callback.message.edit_text(
            "<b>❌ Ошибка при оформлении заявки. Попробуйте позже.</b>",
            parse_mode="HTML",
            reply_markup=back_to_main()
        )
    
    await callback.answer()

# ============ АДМИН КОМАНДЫ ДЛЯ МАГАЗИНА ==========

temp_order_data = {}

@dp.callback_query(F.data.startswith("admin_price_"))
async def admin_set_price(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.replace("admin_price_", ""))
    temp_order_data['current_order_id'] = order_id
    
    await callback.message.answer(
        "💰 Напишите сумму за которую пользователь купит NFT:"
    )
    await state.set_state("waiting_shop_price")
    await callback.answer()

@dp.message(StateFilter("waiting_shop_price"), F.text)
async def admin_get_price(message: Message, state: FSMContext):
    try:
        price = int(message.text.strip())
        order_id = temp_order_data.get('current_order_id')
        
        update_shop_order_price(order_id, price)
        
        await message.answer(
            f"✅ Цена {price} установлена. Выберите действие:",
            reply_markup=admin_shop_actions(order_id)
        )
        await state.clear()
    except:
        await message.answer("❌ Введите число!")

@dp.callback_query(F.data.startswith("admin_link_"))
async def admin_set_link(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.replace("admin_link_", ""))
    temp_order_data['current_order_id'] = order_id
    
    await callback.message.answer(
        "🔗 Укажите пожалуйста ссылку на NFT:"
    )
    await state.set_state("waiting_shop_link")
    await callback.answer()

@dp.message(StateFilter("waiting_shop_link"), F.text)
async def admin_get_link(message: Message, state: FSMContext):
    link = message.text.strip()
    order_id = temp_order_data.get('current_order_id')
    
    update_shop_order_link(order_id, link)
    
    await message.answer(
        f"Ссылка сохранена!",
        reply_markup=admin_shop_actions(order_id)
    )
    await state.clear()

@dp.callback_query(F.data.startswith("admin_approve_"))
async def admin_approve(callback: CallbackQuery):
    order_id = int(callback.data.replace("admin_approve_", ""))
    order = get_shop_order(order_id)
    
    if order:
        user_id = order[1]
        nft_name = order[2]
        color = order[3]
        price = order[5]
        link = order[6]
        
        update_shop_order_status(order_id, "approved")
        
        await bot.send_message(
            user_id,
            f"<b><tg-emoji emoji-id='5202064723922670546'>✅</tg-emoji> Администратор выставил подарок, который вы желаете купить за {price}\n\n"
            f"В приложении Flashgram перейдите по этой ссылке для покупки NFT и осмотра - {link}</b>",
            parse_mode="HTML",
            reply_markup=user_cancel_button(order_id)
        )
        
        await callback.message.edit_text(
            callback.message.text + "\n\nВыставлено! Пользователь уведомлен.",
            reply_markup=None
        )
    
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject(callback: CallbackQuery):
    order_id = int(callback.data.replace("admin_reject_", ""))
    order = get_shop_order(order_id)
    
    if order:
        user_id = order[1]
        update_shop_order_status(order_id, "rejected")
        
        await bot.send_message(
            user_id,
            "<b>Администратор отказал вам в покупке NFT подарка. Попробуйте другой.</b>",
            parse_mode="HTML",
            reply_markup=back_to_main()
        )
        
        await callback.message.edit_text(
            callback.message.text + "\n\nОтказано! Пользователь уведомлен.",
            reply_markup=None
        )
    
    await callback.answer()

@dp.callback_query(F.data.startswith("user_cancel_"))
async def user_cancel_purchase(callback: CallbackQuery):
    order_id = int(callback.data.replace("user_cancel_", ""))
    order = get_shop_order(order_id)
    
    if order:
        thread_id = order[7]
        update_shop_order_status(order_id, "cancelled")
        
        try:
            await bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                message_thread_id=thread_id,
                text="Пользователь отклонил покупку."
            )
        except:
            pass
        
        await callback.message.edit_text(
            "<b>Вы отклонили покупку. Возвращаем вас в главное меню.</b>",
            parse_mode="HTML",
            reply_markup=main_menu()
        )
    
    await callback.answer()

# ============ АЗАРТ ==========

user_bets = {}
dice_game_active = {}

@dp.callback_query(F.data == "casino")
async def casino_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        f"<b><tg-emoji emoji-id='5278467510604160626'>🎮</tg-emoji> Выберите игру ниже\n\n"
        f"<tg-emoji emoji-id='5382194935057372936'>⚠️</tg-emoji> Учтите, вы тратите звезды в боте, никак не в flashgram.</b>",
        parse_mode="HTML",
        reply_markup=casino_menu()
    )
    await callback.answer()

@dp.callback_query(F.data == "dice_game")
async def dice_game_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    
    dice_game_active[user_id] = False
    
    await callback.message.edit_text(
        f"<b><tg-emoji emoji-id='5452069934089641166'>🎲</tg-emoji> Игра «кубик» представляет себя первой азартной игрой в нашем боте!\n\n"
        f"<tg-emoji emoji-id='5262736024651452318'>📖</tg-emoji> Играется очень просто! Нажмите на кнопочку ниже и вы автоматически отправите кубик вместе с ботом. У кого число будет больше - победил. Если победил бот - вы проиграли всю свою ставку, победили вы - забираете в х1.5. Без ставки вы не сможете запустить игру.</b>",
        parse_mode="HTML",
        reply_markup=dice_game_menu(has_bet=False)
    )
    await callback.answer()

@dp.callback_query(F.data == "dice_bet")
async def dice_bet_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "<b>Напишите свою ставку. Учтите, принимаются только больше 35!</b>",
        parse_mode="HTML"
    )
    await state.set_state(CasinoStates.waiting_bet)
    await callback.answer()

@dp.message(StateFilter(CasinoStates.waiting_bet), F.text)
async def dice_save_bet(message: Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        bet = int(message.text.strip())
        if bet < 35:
            await message.answer("<b>Ставка должна быть больше 35!</b>", parse_mode="HTML")
            return
        
        stars = get_stars(user_id)
        if stars < bet:
            await message.answer(f"<b>Недостаточно звезд! У вас {stars} звезд.</b>", parse_mode="HTML")
            return
        
        user_bets[user_id] = bet
        dice_game_active[user_id] = True
        
        await message.answer(
            f"<b>Ставка {bet} принята! Теперь вы можете запустить игру.</b>",
            parse_mode="HTML",
            reply_markup=dice_game_menu(has_bet=True)
        )
        await state.clear()
    except ValueError:
        await message.answer("<b>Введите число!</b>", parse_mode="HTML")

@dp.callback_query(F.data == "dice_play")
async def dice_play_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if not dice_game_active.get(user_id, False):
        await callback.answer("Не ломайся дурачок, ставку поставь быстро!", show_alert=True)
        return
    
    bet = user_bets.get(user_id, 0)
    if bet == 0:
        await callback.answer("Сначала сделайте ставку!", show_alert=True)
        return
    
    stars = get_stars(user_id)
    if stars < bet:
        await callback.answer(f"Недостаточно звезд! У вас {stars} звезд.", show_alert=True)
        return
    
    # Блокируем повторный клик
    await callback.message.edit_reply_markup(reply_markup=None)
    dice_game_active[user_id] = False
    
    # Кидаем кубики с шансом 20% на победу пользователя
    user_dice = roll_dice()
    
    # Шанс выигрыша пользователя 20%
    if random.randint(1, 100) <= 20:
        # Пользователь выигрывает
        bot_dice = random.randint(1, user_dice - 1) if user_dice > 1 else 1
        win_amount = int(bet * 1.5)
        add_stars(user_id, win_amount - bet)
        
        await callback.message.answer(
            f"<b><tg-emoji emoji-id='5262495450648300372'>🎉</tg-emoji> Поздравляем, вы выиграли!\n\n"
            f"Ваш кубик: {user_dice}\n"
            f"Кубик бота: {bot_dice}\n\n"
            f"Ваша ставка: {bet}\n"
            f"Вы выиграли: {win_amount}</b>",
            parse_mode="HTML",
            reply_markup=back_to_main()
        )
    else:
        # Бот выигрывает
        bot_dice = random.randint(user_dice + 1, 6) if user_dice < 6 else 6
        remove_stars(user_id, bet)
        
        await callback.message.answer(
            f"<b><tg-emoji emoji-id='5264841374670275679'>😢</tg-emoji> Увы, вы проиграли!\n\n"
            f"Ваш кубик: {user_dice}\n"
            f"Кубик бота: {bot_dice}\n\n"
            f"Ваша ставка: {bet}\n"
            f"Вы потеряли: {bet}</b>",
            parse_mode="HTML",
            reply_markup=back_to_main()
        )
    
    # Очищаем данные
    user_bets[user_id] = None
    await callback.answer()

# ============ ЗАПУСК ==========

async def main():
    start_health_server()
    start_server()
    keep_alive()
    init_db()
    print("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
