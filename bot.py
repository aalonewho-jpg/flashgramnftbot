import asyncio
import re
import random
import sqlite3
from keep_alive import keep_alive
from health_server import start_health_server
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
    add_shop_order, get_shop_order, update_shop_order_price, update_shop_order_link, update_shop_order_status
)
from states import RegisterStates, SettingsStates, PromocodeStates, ShopStates, CasinoStates
from keyboards import (
    main_menu, subscribe_button, back_to_main, referrals_menu,
    rating_back, get_paginated_inventory, get_paginated_cases, settings_menu,
    admin_withdraw_button, get_paginated_shop, get_paginated_colors,
    admin_shop_buttons, admin_shop_actions, user_cancel_button, casino_menu, dice_game_menu
)
from utils import FREE_CASE_REWARDS, CASES_DATA, get_random_reward, roll_dice

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

REQUIRED_CHANNEL = "@alonewho666"

# ============ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ============

async def is_subscribed(user_id: int) -> bool:
    try:
        # Проверяем первый канал
        member1 = await bot.get_chat_member("@alonewho666", user_id)
        # Проверяем второй канал
        member2 = await bot.get_chat_member("@flashgram_info", user_id)
        
        return member1.status in ["member", "administrator", "creator"] and \
               member2.status in ["member", "administrator", "creator"]
    except:
        return False

async def check_referral_levels(user_id):
    ref_count = get_referral_count(user_id)
    
    level_rewards = {
        1: ["100 Stars"],
        3: ["1000 Stars"],
        5: ["2000 Stars", "Кейс Фелириум"],
        7: ["Кейс Фелириум", "Кейс Запах"],
        10: ["Кейс Запах", "Кейс Богач"],
        13: ["Кейс Богач", "Кейс Свадьба", "Кейс Шахта"],
        17: ["Кейс Свадьба", "Кейс Шахта", "Кейс Все или ничего"],
        23: ["Кейс Шахта", "Кейс Все или ничего", "Кейс Небо"],
        30: ["5000 Stars", "Кейс Небо", "Кейс Сердечный приступ", "Кейс Время", "Кейс Черный"],
        50: ["20000 Stars", "Кейс Сердечный приступ", "Кейс Время", "Кейс Черный", "Кейс PEPE", "Кейс Мифическая слава"]
    }
    
    for level, rewards in level_rewards.items():
        if ref_count >= level:
            for reward in rewards:
                if "Stars" in reward:
                    stars_count = int(re.search(r'\d+', reward).group())
                    add_stars(user_id, stars_count)
                    await bot.send_message(user_id, f"<b>За достижение {level} рефералов вы получили {reward}!</b>", parse_mode="HTML")
                else:
                    add_to_inventory(user_id, reward)
                    await bot.send_message(user_id, f"<b>За достижение {level} рефералов вы получили {reward}!</b>", parse_mode="HTML")

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
        await callback.answer("❌ Вы не подписаны на канал!", show_alert=True)


@dp.message(RegisterStates.waiting_flashgram_username)
async def get_flashgram_username(message: Message, state: FSMContext):
    flashgram_username = message.text.strip()
    await state.update_data(flashgram_username=flashgram_username)
    
    await message.answer(
        "<b><tg-emoji emoji-id='5336860842283515961'>✅</tg-emoji>Напишите свой номер в Flashgram и откройте его в профиле, это нужно для верификации аккаунта и удобного поиска для выдачи NFT.</b>",
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
            await callback.answer(f"⏰ Для следующего открытия подождите {hours_left} часов {minutes_left} минут!", show_alert=True)
            return
    
    all_slots = ["Durov Cap", "100 Stars", "25 Stars", "Pepe", "Snake Box", "Jelly Bunny", "Flying Broom", "Spiced Wine", "Lunar Snake", "Lol Pop", "Pet Snake", "Ice Cream", "Witch Hat"]
    
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


@dp.callback_query(F.data == "referrals")
async def referrals_menu_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    bot_username = (await bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    ref_count = get_referral_count(user_id)
    
    if ref_count >= 50:
        level = 10
    elif ref_count >= 30:
        level = 9
    elif ref_count >= 23:
        level = 8
    elif ref_count >= 17:
        level = 7
    elif ref_count >= 13:
        level = 6
    elif ref_count >= 10:
        level = 5
    elif ref_count >= 7:
        level = 4
    elif ref_count >= 5:
        level = 3
    elif ref_count >= 3:
        level = 2
    elif ref_count >= 1:
        level = 1
    else:
        level = 0
    
    text = f"""<b><tg-emoji emoji-id='5271604874419647061'>👥</tg-emoji> Реферальная программа. С помощью нее вы можете получать кейсы и звезды!

<tg-emoji emoji-id='5262758886762368240'>📊</tg-emoji> Уровни и награды:

<tg-emoji emoji-id='5210863290846053617'>1️⃣</tg-emoji> 1 уровень (1 реферал) - 100 Stars
<tg-emoji emoji-id='5211195669775157055'>2️⃣</tg-emoji> 2 уровень (3 реферала) - 1000 Stars
<tg-emoji emoji-id='5208724955478401912'>3️⃣</tg-emoji> 3 уровень (5 рефералов) - 2000 Stars и Кейс Фелириум
<tg-emoji emoji-id='5208538373509125577'>4️⃣</tg-emoji> 4 уровень (7 рефералов) - Кейс Фелириум и Кейс Запах
<tg-emoji emoji-id='5208966822266706069'>5️⃣</tg-emoji> 5 уровень (10 рефералов) - Кейс Запах и Кейс Богач
<tg-emoji emoji-id='5208487890463530182'>6️⃣</tg-emoji> 6 уровень (13 рефералов) - Кейс Богач, Кейс Свадьба и Кейс Шахта
<tg-emoji emoji-id='5208682766014652414'>7️⃣</tg-emoji> 7 уровень (17 рефералов) - Кейс Свадьба, Кейс Шахта и Кейс Все или ничего
<tg-emoji emoji-id='5208912525290150178'>8️⃣</tg-emoji> 8 уровень (23 реферала) - Кейс Шахта, Кейс Все или ничего и Кейс Небо
<tg-emoji emoji-id='5208919367173048054'>9️⃣</tg-emoji> 9 уровень (30 рефералов) - 5000 Stars, Кейс Небо, Кейс Сердечный приступ, Кейс Время, Кейс Черный
<tg-emoji emoji-id='5211030386548703968'>🔟</tg-emoji> 10 уровень (50 рефералов) - 20000 Stars, Кейс Сердечный приступ, Кейс Время, Кейс Черный, Кейс PEPE, Кейс Мифическая слава

<tg-emoji emoji-id='5339113303522161846'>🏆</tg-emoji> Ваш текущий уровень: {level} (рефералов: {ref_count})

<tg-emoji emoji-id='5339113303522161846'>🔗</tg-emoji> Ваша реферальная ссылка: {ref_link}</b>"""
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=referrals_menu()
    )
    await callback.answer()


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


@dp.callback_query(F.data == "inventory")
async def inventory_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    items = get_inventory(user_id)
    stars = get_stars(user_id)
    
    await callback.message.edit_text(
        f"<b><tg-emoji emoji-id='5165929450369451797'>📦</tg-emoji> Ваш пользовательский инвентарь:\n\n"
        f"<tg-emoji emoji-id='5440539497383087970'>⭐️</tg-emoji> Количество накопленных звезд: {stars}\n\n"
        f"🎁 Предметы:</b>",
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


@dp.callback_query(F.data.startswith("withdraw_"))
async def withdraw_item(callback: CallbackQuery):
    item_name = callback.data.replace("withdraw_", "")
    user_id = callback.from_user.id
    user = get_user(user_id)
    
    # Удаляем из инвентаря
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
        "<b>✅ Вы подали заявку на вывод своего подарка, ожидайте.</b>",
        parse_mode="HTML",
        reply_markup=back_to_main()
    )
    await callback.answer()

@dp.callback_query(F.data == "withdraw_yes")
async def withdraw_confirm(callback: CallbackQuery):
    text = callback.message.text
    item_name = text.split(":")[1].strip().split("?")[0].strip()
    user_id = callback.from_user.id
    user = get_user(user_id)
    
    remove_from_inventory(user_id, item_name)
    
    await callback.message.edit_text(
        "<b>✅ Вы подали заявку на вывод своего подарка, ожидайте.</b>",
        parse_mode="HTML",
        reply_markup=back_to_main()
    )
    await callback.answer()

@dp.callback_query(F.data == "withdraw_no")
async def withdraw_cancel(callback: CallbackQuery):
    await inventory_handler(callback)
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_withdraw_"))
async def admin_withdraw(callback: CallbackQuery):
    await callback.message.edit_text(
        callback.message.text + "\n\n✅ Выведено администратором!",
        reply_markup=None
    )
    await callback.answer("Готово!")


@dp.callback_query(F.data == "cases")
async def cases_handler(callback: CallbackQuery):
    keyboard, _ = get_paginated_cases(0)
    await callback.message.edit_text(
        f"<b><tg-emoji emoji-id='5165663102267557505'>🎲</tg-emoji> Кейсы, место, где вы можете открывать боксы и получать из них NFT подарки и звезды!\n\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «Фелириум» — 100 звезд\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «Запах» — 150 звезд\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «Богач» — 500 звезд\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «Свадьба» — 1300 звезд\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «Шахта» — 3000 звезд\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «Всё или ничего» — 5000 звезд\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «Небо» — 7500 звезд\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «Сердечный приступ» — 10000 звезд\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «Время» — 10500 звезд\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «Чёрный» — 20000 звезд\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «PEPE» — 27000 звезд\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «Мифическая слава» — 30000 звезд\n"
        f"<tg-emoji emoji-id='5323542372036909383'>📦</tg-emoji> Кейс «alone» — 50000 звезд\n\n"
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
    _, prices = get_paginated_cases(0)
    price = prices.get(case_name, 0)
    
    user_id = callback.from_user.id
    stars = get_stars(user_id)
    
    if stars < price:
        await callback.answer(f"❌ Недостаточно звезд! Нужно {price} звезд.", show_alert=True)
        return
    
    remove_stars(user_id, price)
    add_to_inventory(user_id, f"Кейс {case_name}")
    
    await callback.answer(f"✅ Вы купили кейс «{case_name}»! Он появился в инвентаре.", show_alert=True)

@dp.callback_query(F.data.startswith("open_case_"))
async def open_case_from_inventory(callback: CallbackQuery):
    case_full_name = callback.data.replace("open_case_", "")
    user_id = callback.from_user.id
    
    inventory = get_inventory(user_id)
    if case_full_name not in inventory:
        await callback.answer("❌ Этого кейса нет в инвентаре!", show_alert=True)
        return
    
    case_name = case_full_name.replace("Кейс ", "")
    
    if case_name not in CASES_DATA:
        await callback.answer(f"❌ Кейс «{case_name}» не найден!", show_alert=True)
        return
    
    remove_from_inventory(user_id, case_full_name)
    
    items = get_inventory(user_id)
    stars = get_stars(user_id)
    
    await callback.message.edit_text(
        f"<b><tg-emoji emoji-id='5165929450369451797'>📦</tg-emoji> Ваш пользовательский инвентарь:\n\n"
        f"<tg-emoji emoji-id='5440539497383087970'>⭐️</tg-emoji> Количество накопленных звезд: {stars}\n\n"
        f"🎁 Предметы:</b>",
        parse_mode="HTML",
        reply_markup=get_paginated_inventory(items, 0)
    )
    
    all_slots = ["100 Stars", "250 Stars", "500 Stars", "Sharp Tongue", "Snoop Dogg", "Candy Cane", "Lol Pop", "Moon Pendant"]
    
    msg = await callback.message.answer(f"<b><tg-emoji emoji-id='5429106865671793190'>🎲</tg-emoji> Открываем кейс {case_name}...</b>", parse_mode="HTML")
    
    for _ in range(8):
        random_slots = [random.choice(all_slots) for _ in range(3)]
        text = f"{random_slots[0]} | {random_slots[1]} | {random_slots[2]}"
        await msg.edit_text(text)
        await asyncio.sleep(0.3)
    
    reward = get_random_reward(CASES_DATA[case_name])
    
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
        f"выберите, что вы хотите сделать:</b>",
        parse_mode="HTML",
        reply_markup=settings_menu()
    )
    await callback.answer()

@dp.callback_query(F.data == "change_username")
async def change_username(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "<b>Напишите свой новый юзернейм в Flashgram:</b>",
        parse_mode="HTML"
    )
    await state.set_state(SettingsStates.waiting_new_username)
    await callback.answer()

@dp.callback_query(F.data == "change_phone")
async def change_phone(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "<b>Напишите свой новый номер в Flashgram:</b>",
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
        "<b>✅ Юзернейм успешно изменен!</b>",
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
        "<b>✅ Номер успешно изменен!</b>",
        parse_mode="HTML",
        reply_markup=main_menu()
    )


@dp.callback_query(F.data == "promocodes")
async def promocodes_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "<b><tg-emoji emoji-id='5278467510604160626'>😢</tg-emoji>Введите актуальный промокод:</b>",
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
            "<b><tg-emoji emoji-id='5334878195185367136'>😢</tg-emoji>Нет такого промокода!</b>",
            parse_mode="HTML",
            reply_markup=back_to_main()
        )
        await state.clear()
        return
    
    if promo[4] <= 0:
        await message.answer(
            "<b><tg-emoji emoji-id='5334878195185367136'>😢</tg-emoji>У этого промокода закончились активации!</b>",
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
            f"<b><tg-emoji emoji-id='5334789577125147626'>😢</tg-emoji>Вы активировали промокод и получили {reward_value} звезд!</b>",
            parse_mode="HTML",
            reply_markup=back_to_main()
        )
    elif reward_type == "nft":
        add_to_inventory(user_id, reward_value)
        await message.answer(
            f"<b><tg-emoji emoji-id='5334789577125147626'>😢</tg-emoji>Вы активировали промокод и получили NFT «{reward_value}»!</b>",
            parse_mode="HTML",
            reply_markup=back_to_main()
        )
    elif reward_type == "case":
        add_to_inventory(user_id, f"Кейс {reward_value}")
        await message.answer(
            f"<b><tg-emoji emoji-id='5334789577125147626'>😢</tg-emoji>Вы активировали промокод и получили кейс «{reward_value}»!\n\n✅ Он появился в вашем инвентаре!</b>",
            parse_mode="HTML",
            reply_markup=back_to_main()
        )
    
    use_promocode(code)
    await state.clear()


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

user_selected_nft = {}

@dp.callback_query(F.data == "shop")
async def shop_handler(callback: CallbackQuery):
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
async def shop_buy_nft(callback: CallbackQuery, state: FSMContext):
    nft_name = callback.data.replace("shop_buy_", "")
    user_id = callback.from_user.id
    
    # Сохраняем выбранный NFT
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
    color = callback.data.replace("shop_color_", "")
    user_id = callback.from_user.id
    nft_name = user_selected_nft.get(user_id, "Unknown")
    
    user = get_user(user_id)
    
    # Создаем тему в админ группе
    try:
        topic = await bot.create_forum_topic(
            chat_id=ADMIN_GROUP_ID,
            name=f"Покупка {nft_name} {color}"
        )
        thread_id = topic.message_thread_id
        
        # Сохраняем заказ в БД
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
        f"✅ Ссылка сохранена!",
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
                text="❌ Пользователь отклонил покупку."
            )
        except:
            pass
        
        await callback.message.edit_text(
            "<b>✅ Вы отклонили покупку. Возвращаем вас в главное меню.</b>",
            parse_mode="HTML",
            reply_markup=main_menu()
        )
    
    await callback.answer()

user_bets = {}

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
    
    # Очищаем предыдущую ставку
    user_bets[user_id] = None
    
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
        "<b>Напишите свою ставку. Учтите, принимаются только больше 200!</b>",
        parse_mode="HTML"
    )
    await state.set_state(CasinoStates.waiting_bet)
    await callback.answer()

@dp.message(StateFilter(CasinoStates.waiting_bet), F.text)
async def dice_save_bet(message: Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        bet = int(message.text.strip())
        if bet < 200:
            await message.answer("<b>Ставка должна быть больше 200!</b>", parse_mode="HTML")
            return
        
        stars = get_stars(user_id)
        if stars < bet:
            await message.answer(f"<b>Недостаточно звезд! У вас {stars} звезд.</b>", parse_mode="HTML")
            return
        
        # Сохраняем ставку
        user_bets[user_id] = bet
        
        await message.answer(
            f"<b>Ставка {bet} принята! Теперь вы можете запустить игру.</b>",
            parse_mode="HTML",
            reply_markup=dice_game_menu(has_bet=True)
        )
        await state.clear()
    except:
        await message.answer("<b>Введите число!</b>", parse_mode="HTML")

@dp.callback_query(F.data == "dice_play")
async def dice_play_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    bet = user_bets.get(user_id)
    
    if not bet:
        await callback.answer("Не ломайся дурачок, ставку поставь быстро!", show_alert=True)
        return
    
    stars = get_stars(user_id)
    if stars < bet:
        await callback.answer(f"Недостаточно звезд! У вас {stars} звезд.", show_alert=True)
        return
    
    # Кидаем кубики
    user_dice = roll_dice()
    bot_dice = roll_dice()
    
    # Отправляем сообщение с кубиками
    dice_msg = await callback.message.answer(
        f"Ваш кубик: {user_dice}\n"
        f"Кубик бота: {bot_dice}\n\n"
        f"{'⚡ Сравниваем...' if user_dice == bot_dice else '⏳ Определяем победителя...'}"
    )
    
    await asyncio.sleep(1.5)
    
    if user_dice > bot_dice:
        # Победа пользователя
        win_amount = int(bet * 1.5)
        add_stars(user_id, win_amount)
        user_bets[user_id] = None
        
        await dice_msg.edit_text(
            f"<b><tg-emoji emoji-id='5262495450648300372'>🎉</tg-emoji> Поздравляем, вы выиграли!\n\n"
            f"Ваша ставка: {bet}\n"
            f"Вы выиграли: {win_amount}\n"
            f"Ваш кубик: {user_dice} | Кубик бота: {bot_dice}</b>",
            parse_mode="HTML",
            reply_markup=back_to_main()
        )
    elif user_dice < bot_dice:
        # Проигрыш
        remove_stars(user_id, bet)
        user_bets[user_id] = None
        
        await dice_msg.edit_text(
            f"<b><tg-emoji emoji-id='5264841374670275679'>😢</tg-emoji> Увы, вы проиграли!\n\n"
            f"Ваша ставка: {bet}\n"
            f"Вы потеряли: {bet}\n"
            f"Ваш кубик: {user_dice} | Кубик бота: {bot_dice}</b>",
            parse_mode="HTML",
            reply_markup=back_to_main()
        )
    else:
        # Ничья
        await dice_msg.edit_text(
            f"<b><tg-emoji emoji-id='5264841374670275679'>😢</tg-emoji> Ничья!\n\n"
            f"Ваша ставка возвращена.\n"
            f"Ваш кубик: {user_dice} | Кубик бота: {bot_dice}</b>",
            parse_mode="HTML",
            reply_markup=back_to_main()
        )
    
    await callback.answer()

# ============ ЗАПУСК ============

async def main():
    start_health_server()
    keep_alive()
    init_db()
    print("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
