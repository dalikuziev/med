from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker
from app.services.slot_service import SlotEngine

class DependencyMiddleware(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker, slot_engine: SlotEngine):
        self.session_pool = session_pool
        self.slot_engine = slot_engine

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Har bir so'rov (xabar yoki tugma bosilishi) uchun yangi sessiya ochamiz
        async with self.session_pool() as session:
            data['session'] = session              # Handlerdagi `session` argumentiga tushadi
            data['slot_engine'] = self.slot_engine # Handlerdagi `slot_engine` argumentiga tushadi
            return await handler(event, data)
