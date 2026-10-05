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
from app.db.models import Clinic
from app.db.models import Doctor
from app.bot.keyboards.doctor_keyboards import get_doctors_keyboard

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


# Klinika ma'lumotlari oynasidan "Klinikalarga qaytish" yoki Paginatsiya (sahifalash) uchun handler
@clinic_router.callback_query(ClinicSelectCallback.filter(F.action == "page"))
async def back_from_clinic_card(callback: CallbackQuery, callback_data: ClinicSelectCallback, state: FSMContext,
                                session):
    # State'ni yana klinika tanlash bosqichiga qaytaramiz
    await state.set_state(BookingFlow.choosing_clinic)

    # Klinikalarni bazadan tortib olamiz
    stmt = select(Clinic).order_by(Clinic.id)
    result = await session.execute(stmt)
    clinics = result.scalars().all()

    # Tugma orqali yuborilgan sahifa raqamini olamiz (sizning kodingizda bu page=1)
    page_number = callback_data.page if callback_data.page else 1

    await callback.message.edit_text(
        "Quyidagi klinikalardan birini tanlang:",
        reply_markup=get_clinics_paginated_keyboard(clinics, page=page_number)
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


@clinic_router.callback_query(F.data == "continue_to_docs")
async def show_doctors_for_clinic(callback: CallbackQuery, state: FSMContext, session):
    user_data = await state.get_data()
    clinic_id = user_data.get("selected_clinic_id")

    if not clinic_id:
        await callback.answer("Klinika topilmadi, iltimos boshidan boshlang.", show_alert=True)
        return

    stmt = select(Doctor).where(Doctor.clinic_id == clinic_id)
    result = await session.execute(stmt)
    doctors = result.scalars().all()

    if not doctors:
        await callback.message.edit_text(
            "Hozircha bu klinikada shifokorlar ro'yxati yo'q.\nIltimos, boshqa klinika tanlang."
        )
        await callback.answer()
        return

    await state.set_state(BookingFlow.choosing_doctor)
    await callback.message.edit_text(
        "O'zingizga kerakli shifokorni tanlang:",
        reply_markup=get_doctors_keyboard(doctors)
    )
    await callback.answer()


@clinic_router.callback_query(F.data.startswith("select_doc_"))
async def process_doctor_selection(callback: CallbackQuery, state: FSMContext):
    doctor_id = int(callback.data.split("_")[-1])

    await state.update_data(selected_doctor_id=doctor_id)

    # Hozircha shu holatda turadi, keyingi qadamda kalendarga ulaymiz
    # await state.set_state(BookingFlow.choosing_date)

    await callback.message.edit_text(
        f"✅ Shifokor tanlandi!\n\nTez orada sana va bo'sh vaqtlar jadvali ulanadi.",
        reply_markup=None
    )
    await callback.answer()


@clinic_router.callback_query(F.data == "back_to_clinics")
async def go_back_to_clinics(callback: CallbackQuery, state: FSMContext, session):
    await state.set_state(BookingFlow.choosing_clinic)

    stmt = select(Clinic).order_by(Clinic.id)
    result = await session.execute(stmt)
    clinics = result.scalars().all()

    await callback.message.edit_text(
        "Quyidagi klinikalardan birini tanlang:",
        reply_markup=get_clinics_paginated_keyboard(clinics, page=1)
    )
    await callback.answer()
