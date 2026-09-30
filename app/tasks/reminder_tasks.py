import asyncio
from datetime import datetime, timedelta
from celery import shared_task
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.core.celery_app import celery_app
# O'zingizning DB URL va Bot tokeningizni qo'ying
BOT_TOKEN = "SIZNING_BOT_TOKENINGIZ"
DATABASE_URL = "sqlite+aiosqlite:///./med_queue.db"  # yoki postgresql+asyncpg://...

engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def _send_reminders_async():
    from app.db.models import Appointment
    bot = Bot(token=BOT_TOKEN)
    now = datetime.now()

    # 1. 24 soatlik oraliq (ertangi kun shu soatlar)
    target_24h_start = now + timedelta(hours=23, minutes=50)
    target_24h_end = now + timedelta(hours=24, minutes=10)

    # 2. 2 soatlik oraliq
    target_2h_start = now + timedelta(hours=1, minutes=50)
    target_2h_end = now + timedelta(hours=2, minutes=10)

    async with async_session() as session:
        # 24 soat oldingi eslatma
        stmt_24h = select(Appointment).where(
            and_(
                Appointment.status == "confirmed",
                Appointment.appointment_date == target_24h_start.date()
            )
        )
        res_24 = await session.execute(stmt_24h)
        for appt in res_24.scalars().all():
            try:
                await bot.send_message(
                    chat_id=appt.user_id,
                    text=(
                        f"⏰ <b>Eslatma: Ertaga shifokor qabulingiz bor!</b>\n\n"
                        f"🔢 Navbat raqami: #{appt.queue_number}\n"
                        f"🕒 Vaqt: {appt.start_time.strftime('%H:%M')}\n\n"
                        f"Iltimos, o‘z vaqtida kelishingizni so‘raymiz."
                    ),
                    parse_mode="HTML"
                )
            except Exception:
                pass

        # 2 soat oldingi eslatma (Tasdiqlash/Bekor qilish tugmasi bilan)
        stmt_2h = select(Appointment).where(
            and_(
                Appointment.status == "confirmed",
                Appointment.appointment_date == now.date()
            )
        )
        res_2 = await session.execute(stmt_2h)
        for appt in res_2.scalars().all():
            # Agar qabul vaqtiga taxminan 2 soat qolgan bo'lsa
            appt_datetime = datetime.combine(appt.appointment_date, appt.start_time)
            if target_2h_start <= appt_datetime <= target_2h_end:
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✅ Boraman", callback_data=f"confirm_arrival_{appt.id}"),
                        InlineKeyboardButton(text="❌ Kela olmayman", callback_data=f"appt:cancel:{appt.id}")
                    ]
                ])
                try:
                    await bot.send_message(
                        chat_id=appt.user_id,
                        text=(
                            f"🔔 <b>Diqqat: Qabulga 2 soat qoldi!</b>\n\n"
                            f"Shifokoringiz sizni kutmoqda. Qabulga kela olasizmi?"
                        ),
                        reply_markup=kb,
                        parse_mode="HTML"
                    )
                except Exception:
                    pass

    await bot.session.close()

@celery_app.task
def send_appointment_reminders():
    """Celery chaqiradigan sinxron qobiq"""
    asyncio.run(_send_reminders_async())
