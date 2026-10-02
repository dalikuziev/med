from sqlalchemy import select
from app.db.models import Appointment
from datetime import datetime, time
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.states.booking_states import BookingFlow
from app.bot.keyboards.time_keyboards import (
    get_next_days_keyboard,
    get_slots_keyboard,
    DateSelectCallback,
    SlotSelectCallback
)
from app.bot.keyboards.booking_keyboards import get_contact_keyboard
from app.services.slot_service import SlotEngine

slot_router = Router()


# 1. Klinika tanlangach, vaqtinchalik Shifokorlar ro'yxatini chiqarish
# (Aslida buni clinic_handlers ichidagi oxirgi qadam o'rniga chaqiramiz, test uchun shu yerda ushlab turamiz)
@slot_router.callback_query(BookingFlow.choosing_department)
async def show_dummy_doctors(callback: CallbackQuery, state: FSMContext):
    # Bu shunchaki test tugma. Real loyihada bazadan shifokorlar olinadi
    builder = InlineKeyboardBuilder()
    builder.button(text="👨‍⚕️ Dr. Alisher Vohidov (Kardiolog)", callback_data="doc_1")
    builder.button(text="👩‍⚕️ Dr. Malika Karimova (Stomatolog)", callback_data="doc_2")
    builder.adjust(1)

    await callback.message.edit_text(
        "Kerakli shifokorni tanlang:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(BookingFlow.choosing_doctor)


# 2. Shifokor tanlangach, Sanalarni chiqarish
@slot_router.callback_query(BookingFlow.choosing_doctor, F.data.startswith("doc_"))
async def choose_date(callback: CallbackQuery, state: FSMContext):
    doctor_id = int(callback.data.split("_")[1])
    await state.update_data(selected_doctor_id=doctor_id)

    await callback.message.edit_text(
        "📅 Qabul uchun qulay sanani tanlang:",
        reply_markup=get_next_days_keyboard(days_count=7)
    )
    await state.set_state(BookingFlow.choosing_date)


# 3. Sana tanlangach, bo'sh vaqtlarni (slotlarni) hisoblab chiqarish
@slot_router.callback_query(BookingFlow.choosing_date, DateSelectCallback.filter())
async def show_available_slots(
        callback: CallbackQuery,
        callback_data: DateSelectCallback,
        state: FSMContext,
        slot_engine: SlotEngine
):
    target_date = datetime.fromisoformat(callback_data.date_str).date()
    await state.update_data(selected_date=callback_data.date_str)
    user_data = await state.get_data()
    doctor_id = user_data["selected_doctor_id"]

    # Test uchun: Shifokor 09:00 dan 17:00 gacha 20 daqiqadan qabul qiladi deylik
    raw_slots = slot_engine.generate_raw_slots(
        start_time=time(9, 0),
        end_time=time(17, 0),
        duration_minutes=20,
        break_start=time(13, 0),
        break_end=time(14, 0)
    )

    # Bazadan va Redisdan tekshirib, faqat bo'shlarini olamiz (Hozircha bazamiz bo'sh)
    available_slots = await slot_engine.get_available_slots(
        doctor_id=doctor_id,
        target_date=target_date,
        raw_slots=raw_slots,
        booked_times=[]  # Real loyihada DB dan o'qiladi
    )

    if not available_slots:
        await callback.answer("Tanlangan sanada bo'sh vaqtlar qolmagan!", show_alert=True)
        return

    await callback.message.edit_text(
        f"Tanlangan sana: <b>{target_date.strftime('%d.%m.%Y')}</b>\n\nBo'sh vaqtlardan birini tanlang:",
        reply_markup=get_slots_keyboard(available_slots),
        parse_mode="HTML"
    )
    await state.set_state(BookingFlow.choosing_time)


# 4. Vaqt tanlangach, tasdiqlash uchun telefon raqam so'rash
@slot_router.callback_query(BookingFlow.choosing_time, SlotSelectCallback.filter())
async def confirm_slot(
        callback: CallbackQuery,
        callback_data: SlotSelectCallback,
        state: FSMContext,
        slot_engine: SlotEngine
):
    user_data = await state.get_data()
    doctor_id = user_data["selected_doctor_id"]
    target_date = datetime.fromisoformat(user_data["selected_date"]).date()
    chosen_time = callback_data.time_str

    # Redis orqali vaqtni 2 daqiqaga qulflaymiz (Race condition himoyasi)
    is_locked = await slot_engine.lock_slot_temporarily(
        doctor_id=doctor_id, target_date=target_date, slot_time=chosen_time, user_id=callback.from_user.id
    )

    if not is_locked:
        await callback.answer("⚠️ Uzr, bu vaqtni hozirgina boshqa bemor band qildi!", show_alert=True)
        return

    await state.update_data(selected_time=chosen_time)
    await state.set_state(BookingFlow.confirming)

    # Inline xabarni o'chirib, pastdagi klaviaturani chiqaramiz
    await callback.message.delete()
    await callback.message.answer(
        f"✅ Siz <b>{target_date.strftime('%d.%m.%Y')}</b> kuni soat <b>{chosen_time}</b> ni tanladingiz.\n\n"
        "Qabulni yakunlash uchun pastdagi tugma orqali telefon raqamingizni yuboring:",
        reply_markup=get_contact_keyboard(),
        parse_mode="HTML"
    )

# 3. Sana tanlangach, bo'sh vaqtlarni (slotlarni) hisoblab chiqarish
@slot_router.callback_query(BookingFlow.choosing_date, DateSelectCallback.filter())
async def show_available_slots(
    callback: CallbackQuery,
    callback_data: DateSelectCallback,
    state: FSMContext,
    slot_engine: SlotEngine,
    session  # Middleware'dan kelayotgan baza sessiyasi
):
    target_date = datetime.fromisoformat(callback_data.date_str).date()
    await state.update_data(selected_date=callback_data.date_str)
    user_data = await state.get_data()
    doctor_id = user_data["selected_doctor_id"]

    # Test uchun: Shifokor 09:00 dan 17:00 gacha 20 daqiqadan qabul qiladi
    raw_slots = slot_engine.generate_raw_slots(
        start_time=time(9, 0),
        end_time=time(17, 0),
        duration_minutes=20,
        break_start=time(13, 0),
        break_end=time(14, 0)
    )

    # 1. BAZADAN SHU KUNGI BAND QILINGAN VAQTLARNI QIDIRAMIZ
    stmt = select(Appointment.start_time).where(
        Appointment.doctor_id == doctor_id,
        Appointment.appointment_date == target_date,
        Appointment.status == "confirmed"
    )
    result = await session.execute(stmt)
    booked_times_db = result.scalars().all()  # Masalan: [16:00, 10:20] ni topadi

    # 2. Baza ma'lumotini generatorga beramiz (u bandlarini o'chirib tashlaydi)
    available_slots = await slot_engine.get_available_slots(
        doctor_id=doctor_id,
        target_date=target_date,
        raw_slots=raw_slots,
        booked_times=booked_times_db  # Baza natijasini berdik
    )

    if not available_slots:
        await callback.answer("Tanlangan sanada bo'sh vaqtlar qolmagan!", show_alert=True)
        return

    await callback.message.edit_text(
        f"Tanlangan sana: <b>{target_date.strftime('%d.%m.%Y')}</b>\n\nBo'sh vaqtlardan birini tanlang:",
        reply_markup=get_slots_keyboard(available_slots),
        parse_mode="HTML"
    )
    await state.set_state(BookingFlow.choosing_time)
