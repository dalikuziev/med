from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from app.bot.states.booking_states import BookingFlow
from app.bot.keyboards.callbacks import ClinicSelectCallback
from app.bot.keyboards.clinic_keyboards import (
    get_clinic_search_keyboard,
    get_clinics_paginated_keyboard,
    get_clinic_card_keyboard
)

clinic_router = Router()


@clinic_router.message(F.text == "🩺 Navbat olish")
async def start_booking_flow(message: Message, state: FSMContext):
    """Navbat olish oqimini boshlash"""
    await state.set_state(BookingFlow.choosing_clinic)
    await message.answer(
        "Klinikani qanday tanlashni xohlaysiz?\n\n"
        "📍 Joylashuvingizga ko‘ra eng yaqinini topishingiz yoki to‘liq ro‘yxatdan ko‘rishingiz mumkin.",
        reply_markup=get_clinic_search_keyboard()
    )


@clinic_router.message(BookingFlow.choosing_clinic, F.text == "🏢 Hududlar bo‘yicha tanlash")
async def show_all_clinics(message: Message, session):  # session — DB dependency
    """Barcha faol klinikalarni sahifalab ko'rsatish"""
    # Pseudo-kod: bazadan faol klinikalarni olish
    # clinics = await get_all_active_clinics(session)

    clinics = [
        {"id": 1, "name": "Shifo Med (Chilonzor)"},
        {"id": 2, "name": "Akfa Medline (Olmazor)"},
        {"id": 3, "name": "M-Clinic (Yunusobod)"},
    ]  # Test uchun

    await message.answer(
        "Quyidagi klinikalardan birini tanlang:",
        reply_markup=get_clinics_paginated_keyboard(clinics, page=1)
    )


@clinic_router.callback_query(ClinicSelectCallback.filter(F.action == "view"))
async def view_clinic_details(callback: CallbackQuery, callback_data: ClinicSelectCallback):
    """Klinika ustiga bosilganda uning qisqacha kartasini chiqarish"""
    clinic_id = callback_data.clinic_id

    # DB dan klinika ma'lumotlarini olish
    text = (
        "🏥 <b>Shifo Med Klinikasi</b>\n\n"
        "📍 Manzil: Toshkent sh., Chilonzor tumani, 9-mavze\n"
        "📞 Telefon: +998 71 200 00 00\n"
        "⏰ Ish vaqti: 08:00 - 20:00 (Dam olish kunisiz)\n\n"
        "Qabulga yozilish uchun tasdiqlang:"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=get_clinic_card_keyboard(clinic_id),
        parse_mode="HTML"
    )
    await callback.answer()


@clinic_router.callback_query(ClinicSelectCallback.filter(F.action == "select"))
async def select_clinic_proceed(callback: CallbackQuery, callback_data: ClinicSelectCallback, state: FSMContext):
    """Klinika tanlandi, FSM xotirasiga yozib, keyingi bosqichga o'tkazish"""
    clinic_id = callback_data.clinic_id

    # Tanlangan klinikani state'ga saqlaymiz
    await state.update_data(selected_clinic_id=clinic_id)
    await state.set_state(BookingFlow.choosing_department)

    await callback.message.edit_text(
        "Klinika tanlandi! Endi kerakli <b>bo‘lim yoki mutaxassislikni</b> tanlang:",
        # reply_markup=get_departments_keyboard(clinic_id),
        parse_mode="HTML"
    )
    await callback.answer("Klinika biriktirildi")
