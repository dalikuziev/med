from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

# Asosiy menyu tugmalari
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🩺 Navbat olish")],
            [KeyboardButton(text="📅 Mening navbatlarim")]
        ],
        resize_keyboard=True
    )

# Navbatlarni boshqarish uchun CallbackData
class MyAppointmentCallback(CallbackData, prefix="my_app", sep="-"):
    app_id: int
    action: str  # "view" (ko'rish) yoki "cancel" (bekor qilish)

# Faol navbatlar ro'yxati (Inline klaviatura)
def get_my_appointments_keyboard(appointments):
    keyboard = []
    for app in appointments:
        # Tugma matni: "07.10.2026 16:00"
        btn_text = f"📅 {app.appointment_date.strftime('%d.%m.%Y')} ⏰ {app.start_time.strftime('%H:%M')}"
        keyboard.append([
            InlineKeyboardButton(
                text=btn_text,
                callback_data=MyAppointmentCallback(app_id=app.id, action="view").pack()
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Navbatni bekor qilish tugmasi
def get_cancel_appointment_keyboard(app_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="❌ Navbatni bekor qilish",
                callback_data=MyAppointmentCallback(app_id=app_id, action="cancel").pack()
            )],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_list")]
        ]
    )
