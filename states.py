from aiogram.fsm.state import State, StatesGroup

class RegisterStates(StatesGroup):
    waiting_flashgram_username = State()
    waiting_flashgram_phone = State()

class SettingsStates(StatesGroup):
    waiting_new_username = State()
    waiting_new_phone = State()

class PromocodeStates(StatesGroup):
    waiting_promocode = State()

class ShopStates(StatesGroup):
    waiting_nft = State()
    waiting_color = State()

class CasinoStates(StatesGroup):
    waiting_bet = State()