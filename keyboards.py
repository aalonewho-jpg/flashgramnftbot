from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Бесплатный NFT", callback_data="free_case"),
            InlineKeyboardButton(text="Рефералы", callback_data="referrals")
        ],
        [
            InlineKeyboardButton(text="Инвентарь", callback_data="inventory"),
            InlineKeyboardButton(text="Кейсы", callback_data="cases")
        ],
        [
            InlineKeyboardButton(text="Промокоды", callback_data="promocodes"),
            InlineKeyboardButton(text="Магазин", callback_data="shop"),
            InlineKeyboardButton(text="Азарт", callback_data="casino")
        ],
        [
            InlineKeyboardButton(text="Настройки", callback_data="settings")
        ]
    ])

def subscribe_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ПОДПИСАТЬСЯ", url="https://t.me/alonewho666")],
        [InlineKeyboardButton(text="Я подписался", callback_data="check_subscribe")]
    ])

def back_to_main():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="На главную", callback_data="main_menu")]
    ])

def referrals_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Рейтинг", callback_data="rating")],
        [InlineKeyboardButton(text="На главную", callback_data="main_menu")]
    ])

def rating_back():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="referrals")]
    ])

def get_paginated_inventory(items, page, items_per_page=6):
    total_pages = (len(items) + items_per_page - 1) // items_per_page if items else 1
    start = page * items_per_page
    end = start + items_per_page
    page_items = items[start:end] if items else []
    
    keyboard = []
    for item in page_items:
        if "Кейс" in item:
            keyboard.append([InlineKeyboardButton(text=f"📦 {item}", callback_data=f"open_case_{item}")])
        else:
            keyboard.append([InlineKeyboardButton(text=f"🎁 {item}", callback_data=f"withdraw_{item}")])
    
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="◀", callback_data=f"inv_page_{page-1}"))
    nav_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="none"))
    if page + 1 < total_pages:
        nav_row.append(InlineKeyboardButton(text="▶", callback_data=f"inv_page_{page+1}"))
    if nav_row:
        keyboard.append(nav_row)
    keyboard.append([InlineKeyboardButton(text="На главную", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def confirm_withdraw():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ДА", callback_data="withdraw_yes")],
        [InlineKeyboardButton(text="НЕТ", callback_data="withdraw_no")]
    ])

def get_paginated_cases(page, cases_per_page=4):
    all_cases = [
        "Фелириум", "Запах", "Богач", "Свадьба", "Шахта", 
        "Все или ничего", "Небо", "Сердечный приступ", "Время", 
        "Черный", "PEPE", "Мифическая слава", "alone"
    ]
    
    prices = {
        "Фелириум": 100, "Запах": 150, "Богач": 500, "Свадьба": 1300,
        "Шахта": 3000, "Все или ничего": 5000, "Небо": 7500,
        "Сердечный приступ": 10000, "Время": 10500, "Черный": 20000,
        "PEPE": 27000, "Мифическая слава": 30000, "alone": 50000
    }
    
    total_pages = (len(all_cases) + cases_per_page - 1) // cases_per_page
    start = page * cases_per_page
    end = start + cases_per_page
    page_cases = all_cases[start:end]
    
    keyboard = []
    for case in page_cases:
        keyboard.append([InlineKeyboardButton(text=f"{case} - {prices[case]} звезд", callback_data=f"buy_{case}")])
    
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="◀", callback_data=f"cases_page_{page-1}"))
    nav_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="none"))
    if page + 1 < total_pages:
        nav_row.append(InlineKeyboardButton(text="▶", callback_data=f"cases_page_{page+1}"))
    if nav_row:
        keyboard.append(nav_row)
    keyboard.append([InlineKeyboardButton(text="На главную", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard), prices

def settings_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Изменить юзернейм", callback_data="change_username")],
        [InlineKeyboardButton(text="Изменить номер", callback_data="change_phone")],
        [InlineKeyboardButton(text="На главную", callback_data="main_menu")]
    ])

def admin_withdraw_button(withdrawal_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Выведено", callback_data=f"admin_withdraw_{withdrawal_id}")]
    ])

# Магазин - список NFT
def get_paginated_shop(page, items_per_page=20):
    all_nft = [
        "Valentine Box", "Cupid Charm", "Love Potion", "Love Candle", "Cookie Heart",
        "Trapped Heart", "Snoop Dogg", "Ice Cream", "Happy Brownie", "Lol Pop",
        "Desk Calendar", "Candy Cane", "Xmas Stocking", "Fresh Socks", "Clover Pin",
        "Swag Bag", "Snake Box", "Lunar Snake", "B-Day Candle", "Pet Snake",
        "Pretty Posy", "Snoop Cigar", "Jester Hat", "Stellar Rocket", "Input Key",
        "Ginger Cookie", "Jolly Chimp", "Jelly Bunny", "Spiced Wine", "Evil Eye",
        "Spy Agaric", "Winter Wreath", "Star Notepad", "Witch Hat", "Hypno Lollipop",
        "Santa Hat", "Sakura Flower", "Hanging Star", "Eternal Candle", "Top Hat",
        "Crystal Ball", "Record Player", "Toy Bear", "Swiss Watch", "Vintage Cigar",
        "Rare Bird", "Flying Broom", "Low Rider", "Voodoo Doll", "Mad Pumpkin",
        "Skull Flower", "Astral Shard", "Signet Ring", "Sharp Tongue", "Bonded Ring",
        "Gem Signet", "Scared Cat", "Electric Skull", "Kissed Frog", "Nail Bracelet",
        "Loot Bag", "Artisan Brick", "Perfume Bottle", "Durov's Cap", "Ion Gem",
        "Magic Potion", "Mini Oscar", "Mighty Arm", "Heroic Halmet", "Heart Locket", "Plush Pepe"
    ]
    
    total_pages = (len(all_nft) + items_per_page - 1) // items_per_page
    start = page * items_per_page
    end = start + items_per_page
    page_nft = all_nft[start:end]
    
    keyboard = []
    row = []
    for nft in page_nft:
        row.append(InlineKeyboardButton(text=nft, callback_data=f"shop_buy_{nft}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="◀", callback_data=f"shop_page_{page-1}"))
    nav_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="none"))
    if page + 1 < total_pages:
        nav_row.append(InlineKeyboardButton(text="▶", callback_data=f"shop_page_{page+1}"))
    if nav_row:
        keyboard.append(nav_row)
    keyboard.append([InlineKeyboardButton(text="На главную", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Магазин - выбор цвета
def get_paginated_colors(page, items_per_page=4):
    colors = ["Black", "Onyx Black", "Grey", "White", "Green", "Red", "Gold", "Blue", "Pink", "Silver", "Orange"]
    
    total_pages = (len(colors) + items_per_page - 1) // items_per_page
    start = page * items_per_page
    end = start + items_per_page
    page_colors = colors[start:end]
    
    keyboard = []
    for color in page_colors:
        keyboard.append([InlineKeyboardButton(text=color, callback_data=f"shop_color_{color}")])
    
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="◀", callback_data=f"color_page_{page-1}"))
    nav_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="none"))
    if page + 1 < total_pages:
        nav_row.append(InlineKeyboardButton(text="▶", callback_data=f"color_page_{page+1}"))
    if nav_row:
        keyboard.append(nav_row)
    keyboard.append([InlineKeyboardButton(text="На главную", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Админские кнопки для магазина
def admin_shop_buttons(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Выбрать цену", callback_data=f"admin_price_{order_id}"),
            InlineKeyboardButton(text="Отказать", callback_data=f"admin_reject_{order_id}")
        ]
    ])

def admin_shop_actions(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Указать ссылку", callback_data=f"admin_link_{order_id}"),
            InlineKeyboardButton(text="Выставлен", callback_data=f"admin_approve_{order_id}"),
            InlineKeyboardButton(text="Отказать", callback_data=f"admin_reject_{order_id}")
        ]
    ])

# Кнопка Отказаться для пользователя
def user_cancel_button(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отказаться", callback_data=f"user_cancel_{order_id}")]
    ])

# Азарт - главное меню
def casino_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Кубик", callback_data="dice_game")],
        [InlineKeyboardButton(text="Скоро...", callback_data="none")],
        [InlineKeyboardButton(text="На главную", callback_data="main_menu")]
    ])

def dice_game_menu(has_bet=False):
    if has_bet:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Запустить", callback_data="dice_play")],
            [InlineKeyboardButton(text="На главную", callback_data="main_menu")]
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Сделать ставку", callback_data="dice_bet")],
            [InlineKeyboardButton(text="На главную", callback_data="main_menu")]
        ])