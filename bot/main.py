import asyncio
import logging
from os import getenv
import sys
from aiogram import Bot
from dotenv import load_dotenv
from bot.handlers.main import online_booking

load_dotenv()

TOKEN = getenv('BOT_TOKEN')


async def main() -> None:
    bot = Bot(token=TOKEN)
    await online_booking.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )
    asyncio.run(main())
