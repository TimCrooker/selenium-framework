import os
import importlib
import sys

bot_name = os.getenv('BOT_NAME')

if not bot_name:
    print("Error: BOT_NAME environment variable not set.")
    sys.exit(1)

try:
    # Dynamically import the bot module
    bot_module = importlib.import_module(f"bots.{bot_name.lower()}_bot")
    bot_class = getattr(bot_module, bot_name)
    bot = bot_class()
    bot.run()
except Exception as e:
    print(f"Error running bot {bot_name}: {e}")
    sys.exit(1)
