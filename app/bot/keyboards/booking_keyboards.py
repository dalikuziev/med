from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

class AppointmentActionCallback(CallbackData, prefix="appt"):
    action: str  # 'cancel', 'location'
    appointment_id: int

def get_contact_keyboard() -> ReplyKeyboardMarkup:
    """Telefon raqamni yuborish uchun reply tugma"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamimni yuborish", request_contact=True)],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_ticket_keyboard(appointment_id: int) -> InlineKeyboardMarkup:
    """Elektron talon ostidagi boshqaruv tugmalari"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="❌ Navbatni bekor qilish",
        callback_data=AppointmentActionCallback(action="cancel", appointment_id=appointment_id)
    )
    builder.button(
        text="📍 Manzilni xaritada ko‘rish",
        callback_data=AppointmentActionCallback(action="location", appointment_id=appointment_id)
    )
    builder.adjust(1)
    return builder.as_markup()
