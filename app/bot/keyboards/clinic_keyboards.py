from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.bot.keyboards.callbacks import ClinicSelectCallback

def get_clinic_search_keyboard() -> ReplyKeyboardMarkup:
    """Geolokatsiya orqali qidirish uchun reply menyu"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Eng yaqin klinikani topish", request_location=True)],
            [KeyboardButton(text="🏢 Hududlar bo‘yicha tanlash")],
            [KeyboardButton(text="◀️ Asosiy menyu")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_clinics_paginated_keyboard(clinics: list, page: int = 1, per_page: int = 5) -> InlineKeyboardMarkup:
    """Klinikalar ro'yxati va sahifalash tugmalari"""
    builder = InlineKeyboardBuilder()

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    current_page_clinics = clinics[start_idx:end_idx]

    for clinic in current_page_clinics:
        # Masalan: "🏥 Shifo Med (Chilonzor)"
        builder.button(
            text=f"🏥 {clinic.name}",
            callback_data=ClinicSelectCallback(action="view", clinic_id=clinic.id)
        )

    builder.adjust(1)  # Har bir qatorda bittadan klinika

    # Sahifalash navigatsiyasi (Oldingi / Keyingi)
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Oldingi",
                callback_data=ClinicSelectCallback(action="page", page=page - 1).pack()
            )
        )
    if end_idx < len(clinics):
        nav_buttons.append(
            InlineKeyboardButton(
                text="Keyingi ➡️",
                callback_data=ClinicSelectCallback(action="page", page=page + 1).pack()
            )
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    return builder.as_markup()


def get_clinic_card_keyboard(clinic_id: int) -> InlineKeyboardMarkup:
    """Klinika ma'lumotlari chiqqanda tanlash yoki ortga qaytish tugmalari"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Ushbu klinikani tanlash",
        callback_data=ClinicSelectCallback(action="select", clinic_id=clinic_id)
    )
    builder.button(
        text="⬅️ Klinikalarga qaytish",
        callback_data=ClinicSelectCallback(action="page", page=1)
    )
    builder.adjust(1)
    return builder.as_markup()
