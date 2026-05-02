import random
import re
import asyncio
from aiogram import Bot
from database import add_stars, add_to_inventory

FREE_CASE_REWARDS = {
    "1000 Stars": 10,
    "500 Stars": 20,
    "100 Stars": 50,
    "Jelly Bunny": 5,
    "Flying Broom": 4,
    "Spiced Wine": 3,
    "Lunar Snake": 3,
    "Lol Pop": 1,
    "Pet Snake": 1,
    "Snake Box": 1,
    "Ice Cream": 1,
    "Witch Hat": 1
}

CASES_DATA = {
    "Фелириум": {
        "500 Stars": 10, "250 Stars": 15, "100 Stars": 55,
        "Sharp Tongue": 1, "Snoop Dogg": 9, "Candy Cane": 3,
        "Lol Pop": 5, "Moon Pendant": 2
    },
    "Запах": {
        "800 Stars": 10, "500 Stars": 25, "250 Stars": 45,
        "Jelly Bunny": 5, "Mad Pumpkin": 5, "Clover Pin": 5,
        "Record Player": 4, "Perfume Bottle": 1
    },
    "Богач": {
        "1000 stars": 15, "800 stars": 20, "500 stars": 40,
        "Hanging Star": 5, "Low Rider": 5, "Gem Signet": 1,
        "Evil Eye": 9, "Voodoo Doll": 5
    },
    "Свадьба": {
        "2000Stars": 15, "1500 Stars": 50, "Flying Broom": 10,
        "Spiced Wine": 5, "Jelly Bunny": 10, "Party Sparkler": 5,
        "Xmas Stocking": 4, "Trapped Heart": 1
    },
    "Шахта": {
        "3000 stars": 15, "2000 stars": 25, "1000 stars": 50,
        "Happy Brownie": 1, "Jester Hat": 2, "Jingle Bells": 1,
        "Stellar Rocket": 2, "Party Sparkler": 4
    },
    "Все или ничего": {
        "8000 stars": 10, "6000 stars": 10, "3500 stars": 40,
        "Perfume Bottle": 1, "Lunaer Snake": 4, "Snake Box": 5,
        "Lol Pop": 3, "Whip Cupcake": 9, "Trapped Heart": 1,
        "Spy Agaric": 7, "Ice Cream": 10
    },
    "Небо": {
        "20000 stars": 10, "15000 stars": 15, "10000 stars": 50,
        "Electric Skull": 7, "Snoop Dogg": 9, "Astral Shard": 1,
        "Magic Potion": 3, "Input Key": 5
    },
    "Сердечный приступ": {
        "40000 stars": 20, "25000 stars": 40, "Jolly Chimp": 3,
        "Ice cream": 10, "Snoop Cigar": 5, "Swag Bag": 5,
        "Winter Wreath": 5, "Clover Pin": 12
    },
    "Время": {
        "50000 stars": 15, "25000 stars": 45, "Kissed Frog": 10,
        "Snoop Cigar": 5, "Ion Gem": 5, "Astral Shard": 9,
        "Durov's Cap": 3, "Vintage Cigar": 7, "Swiss Watch": 1
    },
    "Черный": {
        "60000 Stars": 20, "30000 Stars": 40, "Perfume Bottle": 10,
        "Diamond Ring": 5, "Gem signet": 5, "Top Hat": 10,
        "Toy Bear": 5, "Rare Bird": 5
    },
    "PEPE": {
        "50000 Stars": 70, "Map Pumpkin": 20, "Skull Flower": 5,
        "Sharp Tongue": 4, "Plush Pepe": 1
    },
    "Мифическая слава": {
        "70000 Stars": 70, "Loot Bag": 10, "Artisan Brick": 9,
        "Astral Shard": 5, "Durov's Cap": 1, "Magic Potion": 5
    },
    "alone": {
        "100000 Stars": 60, "Plush Pepe": 1, "Durov's Cap": 10,
        "Mighty Arm": 5, "Heroic Halmet": 5, "Perfume Bottle": 19
    }
}

def get_random_reward(rewards_dict):
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