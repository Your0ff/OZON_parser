import logging
import sys
import threading
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio

from config_data.config import Config, load_config
from database.database import console_input_loop
from handlers import user_handlers, other_handlers


async def main():
    config: Config = load_config()
    storage = MemoryStorage()

    bot = Bot(token=config.tg_bot.token)
    dp = Dispatcher(storage=storage)

    dp.include_router(user_handlers.router)
    dp.include_router(other_handlers.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    print("Бот запущен")
    threading.Thread(target=console_input_loop, daemon=True).start()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())