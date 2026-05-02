import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID"))
REQUIRED_CHANNEL = "@alonewho666"
REQUIRED_CHANNEL_2 = "@flashgram_info"
