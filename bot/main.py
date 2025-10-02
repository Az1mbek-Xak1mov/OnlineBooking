import asyncio
import logging
import os
import sys

import django
from dotenv import load_dotenv

from bot.handlers import register_all_handlers
from bot.loader import bot, dp

load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "root.settings")

django.setup()


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )


async def main():
    setup_logging()
    register_all_handlers(dp)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
