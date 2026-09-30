from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.states.booking_states import BookingFlow
from app.bot.keyboards.booking_keyboards import get_contact_keyboard, get_ticket_keyboard, AppointmentActionCallback
from app.services.booking_service import BookingService
from app.services.slot_service import SlotEngine

booking_router = Router()

@booking_router.message(BookingFlow.confirming, F.contact)
async def process_patient_contact(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    slot_engine: SlotEngine
):
    """Bemor telefon raqamini yuborganda qabulni bazaga yozish"""
    contact = message.contact
    user_data = await state.get_data()

    clinic_id = user_data["selected_clinic_id"]
    doctor_id = user_data["selected_doctor_id"]
    target_date = datetime.fromisoformat(user_data["selected_date"]).date()
    target_time_str = user_data["selected_time"]
    target_time = datetime.strptime(target_time_str, "%H:%M").time()

    # Bazaga yozish
    appointment = await BookingService.create_appointment(
        session=session,
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        user_id=message.from_user.id,
        patient_name=f"{contact.first_name} {contact.last_name or ''}".strip(),
        patient_phone=contact.phone_number,
        appt_date=target_date,
        appt_time=target_time
    )

    # Redis'dagi vaqtinchalik qulfni olib tashlaymiz (chunki endi bazada rasman band bo'ldi)
    await slot_engine.release_slot_lock(doctor_id, target_date, target_time_str)

    # FSM ni tozalaymiz
    await state.clear()

    # Chiroyli Elektron Talon
    ticket_text = (
        "🎫 <b>ELEKTRON TALON (QABUL TASDIQLANDI)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔢 <b>Navbat raqamingiz:</b> #{appointment.queue_number}\n"
        f"🏥 <b>Klinika:</b> Shifo Med Markazi\n"
        f"👨‍⚕️ <b>Shifokor:</b> Dr. Alisher Vohidov (Kardiolog)\n"
        f"🚪 <b>Xona:</b> 204-xona\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 <b>Sana:</b> {target_date.strftime('%d.%m.%Y')}\n"
        f"⏰ <b>Qabul vaqti:</b> {target_time_str}\n"
        f"👤 <b>Bemor:</b> {appointment.patient_name}\n"
        f"📱 <b>Telefon:</b> {appointment.patient_phone}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>⚠️ Iltimos, belgilangan vaqtdan 10 daqiqa oldin yetib keling. "
        "Kela olmasangiz, pastdagi tugma orqali bekor qiling.</i>"
    )

    await message.answer("✅ Siz muvaffaqiyatli navbatga yozildingiz!", reply_markup=ReplyKeyboardRemove())
    await message.answer(
        ticket_text,
        reply_markup=get_ticket_keyboard(appointment.id),
        parse_mode="HTML"
    )

@booking_router.callback_query(AppointmentActionCallback.filter(F.action == "cancel"))
async def cancel_appointment_handler(
    callback: CallbackQuery,
    callback_data: AppointmentActionCallback,
    session: AsyncSession
):
    appointment_id = callback_data.appointment_id
    success = await BookingService.cancel_appointment(
        session=session,
        appointment_id=appointment_id,
        user_id=callback.from_user.id
    )

    if success:
        await callback.message.edit_text(
            "❌ <b>Qabulingiz bekor qilindi.</b>\n\n"
            "Ushbu vaqt boshqa bemorlar uchun ochildi. Yangi navbat olish uchun /start bosing.",
            parse_mode="HTML"
        )
        await callback.answer("Navbat bekor qilindi")
    else:
        await callback.answer("Bu qabulni bekor qilib bo‘lmadi yoki u allaqachon bekor qilingan.", show_alert=True)
