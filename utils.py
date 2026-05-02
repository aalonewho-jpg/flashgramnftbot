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
    "Valentine Box": 15, "Cupid Charm": 15, "Love Potion": 20, "Love Candle": 15, "Cookie Heart": 15,
    "Trapped Heart": 30, "Snoop Dogg": 20, "Ice Cream": 15, "Happy Brownie": 20, "Lol Pop": 15,
    "Desk Calendar": 15, "Candy Cane": 15, "Xmas Stocking": 20, "Fresh Socks": 20, "Clover Pin": 25,
    "Swag Bag": 20, "Snake Box": 15, "Lunar Snake": 15, "B-Day Candle": 20, "Pet Snake": 15,
    "Pretty Posy": 15, "Snoop Cigar": 35, "Jester Hat": 20, "Stellar Rocket": 25, "Input Key": 25,
    "Ginger Cookie": 25, "Jolly Chimp": 30, "Jelly Bunny": 20, "Spiced Wine": 35, "Evil Eye": 35,
    "Spy Agaric": 35, "Winter Wreath": 30, "Star Notepad": 25, "Witch Hat": 25, "Hypno Lollipop": 20,
    "Santa Hat": 20, "Sakura Flower": 25, "Hanging Star": 20, "Eternal Candle": 20, "Top Hat": 25,
    "Crystal Ball": 20, "Record Player": 25 "Toy Bear": 15, "Swiss Watch": 40, "Vintage Cigar": 35,
    "Rare Bird": 30, "Flying Broom": 25, "Low Rider": 40, "Voodoo Doll": 20, "Mad Pumpkin": 35,
    "Skull Flower": 45, "Astral Shard": 50, "Signet Ring": 50, "Sharp Tongue": 45, "Bonded Ring": 45,
    "Gem Signet": 50, "Scared Cat": 40, "Electric Skull": 45, "Kissed Frog": 40, "Nail Bracelet": 40,
    "Loot Bag": 50, "Artisan Brick": 70, "Perfume Bottle": 55, "Durov's Cap": 60, "Ion Gem": 50,
    "Magic Potion": 55, "Mini Oscar": 60, "Mighty Arm": 65, "Heroic Halmet": 60, "Heart Locket": 70, "Plush Pepe": 100
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
