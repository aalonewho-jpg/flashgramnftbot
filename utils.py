import random
import re
import asyncio
from aiogram import Bot
from database import add_stars, add_to_inventory

# ========== НОВЫЕ ДАННЫЕ ДЛЯ БЕСПЛАТНОГО КЕЙСА ==========
FREE_CASE_REWARDS = {
    "25 Stars": 55,
    "30 Stars": 25,
    "50 Stars": 10,
    "Lol Pop": 5,
    "Candy Cane": 5
}

# ========== НОВЫЕ ДАННЫЕ ДЛЯ КЕЙСОВ (ЦЕНЫ И ШАНСЫ) ==========
CASES_DATA = {
    "Фелириум": {
        "price": 30,
        "rewards": {
            "75 Stars": 10, "50 Stars": 20, "25 Stars": 60,
            "Lol Pop": 5, "Candy Cane": 5
        }
    },
    "Запах": {
        "price": 40,
        "rewards": {
            "75 Stars": 10, "50 Stars": 20, "25 Stars": 60,
            "Jelly Bunny": 5, "Perfume Bottle": 5
        }
    },
    "Богач": {
        "price": 50,
        "rewards": {
            "90 Stars": 10, "60 Stars": 20, "40 Stars": 60,
            "Evil Eye": 5, "Candy Cane": 5
        }
    },
    "Свадьба": {
        "price": 60,
        "rewards": {
            "100 Stars": 10, "80 Stars": 20, "55 Stars": 60,
            "Spiced Wine": 5, "Xmas Stocking": 5
        }
    },
    "Шахта": {
        "price": 80,
        "rewards": {
            "110 Stars": 10, "95 Stars": 20, "60 Stars": 60,
            "Happy Brownie": 5, "Jester Hat": 5
        }
    },
    "Все или ничего": {
        "price": 80,
        "rewards": {
            "150 Stars": 10, "80 Stars": 20, "40 Stars": 50,
            "Perfume Bottle": 10, "Lol Pop": 5, "Trapped Heart": 5
        }
    },
    "Небо": {
        "price": 100,
        "rewards": {
            "145 Stars": 10, "120 Stars": 20, "80 Stars": 60,
            "Astral Shard": 5, "Input Key": 5
        }
    },
    "Сердечный приступ": {
        "price": 130,
        "rewards": {
            "170 Stars": 10, "150 Stars": 20, "100 Stars": 50,
            "Jolly Chimp": 5, "Snoop Cigar": 5, "Trapped Heart": 10
        }
    },
    "Время": {
        "price": 140,
        "rewards": {
            "175 Stars": 10, "145 Stars": 20, "120 Stars": 60,
            "Durov's Cap": 5, "Vintage Cigar": 5
        }
    },
    "Черный": {
        "price": 150,
        "rewards": {
            "200 Stars": 10, "150 Stars": 20, "130 Stars": 50,
            "Gem Signet": 10, "Perfume Bottle": 5, "Snoop Cigar": 5
        }
    },
    "PEPE": {
        "price": 200,
        "rewards": {
            "230 Stars": 10, "170 Stars": 20, "140 Stars": 40,
            "Plush Pepe": 1, "Skull Flower": 5, "Perfume Bottle": 19, "Vintage Cigar": 5
        }
    },
    "Мифическая слава": {
        "price": 210,
        "rewards": {
            "250 Stars": 5, "200 Stars": 10, "180 Stars": 50,
            "Loot Bag": 15, "Astral Shard": 10, "Durov's Cap": 5, "Magic Potion": 5
        }
    },
    "alone": {
        "price": 380,
        "rewards": {
            "400 Stars": 10, "340 Stars": 20, "300 Stars": 40,
            "Plush Pepe": 1, "Durov's Cap": 5, "Perfume Bottle": 19, "Heroic Halmet": 5
        }
    }
}

# ========== ЦЕНЫ НА ПРОДАЖУ NFT (ВСЕ ЧТО ЕСТЬ В МАГАЗИНЕ) ==========
NFT_SELL_PRICES = {
    "Valentine Box": 30, "Cupid Charm": 30, "Love Potion": 30, "Love Candle": 30, "Cookie Heart": 30,
    "Trapped Heart": 40, "Snoop Dogg": 50, "Ice Cream": 25, "Happy Brownie": 35, "Lol Pop": 30,
    "Desk Calendar": 20, "Candy Cane": 25, "Xmas Stocking": 30, "Fresh Socks": 20, "Clover Pin": 25,
    "Swag Bag": 40, "Snake Box": 45, "Lunar Snake": 50, "B-Day Candle": 20, "Pet Snake": 40,
    "Pretty Posy": 35, "Snoop Cigar": 55, "Jester Hat": 30, "Stellar Rocket": 50, "Input Key": 45,
    "Ginger Cookie": 25, "Jolly Chimp": 60, "Jelly Bunny": 40, "Spiced Wine": 35, "Evil Eye": 45,
    "Spy Agaric": 30, "Winter Wreath": 30, "Star Notepad": 25, "Witch Hat": 35, "Hypno Lollipop": 40,
    "Santa Hat": 30, "Sakura Flower": 35, "Hanging Star": 30, "Eternal Candle": 40, "Top Hat": 45,
    "Crystal Ball": 50, "Record Player": 40, "Toy Bear": 35, "Swiss Watch": 60, "Vintage Cigar": 65,
    "Rare Bird": 70, "Flying Broom": 55, "Low Rider": 60, "Voodoo Doll": 50, "Mad Pumpkin": 45,
    "Skull Flower": 55, "Astral Shard": 80, "Signet Ring": 50, "Sharp Tongue": 45, "Bonded Ring": 55,
    "Gem Signet": 70, "Scared Cat": 60, "Electric Skull": 75, "Kissed Frog": 50, "Nail Bracelet": 40,
    "Loot Bag": 90, "Artisan Brick": 70, "Perfume Bottle": 65, "Durov's Cap": 100, "Ion Gem": 80,
    "Magic Potion": 85, "Mini Oscar": 90, "Mighty Arm": 95, "Heroic Halmet": 120, "Heart Locket": 80, "Plush Pepe": 150
}

def get_random_reward(rewards_dict):
    """Универсальная функция получения случайной награды по шансам"""
    total = sum(rewards_dict.values())
    rand = random.randint(1, total)
    cumulative = 0
    for reward, chance in rewards_dict.items():
        cumulative += chance
        if rand <= cumulative:
            return reward
    return list(rewards_dict.keys())[0]

def roll_dice():
    return random.randint(1, 6)
