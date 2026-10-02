import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import redis.asyncio as aioredis
# Biz yozgan barcha modullar
from app.db.models import Base
from app.bot.handlers.start_handlers import start_router
from app.bot.handlers.clinic_handlers import clinic_router
from app.bot.handlers.slot_handlers import slot_router
from app.bot.handlers.booking_handlers import booking_router
from app.bot.handlers.my_appointments_handlers import my_app_router
from app.middlewares.db_middleware import DependencyMiddleware
from app.services.slot_service import SlotEngine

# Konfiguratsiyalar (Kelajakda bularni .env faylga olib o'tamiz)
BOT_TOKEN = "8863118900:AAHLLjvzsgAGeTdxaiybyvP4PAcgSnnXwQs"
# Testni tezroq bajarish uchun hozircha SQLite ishlatamiz, keyin PostgreSQL ga o'zgartirish oson:
DATABASE_URL = "sqlite+aiosqlite:///./med_queue.db"
REDIS_URL = "redis://localhost:6379/0"


async def main():
    logging.basicConfig(level=logging.INFO)

    # 1. Baza va Redis ulanishini tayyorlash
    engine = create_async_engine(DATABASE_URL, echo=False)
    session_pool = async_sessionmaker(engine, expire_on_commit=False)
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

    # Jadvallarni avtomatik yaratish (Migratsiya qilinguncha shundan foydalanamiz)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. Servislarni initsializatsiya qilish
    slot_engine = SlotEngine(redis_client)

    # 3. Bot va Dispatcher yaratish
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # 4. Middleware orqali DB va Redisni ulash
    dp.update.middleware(DependencyMiddleware(session_pool, slot_engine))

    # 5. Barcha yozilgan routerlarni ro'yxatdan o'tkazish
    dp.include_router(start_router)
    dp.include_router(clinic_router)
    dp.include_router(slot_router)
    dp.include_router(booking_router)
    dp.include_router(my_app_router)

    # Botni ishga tushirish
    print("🤖 Tibbiyot navbat tizimi boti ishga tushdi!")
    try:
        await dp.start_polling(bot)
    finally:
        await engine.dispose()
        await redis_client.aclose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi.")
