from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select, update
from app.db.models import Appointment
from app.bot.keyboards.appointment_keyboards import (
    MyAppointmentCallback,
    get_my_appointments_keyboard,
    get_cancel_appointment_keyboard
)

my_app_router = Router()


# 1. Asosiy menyudan "Mening navbatlarim" tugmasi bosilganda
@my_app_router.message(F.text == "📅 Mening navbatlarim")
async def show_my_appointments(message: Message, session):
    user_id = message.from_user.id

    # Bazadan faqat shu foydalanuvchining faol (confirmed) navbatlarini qidiramiz
    stmt = select(Appointment).where(
        Appointment.user_id == user_id,
        Appointment.status == "confirmed"
    ).order_by(Appointment.appointment_date, Appointment.start_time)

    result = await session.execute(stmt)
    appointments = result.scalars().all()

    if not appointments:
        await message.answer("Sizda hozircha faol navbatlar yo'q.")
        return

    await message.answer(
        "Sizning faol navbatlaringiz. Boshqarish uchun keraklisini tanlang:",
        reply_markup=get_my_appointments_keyboard(appointments)
    )


# 2. Ro'yxatdan bitta navbat tanlanganda (Tafsilotlarini ko'rish)
@my_app_router.callback_query(MyAppointmentCallback.filter(F.action == "view"))
async def view_appointment_details(callback: CallbackQuery, callback_data: MyAppointmentCallback, session):
    stmt = select(Appointment).where(Appointment.id == callback_data.app_id)
    result = await session.execute(stmt)
    app = result.scalar_one_or_none()

    if not app:
        await callback.answer("Bu navbat topilmadi.", show_alert=True)
        return

    text = (
        f"📋 <b>Navbat tafsilotlari:</b>\n\n"
        f"📅 Sana: <b>{app.appointment_date.strftime('%d.%m.%Y')}</b>\n"
        f"⏰ Vaqt: <b>{app.start_time.strftime('%H:%M')}</b>\n"
        f"🔢 Talon raqami: <b>{app.queue_number}</b>\n\n"
        f"<i>Agar qabulga kela olmasangiz, iltimos, navbatni bekor qiling.</i>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_cancel_appointment_keyboard(app.id),
        parse_mode="HTML"
    )


# 3. Navbatni bekor qilish tugmasi bosilganda
@my_app_router.callback_query(MyAppointmentCallback.filter(F.action == "cancel"))
async def cancel_appointment(callback: CallbackQuery, callback_data: MyAppointmentCallback, session):
    # Bazadagi statusni "cancelled" ga o'zgartiramiz
    stmt = update(Appointment).where(
        Appointment.id == callback_data.app_id
    ).values(status="cancelled")

    await session.execute(stmt)
    await session.commit()

    await callback.message.edit_text(
        "✅ Navbatingiz muvaffaqiyatli bekor qilindi. O'rningiz boshqalar uchun bo'shatildi.")
    await callback.answer()


# 4. "Orqaga" tugmasi bosilganda
@my_app_router.callback_query(F.data == "back_to_list")
async def back_to_appointments_list(callback: CallbackQuery, session):
    await callback.message.delete()
    # Kodni takrorlamaslik uchun to'g'ridan-to'g'ri message orqali funksiyani chaqiramiz
    await show_my_appointments(callback.message, session)
