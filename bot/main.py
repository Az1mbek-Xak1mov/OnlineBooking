import asyncio
import logging
import os
import sys

from aiogram.utils.i18n import FSMI18nMiddleware, I18n
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "root.settings")
import django

django.setup()

from bot.handlers import register_all_handlers
from bot.loader import bot, dp


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

async def main():
    # i18n = I18n(path='locales', default_locale='uz', domain='messages')
    # dp.update.middleware.register(FSMI18nMiddleware(i18n))
    setup_logging()
    register_all_handlers(dp)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
