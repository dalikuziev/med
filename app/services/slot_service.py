from datetime import datetime, date, time, timedelta
from typing import List, Dict
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

class SlotEngine:
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client

    @staticmethod
    def generate_raw_slots(
            start_time: time,
            end_time: time,
            duration_minutes: int,
            break_start: time = None,
            break_end: time = None
    ) -> List[time]:
        """Ish soatlaridan tushlik vaqtini ayirib, xom slotlar hosil qilish"""
        slots = []
        dummy_date = date.today()
        current_dt = datetime.combine(dummy_date, start_time)
        end_dt = datetime.combine(dummy_date, end_time)

        break_start_dt = datetime.combine(dummy_date, break_start) if break_start else None
        break_end_dt = datetime.combine(dummy_date, break_end) if break_end else None

        while current_dt + timedelta(minutes=duration_minutes) <= end_dt:
            slot_start = current_dt.time()
            slot_end_dt = current_dt + timedelta(minutes=duration_minutes)

            # Tushlik vaqtiga to'g'ri kelib qolmasligini tekshirish
            in_break = False
            if break_start_dt and break_end_dt:
                if not (slot_end_dt <= break_start_dt or current_dt >= break_end_dt):
                    in_break = True

            if not in_break:
                slots.append(slot_start)

            current_dt += timedelta(minutes=duration_minutes)

        return slots

    async def get_available_slots(
            self,
            doctor_id: int,
            target_date: date,
            raw_slots: List[time],
            booked_times: List[time]
    ) -> List[Dict]:
        """Band qilingan va Redis'da ushlab turilgan slotlarni ajratib ko'rsatish"""
        now = datetime.now()
        available_slots = []

        for slot in raw_slots:
            slot_str = slot.strftime("%H:%M")

            # 1. Agar bugungi kun bo'lsa va soat o'tib ketgan bo'lsa, chiqarmaymiz
            if target_date == date.today() and slot < now.time():
                continue

            # 2. Bazada oldindan band qilinganmi?
            if slot in booked_times:
                continue

            # 3. Redis'da boshqa bemor tanlab turibdimi (2 daqiqalik lock)?
            redis_lock_key = f"lock:slot:{doctor_id}:{target_date.isoformat()}:{slot_str}"
            is_locked = await self.redis.exists(redis_lock_key)

            if not is_locked:
                available_slots.append({
                    "time": slot_str,
                    "is_free": True
                })

        return available_slots

    async def lock_slot_temporarily(
            self,
            doctor_id: int,
            target_date: date,
            slot_time: str,
            user_id: int,
            ttl_seconds: int = 120
    ) -> bool:
        """Bemor vaqtni tanlaganda 2 daqiqaga boshqalarga yopib qo'yish"""
        redis_lock_key = f"lock:slot:{doctor_id}:{target_date.isoformat()}:{slot_time}"
        # SET NX EX - faqat kalit mavjud bo'lmasa yozadi (atomar operatsiya)
        success = await self.redis.set(redis_lock_key, str(user_id), ex=ttl_seconds, nx=True)
        return bool(success)

    async def release_slot_lock(self, doctor_id: int, target_date: date, slot_time: str):
        """Bemor ortga qaytsa yoki bekor qilsa qulfni yechish"""
        redis_lock_key = f"lock:slot:{doctor_id}:{target_date.isoformat()}:{slot_time}"
        await self.redis.delete(redis_lock_key)
