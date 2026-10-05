from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_doctors_keyboard(doctors) -> InlineKeyboardMarkup:
    """Bazadan kelgan shifokorlar ro'yxatidan inline tugmalar yasash"""
    builder = InlineKeyboardBuilder()

    for doc in doctors:
        # Har bir shifokor uchun tugma (callback_data formatini o'zingizning logikangizga moslashingiz mumkin)
        builder.button(
            text=f"👨‍⚕️ {doc.full_name} ({doc.specialty})",
            callback_data=f"select_doc_{doc.id}"
        )

    builder.adjust(1)  # Tugmalarni ustma-ust (1 tadan) joylashtirish
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_clinics"))

    return builder.as_markup()
