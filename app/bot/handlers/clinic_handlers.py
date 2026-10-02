from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from app.bot.states.booking_states import BookingFlow
from app.bot.keyboards.callbacks import ClinicSelectCallback
from app.bot.keyboards.clinic_keyboards import (
    get_clinic_search_keyboard,
    get_clinics_paginated_keyboard,
    get_clinic_card_keyboard
)
from app.db.models import Clinic # Bazadagi modelni import qildik

clinic_router = Router()

@clinic_router.message(F.text == "🩺 Navbat olish")
async def start_booking_flow(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(BookingFlow.choosing_clinic)
    await message.answer(
        "Klinikani qanday tanlashni xohlaysiz?\n\n"
        "📍 Joylashuvingizga ko‘ra eng yaqinini topishingiz yoki to‘liq ro‘yxatdan ko‘rishingiz mumkin.",
        reply_markup=get_clinic_search_keyboard()
    )

@clinic_router.message(BookingFlow.choosing_clinic, F.text == "🏢 Hududlar bo‘yicha tanlash")
async def show_all_clinics(message: Message, session):
    # 1. Haqiqiy bazadan barcha klinikalarni tortib olamiz
    stmt = select(Clinic).order_by(Clinic.id)
    result = await session.execute(stmt)
    clinics = result.scalars().all()

    if not clinics:
        await message.answer("Hozircha tizimda klinikalar mavjud emas. Iltimos, keyinroq urinib ko'ring.")
        return

    # Sizning get_clinics_paginated_keyboard funksiyangiz obyektning .id va .name xususiyatlarini
    # o'qiydi, shuning uchun SQLAlchemy modeli ham unga muammosiz tushadi.
    await message.answer(
        "Quyidagi klinikalardan birini tanlang:",
        reply_markup=get_clinics_paginated_keyboard(clinics, page=1)
    )

@clinic_router.callback_query(ClinicSelectCallback.filter(F.action == "view"))
async def view_clinic_details(callback: CallbackQuery, callback_data: ClinicSelectCallback, session):
    clinic_id = callback_data.clinic_id

    # 2. Tanlangan klinika ma'lumotlarini bazadan olamiz
    stmt = select(Clinic).where(Clinic.id == clinic_id)
    result = await session.execute(stmt)
    clinic = result.scalar_one_or_none()

    if not clinic:
        await callback.answer("Klinika topilmadi!", show_alert=True)
        return

    # Bazadan kelgan real ma'lumotlarni matnga joylaymiz
    text = (
        f"🏥 <b>{clinic.name}</b>\n\n"
        f"📍 Manzil: {clinic.address or 'Kiritilmagan'}\n"
        f"📞 Telefon: {clinic.phone or 'Kiritilmagan'}\n\n"
        "Qabulga yozilish uchun tasdiqlang:"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=get_clinic_card_keyboard(clinic.id),
        parse_mode="HTML"
    )
    await callback.answer()

@clinic_router.callback_query(ClinicSelectCallback.filter(F.action == "select"))
async def select_clinic_proceed(callback: CallbackQuery, callback_data: ClinicSelectCallback, state: FSMContext):
    clinic_id = callback_data.clinic_id

    await state.update_data(selected_clinic_id=clinic_id)
    await state.set_state(BookingFlow.choosing_department)

    markup = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="➡️ Shifokor tanlash", callback_data="continue_to_docs")
    ]])

    await callback.message.edit_text(
        "✅ Klinika muvaffaqiyatli tanlandi! Davom etish uchun bosing:",
        reply_markup=markup,
        parse_mode="HTML"
    )
    await callback.answer("Klinika biriktirildi")
